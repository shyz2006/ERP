import re
from datetime import timedelta
from decimal import Decimal, ROUND_CEILING

from django.db import transaction

from .models import (
    BalanceFormula,
    BomStructure,
    Inventory,
    Material,
    MpsRecord,
    MrpResult,
)


class _Node:
    """BOM 展开后的一个物料需求节点（一次出现）。

    日期与库存无关，建树时即可确定；需求数量依赖父节点净需求与共享库存，
    在处理（process）时才计算。
    """

    __slots__ = (
        "material",
        "edge",
        "parent",
        "mps",
        "order_index",
        "level",
        "seq",
        "completion_date",
        "release_date",
        "net",
        "processed",
    )

    def __init__(self, material, edge, parent, mps, order_index, level, seq,
                 completion_date, release_date):
        self.material = material
        self.edge = edge
        self.parent = parent
        self.mps = mps
        self.order_index = order_index
        self.level = level
        self.seq = seq
        self.completion_date = completion_date
        self.release_date = release_date
        self.net = None
        self.processed = False


def _build_tree(mps, order_index, edges_by_parent, counter):
    """以 MPS 记录为根，深度优先展开 BOM，返回该树的所有节点。"""
    product = mps.product
    root = _Node(
        material=product,
        edge=None,
        parent=None,
        mps=mps,
        order_index=order_index,
        level=0,
        seq=next(counter),
        completion_date=mps.completion_date,
        release_date=mps.completion_date - timedelta(days=product.operation_lead_time),
    )
    nodes = [root]
    stack = [root]
    while stack:
        node = stack.pop()
        for edge in reversed(edges_by_parent.get(node.material.code, [])):
            child = edge.child
            completion = node.release_date
            release = completion - timedelta(
                days=child.operation_lead_time
                + edge.preparation_lead_time
                + edge.supplier_lead_time
            )
            child_node = _Node(
                material=child,
                edge=edge,
                parent=node,
                mps=mps,
                order_index=order_index,
                level=node.level + 1,
                seq=next(counter),
                completion_date=completion,
                release_date=release,
            )
            nodes.append(child_node)
            stack.append(child_node)
    return nodes


def _process(node, stock):
    """计算节点净需求、扣减共享库存并写入结果行。"""
    if node.parent is None:
        gross = Decimal(node.mps.quantity)
    else:
        loss = node.material.loss_rate
        gross = (
            Decimal(node.parent.net)
            * node.edge.quantity
            / (Decimal("1") - loss)
        )
    required = int(gross.to_integral_value(rounding=ROUND_CEILING))

    s = stock[node.material.code]
    available = s["process"] + s["material"]
    net = max(0, required - available)

    used = min(required, available)
    from_material = min(s["material"], used)
    s["material"] -= from_material
    s["process"] -= used - from_material

    node.net = net
    node.processed = True
    MrpResult.objects.create(
        mps_record=node.mps,
        material=node.material,
        parent=node.parent.material if node.parent else None,
        allocation_method=node.material.allocation_method,
        demand_quantity=net,
        release_date=node.release_date,
        completion_date=node.completion_date,
        level=node.level,
        order_index=node.order_index,
    )


@transaction.atomic
def run_mrp():
    """对所有 MPS 记录执行 MRP 计算。

    难点处理：
    1) 多条 MPS 展开后涉及相同子物料：全局共享库存，按"日程下达日期最早"
       的顺序处理节点；若目标节点的祖先尚未处理，则自上而下先处理祖先
       （祖先必为其他物料，BOM 无环时不会影响同物料的扣减顺序）。
    2) 中间物料有库存：子物料的毛需求按父物料的净需求展开，
       净需求 = max(0, ceil(父净需求×构成数/(1-损耗率)) - 工序库存 - 资材库存)。
    """
    MrpResult.objects.all().delete()

    stock = {m.code: {"process": 0, "material": 0} for m in Material.objects.all()}
    for inv in Inventory.objects.select_related("material"):
        stock[inv.material_id] = {
            "process": inv.process_stock,
            "material": inv.material_stock,
        }

    edges_by_parent = {}
    for edge in BomStructure.objects.select_related("parent", "child").order_by("id"):
        edges_by_parent.setdefault(edge.parent_id, []).append(edge)

    counter = iter(range(10**9))
    nodes = []
    for idx, mps in enumerate(
        MpsRecord.objects.select_related("product").order_by("completion_date", "id")
    ):
        nodes.extend(_build_tree(mps, idx, edges_by_parent, counter))

    remaining = [n for n in nodes]
    while remaining:
        target = min(
            remaining,
            key=lambda n: (n.release_date, n.level, n.order_index, n.seq),
        )
        chain = []
        cur = target
        while cur is not None and not cur.processed:
            chain.append(cur)
            cur = cur.parent
        for node in reversed(chain):
            _process(node, stock)
        remaining = [n for n in remaining if not n.processed]

    return MrpResult.objects.count()


def query_formulas(raw_names, expand=False):
    """输入多个变量名，输出各自对应的资产负债表公式。"""
    names = [n.strip() for n in re.split(r"[,，;；\s]+", raw_names) if n.strip()]
    results = []
    for name in names:
        formula = BalanceFormula.objects.filter(variable__iexact=name).first()
        if formula is None:
            results.append({"variable": name, "found": False, "expression": None})
        else:
            expr = formula.expression
            if expand:
                expr = expand_expression(expr)
            results.append({"variable": formula.variable, "found": True, "expression": expr})
    return results


def expand_expression(expression, depth=0):
    """把公式中的嵌套变量递归替换为其公式（加括号），直到只剩基础变量。"""
    if depth > 20:
        return expression

    def repl(match):
        var = match.group(0)
        formula = BalanceFormula.objects.filter(variable__iexact=var).first()
        if formula is None:
            return var
        return "(" + expand_expression(formula.expression, depth + 1) + ")"

    return re.sub(r"[A-Za-z]+\d*", repl, expression)

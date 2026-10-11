import datetime

from django.core.management import call_command
from django.test import TestCase

from .models import Inventory, MpsRecord, MrpResult
from .services import query_formulas, run_mrp

D = datetime.date


def result_map():
    """(物料代码, 父物料代码) -> [(需求数量, 下达日期, 完成日期), ...]（按订单序号）"""
    rows = {}
    for r in MrpResult.objects.select_related("material", "parent").order_by("order_index"):
        key = (r.material_id, r.parent_id)
        rows.setdefault(key, []).append((r.demand_quantity, r.release_date, r.completion_date))
    return rows


class SingleOrderMrpTests(TestCase):
    """单条 MPS：眼镜 100 副 @ 2022-05-30（与手算答案对照）"""

    def setUp(self):
        call_command("seed_data", verbosity=0)
        run_mrp()
        self.rows = result_map()

    def test_row_count(self):
        self.assertEqual(MrpResult.objects.count(), 8)

    def test_top_product(self):
        self.assertEqual(
            self.rows[("20000", None)], [(100, D(2022, 5, 29), D(2022, 5, 30))]
        )

    def test_frame(self):
        self.assertEqual(
            self.rows[("20100", "20000")], [(100, D(2022, 5, 27), D(2022, 5, 29))]
        )

    def test_frame_parts(self):
        self.assertEqual(
            self.rows[("20110", "20100")], [(100, D(2022, 5, 6), D(2022, 5, 27))]
        )
        self.assertEqual(
            self.rows[("20120", "20100")], [(170, D(2022, 5, 16), D(2022, 5, 27))]
        )
        self.assertEqual(
            self.rows[("20130", "20100")], [(200, D(2022, 5, 8), D(2022, 5, 27))]
        )

    def test_lens(self):
        self.assertEqual(
            self.rows[("20300", "20000")], [(200, D(2022, 5, 8), D(2022, 5, 29))]
        )

    def test_screw_deeper_level_takes_stock_first(self):
        # 镜框下的螺钉（层次2）先拿掉库存 10+50：ceil(100*4/0.9)-60 = 385
        self.assertEqual(
            self.rows[("20109", "20100")], [(385, D(2022, 5, 16), D(2022, 5, 27))]
        )
        # 眼镜下的螺钉（层次1）已无库存可用：ceil(100*2/0.9) = 223
        self.assertEqual(
            self.rows[("20109", "20000")], [(223, D(2022, 5, 18), D(2022, 5, 29))]
        )


class MultiOrderMrpTests(TestCase):
    """多条 MPS：共享库存，先处理的订单先占用库存"""

    def setUp(self):
        call_command("seed_data", verbosity=0)
        MpsRecord.objects.create(
            product_id="20000", quantity=300, completion_date=D(2022, 6, 3)
        )
        run_mrp()
        self.rows = result_map()

    def test_second_order_gets_no_stock(self):
        # 第二张订单的镜腿：库存已被第一单耗尽，300*2 = 600
        quantities = [q for q, _, _ in self.rows[("20120", "20100")]]
        self.assertEqual(quantities, [170, 600])

    def test_second_order_screw(self):
        # 第二单镜框下的螺钉：ceil(300*4/0.9) = 1334，无库存可扣
        quantities = [q for q, _, _ in self.rows[("20109", "20100")]]
        self.assertEqual(quantities, [385, 1334])

    def test_row_count(self):
        self.assertEqual(MrpResult.objects.count(), 16)


class IntermediateStockTests(TestCase):
    """中间物料（镜框）有库存时，子物料需求按净需求展开"""

    def setUp(self):
        call_command("seed_data", verbosity=0)
        Inventory.objects.filter(material_id="20100").update(
            process_stock=10, material_stock=20
        )
        run_mrp()
        self.rows = result_map()

    def test_frame_net_demand(self):
        self.assertEqual(self.rows[("20100", "20000")][0][0], 70)

    def test_children_based_on_net(self):
        self.assertEqual(self.rows[("20110", "20100")][0][0], 70)
        self.assertEqual(self.rows[("20120", "20100")][0][0], 110)  # 70*2 - 30
        self.assertEqual(self.rows[("20130", "20100")][0][0], 140)
        # ceil(70*4/0.9) - 60 = 312 - 60 = 252
        self.assertEqual(self.rows[("20109", "20100")][0][0], 252)

    def test_lens_unaffected(self):
        self.assertEqual(self.rows[("20300", "20000")][0][0], 200)


class FormulaQueryTests(TestCase):
    def setUp(self):
        call_command("seed_data", verbosity=0)

    def test_single_variable(self):
        results = query_formulas("b1")
        self.assertEqual(results[0]["expression"], "a7+a9")

    def test_multiple_variables(self):
        results = query_formulas("b1, b3")
        self.assertEqual(len(results), 2)
        self.assertEqual(
            results[1]["expression"],
            "a1+a3+a5+b1+a12+a14+a16+a18+a20+a22+a24+a26",
        )

    def test_expand_nested(self):
        results = query_formulas("b3", expand=True)
        self.assertIn("(a7+a9)", results[0]["expression"])
        self.assertNotIn("b1+", results[0]["expression"].replace("(a7+a9)", ""))

    def test_unknown_variable(self):
        results = query_formulas("x9")
        self.assertFalse(results[0]["found"])

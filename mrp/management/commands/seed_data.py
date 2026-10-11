import datetime

from django.core.management.base import BaseCommand

from mrp.models import (
    BalanceFormula,
    BomStructure,
    Inventory,
    Material,
    MpsRecord,
)

MATERIALS = [
    # code, name, unit, allocation_method, loss_rate, operation_lead_time
    ("20000", "眼镜", "副", Material.PRODUCE, "0.00", 1),
    ("20100", "镜框", "个", Material.PRODUCE, "0.00", 2),
    ("20110", "镜架", "个", Material.PURCHASE, "0.00", 0),
    ("20120", "镜腿", "个", Material.PURCHASE, "0.00", 0),
    ("20130", "鼻托", "个", Material.PURCHASE, "0.00", 0),
    ("20109", "螺钉", "个", Material.PURCHASE, "0.10", 0),
    ("20300", "镜片", "个", Material.PURCHASE, "0.00", 0),
]

BOM_EDGES = [
    # standard, zone, parent, child, quantity, preparation_lead, supplier_lead
    ("000001", "L001", "20000", "20100", "1", 0, 0),
    ("000001", "L001", "20000", "20300", "2", 1, 20),
    ("000001", "L001", "20000", "20109", "2", 1, 10),
    ("000001", "L003", "20100", "20110", "1", 1, 20),
    ("000001", "L003", "20100", "20120", "2", 1, 10),
    ("000001", "L003", "20100", "20130", "2", 1, 18),
    ("000001", "L003", "20100", "20109", "4", 1, 10),
]

INVENTORY = [
    # code, process_stock, material_stock
    ("20000", 0, 0),
    ("20109", 10, 50),
    ("20100", 0, 0),
    ("20110", 0, 0),
    ("20120", 10, 20),
    ("20130", 0, 0),
    ("20300", 0, 0),
]

MPS = [
    ("20000", 100, datetime.date(2022, 5, 30)),
]

FORMULAS = [
    ("b1", "a7+a9", "货币资金"),
    ("b2", "a10+a11", "短期投资"),
    ("b3", "a1+a3+a5+b1+a12+a14+a16+a18+a20+a22+a24+a26", "流动资产合计"),
    ("b4", "a28+a29+a30", "长期投资合计"),
    ("b5", "a32+a33-a34", "固定资产净值"),
    ("b6", "b3+b4+b5+a36+a37", "资产总计"),
    ("c1", "a39+a40+a41", "流动负债合计"),
    ("c2", "a43+a44", "长期负债合计"),
    ("c3", "c1+c2", "负债合计"),
    ("d1", "a46+a47+a48", "所有者权益合计"),
    ("z1", "c3+d1", "负债和所有者权益总计"),
]


class Command(BaseCommand):
    help = "导入眼镜 BOM 示例数据与资产负债公式（幂等，可重复执行）"

    def handle(self, *args, **options):
        for code, name, unit, method, loss, lead in MATERIALS:
            Material.objects.update_or_create(
                code=code,
                defaults={
                    "name": name,
                    "unit": unit,
                    "allocation_method": method,
                    "loss_rate": loss,
                    "operation_lead_time": lead,
                },
            )
        for standard, zone, parent, child, qty, prep, supplier in BOM_EDGES:
            BomStructure.objects.update_or_create(
                parent_id=parent,
                child_id=child,
                defaults={
                    "standard_code": standard,
                    "zone_code": zone,
                    "quantity": qty,
                    "preparation_lead_time": prep,
                    "supplier_lead_time": supplier,
                },
            )
        for code, process, material in INVENTORY:
            Inventory.objects.update_or_create(
                material_id=code,
                defaults={"process_stock": process, "material_stock": material},
            )
        if not MpsRecord.objects.exists():
            for code, qty, date in MPS:
                MpsRecord.objects.create(product_id=code, quantity=qty, completion_date=date)
        for variable, expression, description in FORMULAS:
            BalanceFormula.objects.update_or_create(
                variable=variable,
                defaults={"expression": expression, "description": description},
            )
        self.stdout.write(self.style.SUCCESS("示例数据导入完成。"))

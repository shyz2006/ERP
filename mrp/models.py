from django.db import models


class Material(models.Model):
    """物料表"""

    PRODUCE = "生产"
    PURCHASE = "采购"
    ALLOCATION_CHOICES = [(PRODUCE, "生产"), (PURCHASE, "采购")]

    code = models.CharField("物料代码", max_length=20, primary_key=True)
    name = models.CharField("物料名称", max_length=50)
    unit = models.CharField("单位", max_length=10, default="个")
    allocation_method = models.CharField("调配方式", max_length=10, choices=ALLOCATION_CHOICES)
    loss_rate = models.DecimalField("损耗率", max_digits=5, decimal_places=4, default=0)
    operation_lead_time = models.PositiveIntegerField("作业提前期(天)", default=0)

    class Meta:
        verbose_name = "物料"
        verbose_name_plural = "物料表"

    def __str__(self):
        return f"{self.code} {self.name}"


class BomStructure(models.Model):
    """调配构成表（BOM）：一条记录表示 父物料 -> 子物料 的构成关系"""

    standard_code = models.CharField("调配标准编号", max_length=20, default="000001")
    zone_code = models.CharField("调配区代码", max_length=20, default="L001")
    parent = models.ForeignKey(
        Material, verbose_name="父物料", on_delete=models.CASCADE, related_name="child_edges"
    )
    child = models.ForeignKey(
        Material, verbose_name="子物料", on_delete=models.CASCADE, related_name="parent_edges"
    )
    quantity = models.DecimalField("构成数", max_digits=10, decimal_places=4, default=1)
    preparation_lead_time = models.PositiveIntegerField("配料提前期(天)", default=0)
    supplier_lead_time = models.PositiveIntegerField("供应商提前期(天)", default=0)

    class Meta:
        verbose_name = "调配构成"
        verbose_name_plural = "调配构成表"
        unique_together = ("parent", "child")

    def __str__(self):
        return f"{self.parent.name} -> {self.child.name} x{self.quantity}"


class Inventory(models.Model):
    """库存表"""

    material = models.OneToOneField(Material, verbose_name="物料", on_delete=models.CASCADE)
    process_stock = models.PositiveIntegerField("工序库存", default=0)
    material_stock = models.PositiveIntegerField("资材库存", default=0)

    class Meta:
        verbose_name = "库存"
        verbose_name_plural = "库存表"

    def __str__(self):
        return f"{self.material.name}: 工序{self.process_stock} 资材{self.material_stock}"


class MpsRecord(models.Model):
    """主生产计划（MPS）记录"""

    product = models.ForeignKey(Material, verbose_name="产品", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField("数量")
    completion_date = models.DateField("完工日期")

    class Meta:
        verbose_name = "主生产计划"
        verbose_name_plural = "主生产计划"
        ordering = ["completion_date", "id"]

    def __str__(self):
        return f"{self.product.name} x{self.quantity} @ {self.completion_date}"


class MrpResult(models.Model):
    """MRP 计算结果（采购/生产计划的明细行）"""

    mps_record = models.ForeignKey(
        MpsRecord, verbose_name="来源MPS", on_delete=models.CASCADE, related_name="results"
    )
    material = models.ForeignKey(
        Material, verbose_name="物料", on_delete=models.CASCADE, related_name="mrp_results"
    )
    parent = models.ForeignKey(
        Material, verbose_name="父物料", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="child_mrp_results",
    )
    allocation_method = models.CharField("调配方式", max_length=10)
    demand_quantity = models.PositiveIntegerField("需求数量")
    release_date = models.DateField("日程下达日期")
    completion_date = models.DateField("日程完成日期")
    level = models.PositiveIntegerField("层次", default=0)
    order_index = models.PositiveIntegerField("订单序号", default=0)

    class Meta:
        verbose_name = "MRP结果"
        verbose_name_plural = "MRP计算结果"
        ordering = ["release_date", "material__code"]

    def __str__(self):
        return f"{self.allocation_method} {self.material.name} x{self.demand_quantity}"


class BalanceFormula(models.Model):
    """资产负债表公式查询表"""

    variable = models.CharField("变量名", max_length=20, unique=True)
    expression = models.CharField("公式", max_length=500)
    description = models.CharField("含义", max_length=100, blank=True, default="")

    class Meta:
        verbose_name = "资产负债公式"
        verbose_name_plural = "资产负债公式表"
        ordering = ["variable"]

    def __str__(self):
        return f"{self.variable} = {self.expression}"

from django.contrib import admin

from .models import (
    BalanceFormula,
    BomStructure,
    Inventory,
    Material,
    MpsRecord,
    MrpResult,
)


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "unit", "allocation_method", "loss_rate", "operation_lead_time")


@admin.register(BomStructure)
class BomStructureAdmin(admin.ModelAdmin):
    list_display = ("parent", "child", "quantity", "preparation_lead_time", "supplier_lead_time")


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ("material", "process_stock", "material_stock")


@admin.register(MpsRecord)
class MpsRecordAdmin(admin.ModelAdmin):
    list_display = ("product", "quantity", "completion_date")


@admin.register(MrpResult)
class MrpResultAdmin(admin.ModelAdmin):
    list_display = (
        "material",
        "allocation_method",
        "demand_quantity",
        "release_date",
        "completion_date",
    )


@admin.register(BalanceFormula)
class BalanceFormulaAdmin(admin.ModelAdmin):
    list_display = ("variable", "expression", "description")

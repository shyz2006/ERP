from django import forms

from .models import BalanceFormula, BomStructure, Inventory, Material, MpsRecord


class BootstrapMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = "form-check-input" if isinstance(field.widget, forms.CheckboxInput) else "form-control"
            field.widget.attrs.setdefault("class", css)


class MaterialForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Material
        fields = ["code", "name", "unit", "allocation_method", "loss_rate", "operation_lead_time"]


class BomStructureForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = BomStructure
        fields = [
            "standard_code",
            "zone_code",
            "parent",
            "child",
            "quantity",
            "preparation_lead_time",
            "supplier_lead_time",
        ]


class InventoryForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Inventory
        fields = ["material", "process_stock", "material_stock"]


class MpsRecordForm(BootstrapMixin, forms.ModelForm):
    completion_date = forms.DateField(
        label="完工日期", widget=forms.DateInput(attrs={"type": "date", "class": "form-control"})
    )

    class Meta:
        model = MpsRecord
        fields = ["product", "quantity", "completion_date"]


class BalanceFormulaForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = BalanceFormula
        fields = ["variable", "expression", "description"]

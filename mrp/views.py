from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    BalanceFormulaForm,
    BomStructureForm,
    InventoryForm,
    MaterialForm,
    MpsRecordForm,
)
from .models import (
    BalanceFormula,
    BomStructure,
    Inventory,
    Material,
    MpsRecord,
    MrpResult,
)
from .services import query_formulas, run_mrp


def dashboard(request):
    context = {
        "material_count": Material.objects.count(),
        "bom_count": BomStructure.objects.count(),
        "inventory_count": Inventory.objects.count(),
        "mps_records": MpsRecord.objects.select_related("product").all(),
        "result_count": MrpResult.objects.count(),
        "formula_count": BalanceFormula.objects.count(),
    }
    return render(request, "mrp/dashboard.html", context)


def _crud_list(request, model, form_class, template, context_key, redirect_name):
    instance = None
    edit_id = request.GET.get("edit")
    if edit_id:
        instance = get_object_or_404(model, pk=edit_id)
    if request.method == "POST":
        if request.POST.get("delete"):
            get_object_or_404(model, pk=request.POST["delete"]).delete()
            messages.success(request, "已删除。")
            return redirect(redirect_name)
        form = form_class(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, "已保存。")
            return redirect(redirect_name)
    else:
        form = form_class(instance=instance)
    context = {context_key: model.objects.all(), "form": form, "editing": instance}
    return render(request, template, context)


def materials(request):
    return _crud_list(
        request, Material, MaterialForm, "mrp/materials.html", "materials", "materials"
    )


def bom(request):
    return _crud_list(
        request, BomStructure, BomStructureForm, "mrp/bom.html", "edges", "bom"
    )


def inventory(request):
    return _crud_list(
        request, Inventory, InventoryForm, "mrp/inventory.html", "inventories", "inventory"
    )


def mps(request):
    return _crud_list(
        request, MpsRecord, MpsRecordForm, "mrp/mps.html", "records", "mps"
    )


def mrp_run(request):
    if request.method == "POST":
        count = run_mrp()
        messages.success(request, f"MRP 计算完成，共生成 {count} 条计划明细。")
    return redirect("mrp_results")


def mrp_results(request):
    results = MrpResult.objects.select_related("material", "parent", "mps_record").all()
    production = [r for r in results if r.allocation_method == Material.PRODUCE]
    purchase = [r for r in results if r.allocation_method == Material.PURCHASE]
    return render(
        request,
        "mrp/mrp_results.html",
        {"production": production, "purchase": purchase, "total": len(results)},
    )


def formula(request):
    if request.method == "POST":
        if request.POST.get("delete"):
            get_object_or_404(BalanceFormula, pk=request.POST["delete"]).delete()
            messages.success(request, "已删除。")
            return redirect("formula")
        form = BalanceFormulaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "已保存。")
            return redirect("formula")
    else:
        form = BalanceFormulaForm()

    names = request.GET.get("names", "")
    expand = request.GET.get("expand") == "1"
    results = query_formulas(names, expand=expand) if names.strip() else None
    return render(
        request,
        "mrp/formula.html",
        {
            "form": form,
            "formulas": BalanceFormula.objects.all(),
            "names": names,
            "expand": expand,
            "results": results,
        },
    )

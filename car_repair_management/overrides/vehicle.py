import frappe
from frappe import _
from frappe.utils import getdate, nowdate, get_first_day


def validate(doc, method=None):
    """Validate vehicle data before saving."""
    _validate_single_active_driver(doc)


def _validate_single_active_driver(doc):
    """Ensure no more than one Active driver exists in custom_drivers."""
    active_drivers = [d for d in (doc.custom_drivers or []) if d.status == "Active"]
    if len(active_drivers) > 1:
        frappe.throw(
            _("A vehicle can only have one active driver at a time. Found {0} active drivers.").format(
                len(active_drivers)
            )
        )


def on_update(doc, method=None):
    """Create a linked Asset when a Vehicle is created/updated with acquisition info."""
    if not frappe.db.exists("DocType", "Asset"):
        return

    # Check if we already have a linked asset
    existing_asset = doc.get("erpnext_asset")
    if not existing_asset:
        # Also check by reverse lookup
        existing_asset = frappe.db.get_value("Asset", {"vehicle": doc.name}, "name")
        if existing_asset:
            doc.db_set("erpnext_asset", existing_asset)
            return

    if existing_asset:
        return

    # Need acquisition_cost and acquisition_date to create an asset
    acq_cost = doc.get("acquisition_cost") or doc.get("vehicle_value")
    acq_date = doc.get("acquisition_date")
    if not (acq_date and acq_cost and float(acq_cost) > 0):
        return

    # Ensure master data exists
    if not frappe.db.exists("Asset Category", "Vehicles"):
        return
    if not frappe.db.exists("Item", "VEHICLE-ASSET"):
        return

    try:
        company = doc.company or frappe.defaults.get_global_default("company")
        if not company:
            return

        # Get a valid location
        location_val = doc.location if doc.location and frappe.db.exists("Location", doc.location) else None
        if not location_val:
            location_val = frappe.db.get_value("Location", {"is_group": 0}, "name")
        if not location_val:
            location_val = "Main Office"
            if not frappe.db.exists("Location", location_val):
                frappe.get_doc({
                    "doctype": "Location",
                    "location_name": location_val,
                    "is_group": 0,
                }).insert(ignore_permissions=True)
                frappe.db.commit()

        # Depreciation settings from vehicle or defaults
        dep_method = doc.get("depreciation_method") or "Straight Line"
        dep_months = int(doc.get("depreciation_months") or 60)

        # Determine a depreciation_start_date within an active fiscal year
        dep_start_date = _get_valid_depreciation_start(acq_date, company)

        asset_data = {
            "doctype": "Asset",
            "asset_name": _("Vehicle {0}").format(doc.license_plate or doc.name),
            "item_code": "VEHICLE-ASSET",
            "company": company,
            "purchase_date": acq_date,
            "gross_purchase_amount": float(acq_cost),
            "purchase_amount": float(acq_cost),
            "net_purchase_amount": float(acq_cost),
            "available_for_use_date": dep_start_date,
            "asset_category": "Vehicles",
            "location": location_val,
            "is_existing_asset": 1,
            "calculate_depreciation": 1,
            "vehicle": doc.name,
            "finance_books": [{
                "depreciation_method": dep_method,
                "frequency_of_depreciation": 12,
                "total_number_of_depreciations": dep_months // 12,
                "depreciation_start_date": dep_start_date,
            }],
        }

        asset = frappe.get_doc(asset_data)
        asset.insert(ignore_permissions=True)

        # Link back to vehicle
        doc.db_set("erpnext_asset", asset.name)
        frappe.msgprint(_("Linked Asset {0} created successfully").format(asset.name))

    except Exception:
        frappe.log_error(frappe.get_traceback(), _("Vehicle Asset Creation Error"))

    # Auto-create fuel quota for current month if vehicle has fuel capacity
    _ensure_fuel_quota(doc)

    # Sync insurance data to any linked asset (existing or newly created)
    _sync_insurance_to_asset(doc)


def _ensure_fuel_quota(doc):
    """Auto-create a Vehicle Fuel Quota for the current month if fuel capacity is set."""
    from frappe.utils import flt

    fuel_capacity = flt(doc.get("custom_fuel_capacity_liters"))
    if fuel_capacity <= 0:
        return

    month = getdate(nowdate()).strftime("%Y-%m")
    quota_name = f"FQ-{doc.name}-{month}"

    if frappe.db.exists("Vehicle Fuel Quota", quota_name):
        return

    km_per_liter = flt(doc.get("custom_km_per_liter"))
    monthly_override = flt(doc.get("custom_monthly_fuel_quota"))

    if monthly_override > 0:
        quota_liters = monthly_override
    else:
        quota_liters = fuel_capacity * 2

    try:
        frappe.get_doc({
            "doctype": "Vehicle Fuel Quota",
            "vehicle": doc.name,
            "quota_month": month,
            "fuel_capacity_liters": fuel_capacity,
            "km_per_liter": km_per_liter,
            "quota_liters": quota_liters,
            "consumed_liters": 0,
            "remaining_liters": quota_liters,
            "status": "Active",
        }).insert(ignore_permissions=True)
    except Exception:
        frappe.log_error(frappe.get_traceback(), _("Vehicle Fuel Quota Auto-Creation Error"))


def _sync_insurance_to_asset(doc):
    """Sync insurance fields from Vehicle to linked Asset."""
    asset_name = doc.get("erpnext_asset")
    if not asset_name:
        asset_name = frappe.db.get_value("Asset", {"vehicle": doc.name}, "name")
    if not asset_name:
        return

    insurance_updates = {}
    if doc.get("insurance_company"):
        insurance_updates["insurer"] = doc.insurance_company
    if doc.get("policy_no") or doc.get("insurance_policy"):
        insurance_updates["policy_number"] = doc.get("insurance_policy") or doc.policy_no
    if doc.get("insured_value"):
        insurance_updates["insured_value"] = doc.insured_value
    if doc.get("start_date") or doc.get("insurance_start_date"):
        insurance_updates["insurance_start_date"] = doc.get("insurance_start_date") or doc.start_date
    if doc.get("end_date") or doc.get("insurance_expiry"):
        insurance_updates["insurance_end_date"] = doc.get("insurance_expiry") or doc.end_date
    if doc.get("comprehensive_insurance"):
        insurance_updates["comprehensive_insurance"] = doc.comprehensive_insurance

    if insurance_updates:
        for field, value in insurance_updates.items():
            frappe.db.set_value("Asset", asset_name, field, value, update_modified=False)


def _get_valid_depreciation_start(acq_date, company):
    """Return acq_date if it falls within an active fiscal year, otherwise the start of the earliest active fiscal year."""
    from erpnext.accounts.utils import get_fiscal_year

    acq_date = getdate(acq_date)
    try:
        get_fiscal_year(acq_date, company=company)
        return acq_date
    except Exception:
        pass

    # acq_date is outside all fiscal years – pick the earliest fiscal year start
    earliest = frappe.db.sql(
        "SELECT year_start_date FROM `tabFiscal Year` ORDER BY year_start_date ASC LIMIT 1",
        as_dict=True,
    )
    if earliest:
        return earliest[0].year_start_date

    # Last resort: first day of current month
    return get_first_day(nowdate())

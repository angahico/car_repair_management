import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class RepairOrder(Document):
    pass


def _mutual_exclusion_parts(doc):
    for d in doc.parts_plan or []:
        if d.is_billable and d.is_foc:
            frappe.throw("Parts Plan row cannot be both Billable and FoC")
        if d.item_code and not d.item_name:
            d.item_name = frappe.db.get_value("Item", d.item_code, "item_name")


def on_validate(doc, method=None):
    # Validate order_for requirements
    if getattr(doc, "order_for", "Customer") == "Customer" and not doc.customer:
        frappe.throw("Customer is required when order is for a Customer")
    if getattr(doc, "order_for", "Customer") == "Company" and not doc.company:
        frappe.throw("Company is required when order is for the Company")

    _mutual_exclusion_parts(doc)
    # Auto-populate type from linked Handover Checklist Item
    for item in doc.handover_checklist or []:
        if item.check_item:
            item_type = frappe.db.get_value("Handover Checklist Item", item.check_item, "type")
            if item_type:
                item.type = item_type
    # Basic SLA validations
    if doc.sla_delivery_by and doc.sla_response_by and doc.sla_delivery_by < doc.sla_response_by:
        frappe.throw("SLA Delivery By cannot be before SLA Response By")


def before_save(doc, method=None):
    # Auto-set entry_datetime if not manually edited
    if not doc.entry_datetime:
        doc.entry_datetime = now_datetime()
    # Recompute cost aggregates
    _recompute_costs(doc)


def after_save(doc, method=None):
    pass


def on_submit(doc, method=None):
    # on_submit runs after save, so use db_set to persist the status change
    doc.db_set("status", "Scheduled", update_modified=False)
    doc.status = "Scheduled"
    
    # Expand from Service Template if provided (simple copy)
    if doc.service_template:
        _apply_service_template(doc)


def _create_project_and_tasks(doc):
    """Create project and tasks for a submitted RO."""
    # Create Project
    project = frappe.get_doc({
        "doctype": "Project",
        "project_name": f"RO {doc.name} - {doc.customer or doc.company or ''}",
        "repair_order": doc.name,
        "expected_start_date": now_datetime(),
    }).insert(ignore_permissions=True)
    
    # Create Tasks for each operation
    task_names = []
    for idx, op in enumerate(doc.operations or [], start=1):
        task = frappe.get_doc({
            "doctype": "Task",
            "subject": op.operation_name or f"Operation {idx}",
            "project": project.name,
            "repair_order": doc.name,
            "exp_start_date": now_datetime(),
            "is_group": 0,
        }).insert(ignore_permissions=True)
        task_names.append((op.name, task.name))
    
    # Assign tasks to employees and notify them
    for op_name_val, task_name in task_names:
        op_row = None
        for op in doc.operations or []:
            if op.name == op_name_val:
                op_row = op
                break
        if op_row and op_row.assigned_to:
            from frappe.desk.form.assign_to import add as assign_to
            try:
                assign_to({
                    "doctype": "Task",
                    "name": task_name,
                    "assign_to": [op_row.assigned_to],
                    "description": f"Task for Repair Order {doc.name}: {op_row.operation_name}",
                })
            except Exception:
                frappe.log_error(frappe.get_traceback(), f"Task Assignment: {task_name}")

            try:
                frappe.get_doc({
                    "doctype": "Notification Log",
                    "for_user": op_row.assigned_to,
                    "type": "Assignment",
                    "document_type": "Task",
                    "document_name": task_name,
                    "subject": f"New task assigned: {op_row.operation_name}",
                    "email_content": f"You have been assigned to work on '{op_row.operation_name}' for Repair Order {doc.name}.",
                    "from_user": frappe.session.user,
                }).insert(ignore_permissions=True)
            except Exception:
                frappe.log_error(frappe.get_traceback(), f"Task Notification: {task_name}")

    # Update operation rows with task links and reload doc to get updated child rows
    for op_name, task_name in task_names:
        frappe.db.set_value("Repair Operation Line", op_name, "task", task_name, update_modified=False)
    
    # Update RO with project using db_set which will trigger update after submit
    doc.db_set("project", project.name, update_modified=False)
    frappe.db.commit()
    
    frappe.msgprint(f"Created Project {project.name} and {len(task_names)} tasks", alert=True, indicator="green")


def before_update_after_submit(doc, method=None):
    # Recompute costs on status changes
    _recompute_costs(doc)
    
    # Guard: Ready for Handover requires all QC tasks completed
    if doc.status == "Ready for Handover":
        qc_incomplete = []
        for op in doc.operations or []:
            if op.is_qc and op.task:
                status = frappe.db.get_value("Task", op.task, "status")
                if status not in ("Completed", "Closed"):
                    qc_incomplete.append(op.operation_name or op.task)
        if qc_incomplete:
            frappe.throw("Cannot set Ready for Handover. QC tasks incomplete: " + ", ".join(qc_incomplete))

    # Guard: Close requires Sales Invoices fully paid
    if doc.status in ("Closed",):
        if doc.sales_invoice:
            status = frappe.db.get_value("Sales Invoice", doc.sales_invoice, "status")
            if status not in ("Paid", "Submitted"):
                frappe.throw("Cannot Close. Linked Sales Invoice not fully paid.")
    
    # Snapshot to Job Costing on status transitions
    _update_job_costing_snapshot(doc)


@frappe.whitelist()
def make_quotation_from_repair_order(name: str):
    doc = frappe.get_doc("Repair Order", name)
    quotation = frappe.new_doc("Quotation")
    quotation.quotation_to = "Customer"
    quotation.party_name = doc.customer
    quotation.order_type = "Maintenance"
    quotation.custom_repair_order = doc.name
    # Add operations as service items (zero rate)
    for op in doc.operations or []:
        quotation.append("items", {
            "item_code": None,
            "item_name": op.operation_name or "Service Operation",
            "description": (op.operation_name or "Service Operation"),
            "qty": 1,
            "uom": "Nos",
            "rate": 0,
            "repair_order": doc.name,
            "vehicle": doc.vehicle,
        })
    # Add billable parts
    for part in doc.parts_plan or []:
        if part.is_billable:
            quotation.append("items", {
                "item_code": part.item_code,
                "item_name": part.item_name,
                "description": part.item_name,
                "qty": part.qty_planned or 0,
                "uom": part.uom or frappe.db.get_value("Item", part.item_code, "stock_uom"),
                "repair_order": doc.name,
                "vehicle": doc.vehicle,
            })
    quotation.flags.ignore_permissions = True
    quotation.insert()
    return quotation.as_dict()


@frappe.whitelist()
def make_material_request_from_repair_order(name: str):
    doc = frappe.get_doc("Repair Order", name)
    mr = frappe.new_doc("Material Request")
    mr.material_request_type = "Material Issue"
    mr.company = frappe.defaults.get_user_default("Company")
    # determine a warehouse
    wh = None
    if mr.company:
        try:
            wh = frappe.db.get_value("Company", mr.company, "default_warehouse")
        except Exception:
            wh = None
    if not wh:
        wh = frappe.db.get_value("Warehouse", {"is_group": 0, "company": mr.company})
    for part in doc.parts_plan or []:
        if part.is_billable:
            mr.append("items", {
                "item_code": part.item_code,
                "qty": part.qty_planned or 0,
                "schedule_date": now_datetime(),
                "uom": part.uom or frappe.db.get_value("Item", part.item_code, "stock_uom"),
                "warehouse": wh,
            })
    mr.flags.ignore_permissions = True
    mr.insert()
    return mr.as_dict()


def _apply_service_template(doc):
    template = frappe.get_doc("Service Template", doc.service_template)
    if not doc.operations:
        doc.set("operations", [])
    for d in template.default_operations or []:
        doc.append("operations", {
            "operation_name": d.operation_name,
            "planned_minutes": d.planned_minutes,
            "workstation": d.workstation,
            "is_qc": d.is_qc,
        })
    if not doc.parts_plan:
        doc.set("parts_plan", [])
    for d in template.default_parts or []:
        doc.append("parts_plan", {
            "item_code": d.item_code,
            "item_name": d.item_name or frappe.db.get_value("Item", d.item_code, "item_name"),
            "uom": d.uom,
            "qty_planned": d.qty_planned,
            "is_billable": d.is_billable,
            "is_foc": d.is_foc,
            "notes": d.notes,
        })
    if not doc.handover_checklist:
        doc.set("handover_checklist", [])
    for d in template.default_checklist or []:
        doc.append("handover_checklist", {
            "check_item": d.check_item,
            "type": d.type,
        })


@frappe.whitelist()
def apply_service_template(name: str, template: str):
    """Apply service template to an existing Repair Order (before submit)."""
    doc = frappe.get_doc("Repair Order", name)
    if doc.docstatus != 0:
        frappe.throw("Cannot apply template to submitted Repair Order")
    doc.service_template = template
    _apply_service_template(doc)
    doc.save(ignore_permissions=True)
    return doc.as_dict()


@frappe.whitelist()
def make_sales_order_from_quotation(quotation_name: str):
    """Create Sales Order from Quotation, carrying over RO link and project."""
    from erpnext.selling.doctype.quotation.quotation import _make_sales_order
    quotation = frappe.get_doc("Quotation", quotation_name)
    so_doc = _make_sales_order(quotation_name)
    
    # Carry over RO link from quotation
    if hasattr(quotation, 'custom_repair_order') and quotation.custom_repair_order:
        so_doc.custom_repair_order = quotation.custom_repair_order
        
        # Get and set project from RO
        ro = frappe.get_doc("Repair Order", quotation.custom_repair_order)
        if ro.project:
            so_doc.project = ro.project
        
        # Also set RO link on items (for tracking)
        for item in so_doc.items:
            item.repair_order = quotation.custom_repair_order
            if ro.vehicle:
                item.vehicle = ro.vehicle
    
    return so_doc


@frappe.whitelist()
def make_sales_invoice_from_sales_order(sales_order_name: str):
    """Create Sales Invoice from Sales Order, carrying over RO link."""
    from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice
    sales_order = frappe.get_doc("Sales Order", sales_order_name)
    si = make_sales_invoice(sales_order_name)
    
    # Carry over RO link from sales order
    if hasattr(sales_order, 'custom_repair_order') and sales_order.custom_repair_order:
        si.custom_repair_order = sales_order.custom_repair_order
        
        # Get RO for additional info
        ro = frappe.get_doc("Repair Order", sales_order.custom_repair_order)
        
        # Set RO link on items (for tracking)
        for item in si.items:
            item.repair_order = sales_order.custom_repair_order
            if ro.vehicle:
                item.vehicle = ro.vehicle
    
    return si


def _recompute_costs(doc):
    """Compute parts_cost, labor_cost, other_charges, total_job_cost, quoted_amount, invoiced_amount, gross_margin."""
    # Parts cost from planned parts (valuation rate)
    parts_cost = 0
    for d in doc.parts_plan or []:
        rate = frappe.db.get_value("Item", d.item_code, "valuation_rate") if d.item_code else 0
        try:
            rate = float(rate or 0)
        except Exception:
            rate = 0
        parts_cost += (float(d.qty_planned or 0) * rate)
    
    # Labor cost from actual timesheets linked to this RO or its project/tasks
    labor_cost = 0.0
    if doc.name:
        # Direct RO link
        ts_hours = frappe.db.sql(
            """
            select sum(tl.hours * tl.billing_rate) as cost
            from `tabTimesheet` ts
            join `tabTimesheet Detail` tl on tl.parent = ts.name
            where ts.docstatus = 1 and ts.repair_order = %s
            """,
            doc.name
        )
        if ts_hours and ts_hours[0][0]:
            labor_cost += float(ts_hours[0][0])
        
        # Via project link (project is in Timesheet Detail, not Timesheet parent)
        if doc.project:
            ts_proj = frappe.db.sql(
                """
                select sum(tl.hours * tl.billing_rate) as cost
                from `tabTimesheet` ts
                join `tabTimesheet Detail` tl on tl.parent = ts.name
                where ts.docstatus = 1 and tl.project = %s
                """,
                doc.project
            )
            if ts_proj and ts_proj[0][0]:
                labor_cost += float(ts_proj[0][0])
        
        # Via tasks (find tasks linked to RO)
        task_names = [op.task for op in (doc.operations or []) if op.task]
        if task_names:
            placeholders = ','.join(['%s'] * len(task_names))
            ts_task = frappe.db.sql(
                f"""
                select sum(tl.hours * tl.billing_rate) as cost
                from `tabTimesheet` ts
                join `tabTimesheet Detail` tl on tl.parent = ts.name
                where ts.docstatus = 1 and tl.task in ({placeholders})
                """,
                tuple(task_names)
            )
            if ts_task and ts_task[0][0]:
                labor_cost += float(ts_task[0][0])
    
    # Other charges from Purchase Invoices linked to RO
    other_charges_auto = 0.0
    if doc.name:
        pi_total = frappe.db.sql(
            """
            select sum(grand_total) as total
            from `tabPurchase Invoice`
            where docstatus = 1 and repair_order = %s
            """,
            doc.name
        )
        if pi_total and pi_total[0][0]:
            other_charges_auto = float(pi_total[0][0])
    
    # If other_charges manually set, keep it; else use auto
    if not doc.other_charges:
        doc.other_charges = other_charges_auto
    
    doc.parts_cost = parts_cost
    doc.labor_cost = labor_cost
    doc.total_job_cost = (doc.parts_cost or 0) + (doc.labor_cost or 0) + (doc.other_charges or 0)
    
    # Quoted amount from linked quotation or any quotation with this RO
    quoted = 0.0
    if doc.quotation:
        q_total = frappe.db.get_value("Quotation", doc.quotation, "grand_total")
        quoted = float(q_total or 0)
    elif doc.name:
        # Find quotations linked via parent field
        q_totals = frappe.db.sql(
            """
            select sum(grand_total) as total
            from `tabQuotation`
            where docstatus = 1 and custom_repair_order = %s
            """,
            doc.name
        )
        if q_totals and q_totals[0][0]:
            quoted = float(q_totals[0][0])
    doc.quoted_amount = quoted
    
    # Invoiced amount from linked sales invoice or any SI with this RO
    invoiced = 0.0
    if doc.sales_invoice:
        si_total = frappe.db.get_value("Sales Invoice", doc.sales_invoice, "grand_total")
        invoiced = float(si_total or 0)
    elif doc.name:
        # Find sales invoices linked via parent field
        si_totals = frappe.db.sql(
            """
            select sum(grand_total) as total
            from `tabSales Invoice`
            where docstatus = 1 and custom_repair_order = %s
            """,
            doc.name
        )
        if si_totals and si_totals[0][0]:
            invoiced = float(si_totals[0][0])
    doc.invoiced_amount = invoiced
    
    # Gross margin
    doc.gross_margin = (doc.invoiced_amount or 0) - (doc.total_job_cost or 0)


def update_ro_from_timesheet(timesheet_doc, method=None):
    """Update RO labor cost when timesheet is submitted/cancelled."""
    ro_name = getattr(timesheet_doc, 'repair_order', None)
    if not ro_name:
        # Try via task in time_logs (project is in Timesheet Detail, not parent)
        for d in (timesheet_doc.time_logs or []):
            if d.task:
                ro_name = frappe.db.get_value("Task", d.task, "repair_order")
                if ro_name:
                    break
            # Try via project in time_logs
            if not ro_name and hasattr(d, 'project') and d.project:
                ro_name = frappe.db.get_value("Project", d.project, "repair_order")
                if ro_name:
                    break
    if ro_name:
        ro = frappe.get_doc("Repair Order", ro_name)
        _recompute_costs(ro)
        ro.flags.ignore_validate_update_after_submit = True
        ro.save(ignore_permissions=True)


def update_ro_from_purchase_invoice(pi_doc, method=None):
    """Update RO other_charges when PI is submitted/cancelled."""
    if pi_doc.repair_order:
        ro = frappe.get_doc("Repair Order", pi_doc.repair_order)
        _recompute_costs(ro)
        ro.flags.ignore_validate_update_after_submit = True
        ro.save(ignore_permissions=True)


def update_ro_from_quotation(quotation_doc, method=None):
    """Update RO quoted_amount and quotation field when Quotation is submitted/cancelled."""
    # Find RO via parent field or quotation items
    ro_name = quotation_doc.custom_repair_order if hasattr(quotation_doc, 'custom_repair_order') else None
    if not ro_name:
        for item in (quotation_doc.items or []):
            if hasattr(item, 'repair_order') and item.repair_order:
                ro_name = item.repair_order
                break
    if ro_name:
        ro = frappe.get_doc("Repair Order", ro_name)
        # Update quotation field if not already set (for first quotation only)
        if not ro.quotation and quotation_doc.docstatus == 1:
            ro.quotation = quotation_doc.name
        _recompute_costs(ro)
        ro.flags.ignore_validate_update_after_submit = True
        ro.save(ignore_permissions=True)


def update_ro_from_sales_order(so_doc, method=None):
    """Update RO sales_order field when SO is submitted."""
    # Find RO via parent field or sales order items
    ro_name = so_doc.custom_repair_order if hasattr(so_doc, 'custom_repair_order') else None
    if not ro_name:
        for item in (so_doc.items or []):
            if hasattr(item, 'repair_order') and item.repair_order:
                ro_name = item.repair_order
                break
    if ro_name:
        ro = frappe.get_doc("Repair Order", ro_name)
        # Update sales_order field if not already set (for first SO only)
        if not ro.sales_order and so_doc.docstatus == 1:
            ro.sales_order = so_doc.name
        ro.flags.ignore_validate_update_after_submit = True
        ro.save(ignore_permissions=True)


def update_ro_from_sales_invoice(si_doc, method=None):
    """Update RO invoiced_amount and sales_invoice field when SI is submitted/cancelled."""
    # Find RO via parent field or sales invoice items
    ro_name = si_doc.custom_repair_order if hasattr(si_doc, 'custom_repair_order') else None
    if not ro_name:
        for item in (si_doc.items or []):
            if hasattr(item, 'repair_order') and item.repair_order:
                ro_name = item.repair_order
                break
    if ro_name:
        ro = frappe.get_doc("Repair Order", ro_name)
        # Update sales_invoice field if not already set (for first invoice only)
        if not ro.sales_invoice and si_doc.docstatus == 1:
            ro.sales_invoice = si_doc.name
        _recompute_costs(ro)
        ro.flags.ignore_validate_update_after_submit = True
        ro.save(ignore_permissions=True)


def _update_job_costing_snapshot(doc):
    """Create or update Job Costing record for this RO."""
    if not doc.name:
        return
    jc_name = frappe.db.get_value("Job Costing", {"repair_order": doc.name})
    if jc_name:
        jc = frappe.get_doc("Job Costing", jc_name)
    else:
        jc = frappe.get_doc({
            "doctype": "Job Costing",
            "repair_order": doc.name,
            "project": doc.project,
            "vehicle": doc.vehicle,
        })
    jc.parts_cost = doc.parts_cost or 0
    jc.labor_cost = doc.labor_cost or 0
    jc.other_charges = doc.other_charges or 0
    jc.total_job_cost = doc.total_job_cost or 0
    jc.margin_snapshot = doc.gross_margin or 0
    if jc.name:
        jc.save(ignore_permissions=True)
    else:
        jc.insert(ignore_permissions=True)


@frappe.whitelist()
def set_status(name: str, status: str):
    """Manually set RO status."""
    allowed_statuses = ["Scheduled", "On Hold", "Cancelled", "Ready for Handover"]
    if status not in allowed_statuses:
        frappe.throw(f"Cannot manually set status to {status}. Use buttons for: {', '.join(allowed_statuses)}")
    
    doc = frappe.get_doc("Repair Order", name)
    doc.status = status
    doc.flags.ignore_validate_update_after_submit = True
    doc.save(ignore_permissions=True)
    frappe.msgprint(f"Status updated to {status}", alert=True, indicator="blue")
    return doc.as_dict()


@frappe.whitelist()
def start_work(name: str):
    """Start work on a Repair Order - creates project/tasks and sets status to In Progress."""
    doc = frappe.get_doc("Repair Order", name)
    if doc.docstatus != 1:
        frappe.throw("Repair Order must be submitted before starting work")
    if doc.status not in ("Scheduled",):
        frappe.throw(f"Cannot start work. Current status is {doc.status}")

    # Create project and tasks if not already created
    if not doc.project:
        _create_project_and_tasks(doc)
        # Reload doc to get updated modified timestamp after _create_project_and_tasks
        doc.reload()

    # Update status to In Progress
    doc.status = "In Progress"
    doc.flags.ignore_validate_update_after_submit = True
    doc.save(ignore_permissions=True)

    frappe.msgprint("Work started! Project and tasks created.", alert=True, indicator="green")
    return doc.as_dict()


@frappe.whitelist()
def get_repair_order_detail(name: str):
    """Get comprehensive repair order detail with project progress."""
    doc = frappe.get_doc("Repair Order", name)

    # Get project info and task progress
    project_info = None
    tasks = []
    progress = 0

    if doc.project:
        project = frappe.get_doc("Project", doc.project)
        project_info = {
            "name": project.name,
            "project_name": project.project_name,
            "status": project.status,
            "percent_complete": project.percent_complete,
        }

        tasks = frappe.get_all(
            "Task",
            filters={"project": doc.project},
            fields=["name", "subject", "status", "exp_start_date", "exp_end_date",
                     "_assign", "progress", "completed_on"],
            order_by="creation asc",
        )

        if tasks:
            completed = sum(1 for t in tasks if t.status == "Completed")
            progress = round(completed / len(tasks) * 100)

    return {
        "doc": doc.as_dict(),
        "project": project_info,
        "tasks": tasks,
        "progress": progress,
    }


@frappe.whitelist()
def get_repair_order_timeline(name: str):
    """Get activity timeline for a Repair Order - comments, versions, status changes."""
    import json as _json

    timeline = []

    # Comments on the RO
    comments = frappe.get_all(
        "Comment",
        filters={
            "reference_doctype": "Repair Order",
            "reference_name": name,
            "comment_type": ["in", ["Comment", "Info", "Edit", "Like", "Label"]],
        },
        fields=["name", "comment_by", "creation", "content", "comment_type"],
        order_by="creation desc",
        limit=100,
    )
    for c in comments:
        timeline.append({
            "type": "comment",
            "timestamp": str(c.creation),
            "user": c.comment_by,
            "content": c.content,
            "comment_type": c.comment_type,
        })

    # Version history (field changes)
    versions = frappe.get_all(
        "Version",
        filters={"ref_doctype": "Repair Order", "docname": name},
        fields=["name", "owner", "creation", "data"],
        order_by="creation desc",
        limit=50,
    )
    for v in versions:
        changes = []
        try:
            data = _json.loads(v.data) if v.data else {}
            for change in data.get("changed", []):
                if len(change) >= 3:
                    changes.append({
                        "field": change[0],
                        "old": str(change[1]) if change[1] is not None else "",
                        "new": str(change[2]) if change[2] is not None else "",
                    })
        except Exception:
            pass
        if changes:
            timeline.append({
                "type": "change",
                "timestamp": str(v.creation),
                "user": v.owner,
                "changes": changes,
            })

    # Activity from linked tasks
    doc = frappe.get_doc("Repair Order", name)
    task_names = [op.task for op in (doc.operations or []) if op.task]
    if task_names:
        task_comments = frappe.get_all(
            "Comment",
            filters={
                "reference_doctype": "Task",
                "reference_name": ["in", task_names],
                "comment_type": ["in", ["Comment", "Info"]],
            },
            fields=["name", "comment_by", "creation", "content", "comment_type", "reference_name"],
            order_by="creation desc",
            limit=50,
        )
        for c in task_comments:
            task_subject = frappe.db.get_value("Task", c.reference_name, "subject") or c.reference_name
            timeline.append({
                "type": "task_comment",
                "timestamp": str(c.creation),
                "user": c.comment_by,
                "content": c.content,
                "task": c.reference_name,
                "task_subject": task_subject,
            })

    # Sort by timestamp descending
    timeline.sort(key=lambda x: x["timestamp"], reverse=True)
    return timeline[:100]


@frappe.whitelist()
def get_repair_order_attachments(name: str):
    """Get file attachments for a Repair Order, organized by category."""
    files = frappe.get_all(
        "File",
        filters={
            "attached_to_doctype": "Repair Order",
            "attached_to_name": name,
        },
        fields=["name", "file_name", "file_url", "file_size", "is_private", "owner", "creation"],
        order_by="creation desc",
    )

    folder_config = ["photos", "estimates", "invoices", "reports", "other"]
    folders = {f: [] for f in folder_config}
    counts = {f: 0 for f in folder_config}
    all_files = []

    for f in files:
        file_type = (f.file_name or "").rsplit(".", 1)[-1].lower() if f.file_name else ""
        category = "other"
        fname_lower = (f.file_name or "").lower()
        if fname_lower.startswith("[photos]") or fname_lower.startswith("[photo]"):
            category = "photos"
        elif fname_lower.startswith("[estimates]") or fname_lower.startswith("[estimate]"):
            category = "estimates"
        elif fname_lower.startswith("[invoices]") or fname_lower.startswith("[invoice]"):
            category = "invoices"
        elif fname_lower.startswith("[reports]") or fname_lower.startswith("[report]"):
            category = "reports"

        file_data = {
            "name": f.name,
            "file_name": f.file_name,
            "file_url": f.file_url,
            "size": f.file_size,
            "type": file_type,
            "is_private": f.is_private,
            "uploaded_by": f.owner,
            "upload_date": str(f.creation)[:10] if f.creation else None,
            "category": category,
        }
        folders[category].append(file_data)
        counts[category] += 1
        all_files.append(file_data)

    return {
        "files": all_files,
        "folders": folders,
        "counts": counts,
        "total": len(all_files),
    }


@frappe.whitelist()
def upload_repair_order_attachment(name: str, file_url: str, category: str = "other"):
    """Rename a file to include category prefix for a Repair Order."""
    file_doc = frappe.get_all(
        "File",
        filters={
            "file_url": file_url,
            "attached_to_doctype": "Repair Order",
            "attached_to_name": name,
        },
        fields=["name", "file_name"],
        limit=1,
    )
    if file_doc:
        old_name = file_doc[0].file_name or ""
        # Remove existing category prefix
        import re
        clean_name = re.sub(r"^\[[\w\s]+\]\s*", "", old_name)
        new_name = f"[{category}] {clean_name}"
        frappe.db.set_value("File", file_doc[0].name, "file_name", new_name)
        frappe.db.commit()
    return {"ok": True}


@frappe.whitelist()
def add_repair_order_comment(name: str, content: str):
    """Add a comment to a Repair Order."""
    comment = frappe.get_doc({
        "doctype": "Comment",
        "comment_type": "Comment",
        "reference_doctype": "Repair Order",
        "reference_name": name,
        "content": content,
        "comment_by": frappe.session.user,
        "comment_email": frappe.session.user,
    }).insert(ignore_permissions=True)
    return {
        "name": comment.name,
        "comment_by": comment.comment_by,
        "content": comment.content,
        "creation": str(comment.creation),
    }


@frappe.whitelist()
def get_service_template_data(template_name: str):
    """Get service template data for preview."""
    template = frappe.get_doc("Service Template", template_name)

    operations = []
    for op in template.default_operations or []:
        operations.append({
            "operation_name": op.operation_name,
            "planned_minutes": op.planned_minutes,
            "workstation": op.workstation,
            "is_qc": op.is_qc,
        })

    parts = []
    for part in template.default_parts or []:
        parts.append({
            "item_code": part.item_code,
            "item_name": part.item_name,
            "uom": part.uom,
            "qty_planned": part.qty_planned,
            "is_billable": part.is_billable,
            "is_foc": part.is_foc,
        })

    checklist = []
    for item in template.default_checklist or []:
        checklist.append({
            "check_item": item.check_item,
            "type": item.type,
        })

    # Calculate expected duration
    total_minutes = sum(op.get("planned_minutes", 0) for op in operations)

    return {
        "operations": operations,
        "parts": parts,
        "checklist": checklist,
        "total_minutes": total_minutes,
    }


@frappe.whitelist()
def get_vehicles_for_customer(customer):
    """Get vehicles linked to a customer via the Asset doctype.
    Vehicle has a custom 'erpnext_asset' field linking to Asset.
    Asset has a custom 'vehicle' field linking back to Vehicle.
    The customer relationship is tracked on Asset via asset_owner fields.
    """
    if not customer:
        return []

    # Find vehicles via Asset where customer owns the asset
    vehicles = frappe.db.sql("""
        SELECT DISTINCT v.name, v.license_plate, v.make, v.model
        FROM `tabVehicle` v
        INNER JOIN `tabAsset` a ON a.vehicle = v.name
        WHERE (a.asset_owner = 'Customer' AND a.asset_owner_company = %(customer)s)
        ORDER BY v.license_plate
    """, {"customer": customer}, as_dict=True)

    if not vehicles:
        # Fallback: try custodian match
        vehicles = frappe.db.sql("""
            SELECT DISTINCT v.name, v.license_plate, v.make, v.model
            FROM `tabVehicle` v
            INNER JOIN `tabAsset` a ON a.vehicle = v.name
            WHERE a.custodian = %(customer)s
            ORDER BY v.license_plate
        """, {"customer": customer}, as_dict=True)

    return vehicles


@frappe.whitelist()
def get_vehicles_for_company(company):
    """Get vehicles linked to a company via the Asset doctype."""
    if not company:
        return []

    vehicles = frappe.db.sql("""
        SELECT DISTINCT v.name, v.license_plate, v.make, v.model
        FROM `tabVehicle` v
        INNER JOIN `tabAsset` a ON a.vehicle = v.name
        WHERE a.company = %(company)s
        ORDER BY v.license_plate
    """, {"company": company}, as_dict=True)

    return vehicles


@frappe.whitelist()
def get_operation_detail(repair_order: str, operation_idx: str):
	"""Get detailed info about a specific operation line in a Repair Order."""
	doc = frappe.get_doc("Repair Order", repair_order)
	op_row = None
	for op in doc.operations or []:
		if op.name == operation_idx:
			op_row = op
			break
	if not op_row:
		frappe.throw(f"Operation {operation_idx} not found in {repair_order}")

	# Get linked task details
	task_data = None
	if op_row.task:
		task = frappe.get_doc("Task", op_row.task)
		task_data = {
			"name": task.name,
			"subject": task.subject,
			"status": task.status,
			"priority": task.priority,
			"exp_start_date": str(task.exp_start_date) if task.exp_start_date else None,
			"exp_end_date": str(task.exp_end_date) if task.exp_end_date else None,
			"completed_on": str(task.completed_on) if task.completed_on else None,
			"progress": task.progress,
			"_assign": task._assign,
		}

	# Get workstation details
	workstation_data = None
	if op_row.workstation:
		try:
			ws = frappe.get_doc("Workstation", op_row.workstation)
			workstation_data = {
				"name": ws.name,
				"workstation_name": ws.workstation_name,
				"description": ws.description,
				"production_capacity": ws.production_capacity if hasattr(ws, "production_capacity") else None,
			}
		except Exception:
			workstation_data = {"name": op_row.workstation}

	# Get comments on the linked task
	comments = []
	if op_row.task:
		comments = frappe.get_all(
			"Comment",
			filters={
				"reference_doctype": "Task",
				"reference_name": op_row.task,
				"comment_type": "Comment",
			},
			fields=["name", "comment_by", "comment_email", "content", "creation"],
			order_by="creation asc",
			limit=50,
		)

	# Get issues linked to this RO (general issues)
	issues = []
	if doc.name:
		issues = frappe.get_all(
			"Issue",
			filters={"custom_linked_work_order": doc.name},
			fields=["name", "subject", "status", "priority", "creation"],
			order_by="creation desc",
			limit=20,
		)

	# Get assigned user info
	assigned_user = None
	if op_row.assigned_to:
		user = frappe.get_doc("User", op_row.assigned_to)
		assigned_user = {
			"name": user.name,
			"full_name": user.full_name,
			"user_image": user.user_image,
		}

	return {
		"operation": {
			"name": op_row.name,
			"operation_name": op_row.operation_name,
			"planned_minutes": op_row.planned_minutes,
			"workstation": op_row.workstation,
			"is_qc": op_row.is_qc,
			"assigned_to": op_row.assigned_to,
			"task": op_row.task,
			"status": getattr(op_row, "status", "Open"),
		},
		"task": task_data,
		"workstation": workstation_data,
		"comments": comments,
		"issues": issues,
		"assigned_user": assigned_user,
		"repair_order": {
			"name": doc.name,
			"status": doc.status,
			"vehicle": doc.vehicle,
			"customer": doc.customer,
			"company": doc.company,
		},
	}


@frappe.whitelist()
def update_operation_status(repair_order: str, operation_idx: str, status: str):
	"""Update the status of an operation line and its linked task."""
	allowed = ["Open", "Working", "Pending Review", "Completed", "Rejected", "Cancelled"]
	if status not in allowed:
		frappe.throw(f"Invalid status: {status}")

	doc = frappe.get_doc("Repair Order", repair_order)
	op_row = None
	for op in doc.operations or []:
		if op.name == operation_idx:
			op_row = op
			break
	if not op_row:
		frappe.throw(f"Operation {operation_idx} not found")

	# Update child table row status via db_set
	frappe.db.set_value("Repair Operation Line", operation_idx, "status", status, update_modified=False)

	# Sync to linked Task status
	task_status_map = {
		"Open": "Open",
		"Working": "Working",
		"Pending Review": "Pending Review",
		"Completed": "Completed",
		"Rejected": "Open",
		"Cancelled": "Cancelled",
	}
	if op_row.task:
		task_status = task_status_map.get(status, "Open")
		task = frappe.get_doc("Task", op_row.task)
		task.status = task_status
		task.save(ignore_permissions=True)

	frappe.db.commit()
	return {"status": status}


@frappe.whitelist()
def assign_operation(repair_order: str, operation_idx: str, user: str):
	"""Assign a user to an operation and its linked task."""
	doc = frappe.get_doc("Repair Order", repair_order)
	op_row = None
	for op in doc.operations or []:
		if op.name == operation_idx:
			op_row = op
			break
	if not op_row:
		frappe.throw(f"Operation {operation_idx} not found")

	# Update assigned_to on the operation line
	frappe.db.set_value("Repair Operation Line", operation_idx, "assigned_to", user, update_modified=False)

	# Assign on linked task
	if op_row.task:
		from frappe.desk.form.assign_to import add as assign_to

		try:
			assign_to({
				"doctype": "Task",
				"name": op_row.task,
				"assign_to": [user],
				"description": f"Assigned to operation: {op_row.operation_name}",
			})
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Operation Assignment: {op_row.task}")

	frappe.db.commit()
	return {"assigned_to": user}


@frappe.whitelist()
def add_operation_comment(repair_order: str, operation_idx: str, content: str):
	"""Add a comment to the linked task of an operation."""
	doc = frappe.get_doc("Repair Order", repair_order)
	op_row = None
	for op in doc.operations or []:
		if op.name == operation_idx:
			op_row = op
			break
	if not op_row:
		frappe.throw(f"Operation {operation_idx} not found")

	if not op_row.task:
		frappe.throw("No task linked to this operation. Start work first.")

	comment = frappe.get_doc({
		"doctype": "Comment",
		"comment_type": "Comment",
		"reference_doctype": "Task",
		"reference_name": op_row.task,
		"content": content,
		"comment_by": frappe.session.user,
		"comment_email": frappe.session.user,
	}).insert(ignore_permissions=True)

	return {
		"name": comment.name,
		"comment_by": comment.comment_by,
		"content": comment.content,
		"creation": str(comment.creation),
	}


@frappe.whitelist()
def get_handover_checklist_status(repair_order: str):
	"""Get handover checklist items with their linked inspection status."""
	doc = frappe.get_doc("Repair Order", repair_order)

	items = []
	for row in doc.handover_checklist or []:
		# Find linked Vehicle Inspection for this checklist item + RO
		inspection = frappe.db.get_value(
			"Vehicle Inspection",
			{
				"linked_work_order": doc.name,
				"handover_checklist_item": row.check_item,
			},
			["name", "result", "status", "score", "inspection_date", "inspector"],
			as_dict=True,
		)
		items.append({
			"name": row.name,
			"check_item": row.check_item,
			"type": row.type,
			"value": row.value,
			"notes": row.notes,
			"passed": row.passed,
			"inspection": inspection,
		})

	# Check if all items have passing inspections
	all_passed = bool(items) and all(
		item.get("inspection") and item["inspection"].get("result") == "Pass"
		for item in items
	)

	return {
		"items": items,
		"all_passed": all_passed,
		"total": len(items),
		"passed_count": sum(1 for i in items if i.get("inspection") and i["inspection"].get("result") == "Pass"),
	}


@frappe.whitelist()
def create_handover_inspection(repair_order: str, checklist_item_name: str):
	"""Create a Vehicle Inspection linked to a specific handover checklist item."""
	doc = frappe.get_doc("Repair Order", repair_order)

	# Find the checklist row
	row = None
	for r in doc.handover_checklist or []:
		if r.check_item == checklist_item_name or r.name == checklist_item_name:
			row = r
			break
	if not row:
		frappe.throw(f"Checklist item not found: {checklist_item_name}")

	check_item_label = row.check_item or checklist_item_name

	# Check if inspection already exists
	existing = frappe.db.get_value(
		"Vehicle Inspection",
		{
			"linked_work_order": doc.name,
			"handover_checklist_item": row.check_item,
		},
	)
	if existing:
		frappe.throw(f"Inspection already exists for this checklist item: {existing}")

	# Try to pre-fill inspector from current user's linked Employee
	inspector = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")

	inspection = frappe.get_doc({
		"doctype": "Vehicle Inspection",
		"title": f"Handover: {check_item_label} - {doc.name}",
		"vehicle": doc.vehicle,
		"inspection_date": now_datetime(),
		"inspection_type": "Ad-Hoc",
		"status": "Draft",
		"linked_work_order": doc.name,
		"handover_checklist_item": row.check_item,
		"inspector": inspector,
	}).insert(ignore_permissions=True)

	return inspection.as_dict()

import frappe

no_cache = 1


def get_context(context):
    csrf_token = frappe.sessions.get_csrf_token()
    frappe.db.commit()
    
    context.boot = {
        "csrf_token": csrf_token,
        "user": frappe.session.user,
        "user_id": frappe.session.user,
    }
    return context


@frappe.whitelist(allow_guest=True)
def get_context_for_dev():
    if frappe.session.user == "Guest":
        return {}
    return {
        "csrf_token": frappe.sessions.get_csrf_token(),
        "user": frappe.session.user,
    }

import frappe


@frappe.whitelist()
def get_notifications(limit=20):
	"""Get recent notifications for current user."""
	notifications = frappe.get_all(
		"Notification Log",
		filters={"for_user": frappe.session.user},
		fields=["name", "subject", "email_content", "type", "read", "creation", "document_type", "document_name"],
		order_by="creation desc",
		limit=int(limit),
	)
	unread_count = frappe.db.count("Notification Log", {
		"for_user": frappe.session.user,
		"read": 0,
	})
	return {"notifications": notifications, "unread_count": unread_count}


@frappe.whitelist()
def mark_as_read(name=None):
	"""Mark notification(s) as read."""
	if name:
		frappe.db.set_value("Notification Log", name, "read", 1)
	else:
		frappe.db.sql("""
			UPDATE `tabNotification Log` SET `read`=1
			WHERE for_user=%s AND `read`=0
		""", frappe.session.user)
	frappe.db.commit()
	return {"success": True}

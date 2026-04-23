import json
import frappe


@frappe.whitelist()
def get_document_activity(doctype, name, limit=50):
	"""Get all activity (creation, comments, version changes) for any document.

	Returns a merged, chronologically sorted list of activity entries.
	"""
	limit = int(limit)
	user_map = _build_user_fullname_map()
	activities = []

	# 1. Document creation event
	doc_meta = frappe.db.get_value(doctype, name, ["creation", "owner"], as_dict=True)
	if doc_meta:
		activities.append({
			"type": "created",
			"timestamp": str(doc_meta.creation),
			"user": doc_meta.owner,
			"user_fullname": user_map.get(doc_meta.owner, doc_meta.owner),
			"content": f"Created this {doctype}",
			"details": {},
		})

	# 2. Comments
	comment_types = [
		"Comment", "Info", "Created", "Submitted", "Cancelled", "Updated",
		"Assignment Completed", "Attachment", "Attachment Removed", "Like",
		"Workflow", "Label", "Shared", "Unshared",
	]
	comments = frappe.get_all(
		"Comment",
		filters={
			"reference_doctype": doctype,
			"reference_name": name,
			"comment_type": ["in", comment_types],
		},
		fields=["comment_type", "content", "comment_by", "creation"],
		order_by="creation desc",
	)
	for c in comments:
		activity_type = _map_comment_type(c.comment_type)
		activities.append({
			"type": activity_type,
			"timestamp": str(c.creation),
			"user": c.comment_by,
			"user_fullname": user_map.get(c.comment_by, c.comment_by),
			"content": c.content or c.comment_type,
			"details": {"comment_type": c.comment_type},
		})

	# 3. Version changes
	versions = frappe.get_all(
		"Version",
		filters={
			"ref_doctype": doctype,
			"docname": name,
		},
		fields=["data", "owner", "creation"],
		order_by="creation desc",
	)
	for v in versions:
		try:
			data = json.loads(v.data) if v.data else {}
		except (json.JSONDecodeError, TypeError):
			data = {}

		changed = data.get("changed", [])
		for change in changed:
			if len(change) >= 3:
				field, old_val, new_val = change[0], change[1], change[2]
				activities.append({
					"type": "field_change",
					"timestamp": str(v.creation),
					"user": v.owner,
					"user_fullname": user_map.get(v.owner, v.owner),
					"content": f"Changed {field} from '{old_val}' to '{new_val}'",
					"details": {"field": field, "old_value": old_val, "new_value": new_val},
				})

		row_changed = data.get("row_changed", [])
		for rc in row_changed:
			if len(rc) >= 4:
				child_doctype, child_name, _idx, field_changes = rc[0], rc[1], rc[2], rc[3]
				for fc in field_changes:
					if len(fc) >= 3:
						activities.append({
							"type": "field_change",
							"timestamp": str(v.creation),
							"user": v.owner,
							"user_fullname": user_map.get(v.owner, v.owner),
							"content": f"Changed {fc[0]} from '{fc[1]}' to '{fc[2]}' in {child_doctype} ({child_name})",
							"details": {
								"field": fc[0],
								"old_value": fc[1],
								"new_value": fc[2],
								"child_doctype": child_doctype,
								"child_name": child_name,
							},
						})

		added = data.get("added", [])
		for a in added:
			if len(a) >= 2:
				activities.append({
					"type": "field_change",
					"timestamp": str(v.creation),
					"user": v.owner,
					"user_fullname": user_map.get(v.owner, v.owner),
					"content": f"Added row in {a[0]}",
					"details": {"child_doctype": a[0], "child_name": a[1]},
				})

		removed = data.get("removed", [])
		for r in removed:
			if len(r) >= 2:
				activities.append({
					"type": "field_change",
					"timestamp": str(v.creation),
					"user": v.owner,
					"user_fullname": user_map.get(v.owner, v.owner),
					"content": f"Removed row from {r[0]}",
					"details": {"child_doctype": r[0], "child_name": r[1]},
				})

	# Sort by timestamp descending and apply limit
	activities.sort(key=lambda x: x["timestamp"], reverse=True)
	return activities[:limit]


def _build_user_fullname_map():
	users = frappe.get_all("User", fields=["name", "full_name"])
	return {u.name: u.full_name or u.name for u in users}


def _map_comment_type(comment_type):
	mapping = {
		"Comment": "comment",
		"Info": "info",
		"Created": "created",
		"Submitted": "info",
		"Cancelled": "info",
		"Updated": "info",
		"Assignment Completed": "assignment",
		"Attachment": "attachment",
		"Attachment Removed": "attachment",
		"Like": "info",
		"Workflow": "workflow",
		"Label": "info",
		"Shared": "info",
		"Unshared": "info",
	}
	return mapping.get(comment_type, "info")

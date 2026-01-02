import frappe
from frappe.utils import flt

def capture_packed_items_changes(doc, method):
	"""
	Before validate: Capture user edits to packed_items and store in override fields.
	This runs BEFORE ERPNext's make_packing_list regenerates the items.
	"""
	if not doc.get("packed_items"):
		return
	
	# Store current values in the override fields for persistence
	for item in doc.packed_items:
		# Check if user has edited this item (compare with what bundle would have)
		# For now, just store current values - they will be restored after ERPNext regenerates
		if item.item_code and flt(item.qty) > 0:
			# Store in doc.flags for later restoration
			if not getattr(doc.flags, 'packed_items_edits', None):
				doc.flags.packed_items_edits = {}
			
			# Use parent_item + idx as key
			key = f"{item.parent_item}:{item.idx}"
			doc.flags.packed_items_edits[key] = {
				"item_code": item.item_code,
				"qty": flt(item.qty),
				"custom_is_overridden": item.get("custom_is_overridden") or 0,
				"custom_override_item_code": item.get("custom_override_item_code") or "",
				"custom_override_qty": item.get("custom_override_qty") or 0
			}

def restore_packed_items_changes(doc, method):
	"""
	On update: Restore packed_items from override fields or from captured edits.
	This ensures user edits persist even after ERPNext regenerates from Product Bundle.
	"""
	if not is_packed_items_edit_allowed_for_doctype(doc.doctype):
		return
	
	if not doc.get("packed_items"):
		return
	
	edits = getattr(doc.flags, 'packed_items_edits', {})
	
	items_to_delete = []
	
	# Group by parent_item
	packed_by_parent = {}
	for item in doc.packed_items:
		parent = item.parent_item
		if parent not in packed_by_parent:
			packed_by_parent[parent] = []
		packed_by_parent[parent].append(item)
	
	for parent_item, items in packed_by_parent.items():
		# Count expected items from our edits for this parent
		expected_keys = [k for k in edits.keys() if k.startswith(f"{parent_item}:")]
		expected_count = len(expected_keys)
		
		if expected_count == 0:
			continue
		
		# Remove extras
		if len(items) > expected_count:
			extras = items[expected_count:]
			for extra in extras:
				if extra.name:
					items_to_delete.append(extra.name)
		
		# Restore values for valid items
		for i, item in enumerate(items[:expected_count]):
			key = f"{parent_item}:{i + 1}"
			edit = edits.get(key)
			
			if edit:
				item_name = frappe.db.get_value("Item", edit["item_code"], "item_name") or edit["item_code"]
				
				# Update in database with override fields
				frappe.db.set_value("Packed Item", item.name, {
					"item_code": edit["item_code"],
					"qty": edit["qty"],
					"item_name": item_name,
					"description": item_name,
					"custom_is_overridden": 1,
					"custom_override_item_code": edit["item_code"],
					"custom_override_qty": edit["qty"]
				}, update_modified=False)
	
	# Delete extras
	for name in items_to_delete:
		frappe.db.delete("Packed Item", name)
	
	frappe.db.commit()

def apply_overrides_on_load(doc, method):
	"""
	On load: Apply stored overrides to packed_items.
	This ensures overridden values are shown even when ERPNext loads from Product Bundle.
	"""
	if not is_packed_items_edit_allowed_for_doctype(doc.doctype):
		return
	
	if not doc.get("packed_items"):
		return
	
	for item in doc.packed_items:
		if item.get("custom_is_overridden") and item.get("custom_override_item_code"):
			# Apply the override
			item.item_code = item.custom_override_item_code
			item.qty = flt(item.custom_override_qty) or item.qty
			item_name = frappe.db.get_value("Item", item.item_code, "item_name") or item.item_code
			item.item_name = item_name
			item.description = item_name

def is_packed_items_edit_allowed_for_doctype(doctype):
	"""Check if packed items editing is allowed for a specific doctype via Settings"""
	try:
		settings = frappe.get_single("Delight Shade Settings")
		
		if not settings.allow_packed_items_edit:
			return False
		
		doctype_field_map = {
			"Quotation": "quotation",
			"Sales Order": "sales_order",
			"Delivery Note": "delivery_note",
			"Sales Invoice": "sales_invoice"
		}
		
		field = doctype_field_map.get(doctype)
		if field:
			return bool(getattr(settings, field, False))
		
		return False
	except Exception:
		return False

def is_packed_items_edit_allowed():
	"""Check if packed items editing is allowed via Settings"""
	try:
		settings = frappe.get_single("Delight Shade Settings")
		return bool(settings.allow_packed_items_edit)
	except Exception:
		return False

@frappe.whitelist()
def get_packed_items_edit_setting(doctype=None):
	"""API to check setting from client side"""
	if doctype:
		return is_packed_items_edit_allowed_for_doctype(doctype)
	return is_packed_items_edit_allowed()

def apply_packed_items_override():
	"""Placeholder function for hooks"""
	pass

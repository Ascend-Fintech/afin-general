import frappe
from frappe.utils import flt

def sync_packed_items_to_bundle(doc, method):
	"""
	On save of Quotation/Delivery Note: Sync Packed Items changes back to Product Bundle master.
	Also removes extra packed items that exceed the bundle definition and updates descriptions.
	Only runs if setting is enabled.
	"""
	try:
		settings = frappe.get_single("Delight Shade Settings")
		if not settings.allow_packed_items_edit:
			return
	except Exception as e:
		frappe.log_error(f"Error fetching settings: {e}")
		return
	
	if not doc.get("packed_items"):
		return
	
	# Group packed items by parent_item (the bundle item)
	packed_by_parent = {}
	
	for packed_item in doc.packed_items:
		parent_item = packed_item.parent_item
		if parent_item not in packed_by_parent:
			packed_by_parent[parent_item] = []
		packed_by_parent[parent_item].append(packed_item)
	
	# Check each bundle and remove extras
	items_to_remove = []
	
	for bundle_item_code, packed_items in packed_by_parent.items():
		# Get the expected count from Product Bundle
		if frappe.db.exists("Product Bundle", bundle_item_code):
			bundle = frappe.get_doc("Product Bundle", bundle_item_code)
			expected_count = len(bundle.items)
			
			# If we have more packed items than bundle items, remove the extras (from the end)
			if len(packed_items) > expected_count:
				# The extras are at the end - they are the old replaced items
				extras = packed_items[expected_count:]
				items_to_remove.extend(extras)
	
	# Remove extra items
	if items_to_remove:
		for item in items_to_remove:
			doc.packed_items.remove(item)
		
		# Reindex
		for i, item in enumerate(doc.packed_items):
			item.idx = i + 1
		
		# Delete extras from database
		for item in items_to_remove:
			if item.name:
				frappe.db.sql("""DELETE FROM `tabPacked Item` WHERE name = %s""", item.name)
		frappe.db.commit()
	
	# Rebuild packed_by_parent after removal
	packed_by_parent = {}
	for packed_item in doc.packed_items:
		parent_item = packed_item.parent_item
		if parent_item not in packed_by_parent:
			packed_by_parent[parent_item] = []
		packed_by_parent[parent_item].append(packed_item)
	
	# Now sync changes to Product Bundle
	for bundle_item_code, packed_items in packed_by_parent.items():
		if not frappe.db.exists("Product Bundle", bundle_item_code):
			continue
		
		bundle = frappe.get_doc("Product Bundle", bundle_item_code)
		bundle_updated = False
		
		# Match by position (order) in the items list
		for i, packed_item in enumerate(packed_items):
			if i < len(bundle.items):
				bundle_row = bundle.items[i]
				item_name = frappe.db.get_value("Item", packed_item.item_code, "item_name") or packed_item.item_code
				
				# Update item_code if changed
				if bundle_row.item_code != packed_item.item_code:
					bundle_row.item_code = packed_item.item_code
					bundle_row.description = item_name
					bundle_updated = True
				
				# Update qty - always sync from packed_item to bundle
				packed_qty = flt(packed_item.qty)
				if flt(bundle_row.qty) != packed_qty:
					bundle_row.qty = packed_qty
					bundle_updated = True
				
				# Update packed_item row in database
				frappe.db.set_value("Packed Item", packed_item.name, {
					"description": item_name,
					"item_name": item_name,
					"qty": packed_qty
				}, update_modified=False)
		
		if bundle_updated:
			bundle.flags.ignore_permissions = True
			bundle.flags.ignore_validate = True
			bundle.save()
			frappe.db.commit()
			frappe.msgprint(f"Product Bundle '{bundle_item_code}' updated.", alert=True)

def is_packed_items_edit_allowed():
	"""Check if packed items editing is allowed via Settings"""
	try:
		settings = frappe.get_single("Delight Shade Settings")
		return bool(settings.allow_packed_items_edit)
	except Exception:
		return False

@frappe.whitelist()
def get_packed_items_edit_setting():
	"""API to check setting from client side"""
	return is_packed_items_edit_allowed()

def apply_packed_items_override():
	"""Placeholder function for hooks"""
	pass

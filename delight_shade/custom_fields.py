import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def setup_custom_fields():
	"""
	Creates Custom Fields for Commission Logic if they don't exist.
	Hooked to: after_migrate and after_install
	"""
	
	# Common fields for Header (Commission Account now in Settings)
	header_fields = [
		{
			"fieldname": "custom_additional_charges",
			"label": "Additional Charges",
			"fieldtype": "Currency",
			"insert_after": "total_taxes_and_charges",
			"default": "0"
		},
		{
			"fieldname": "custom_additional_charges_in_percentage",
			"label": "Additional Charges %",
			"fieldtype": "Percent",
			"insert_after": "custom_additional_charges",
			"default": "0"
		}
	]
	
	# Common fields for Item Table
	item_fields = [
		{
			"fieldname": "custom_actual_rate",
			"label": "Actual Rate",
			"fieldtype": "Currency",
			"default": "0",
			"read_only": 1,
			"insert_after": "rate",
			"description": "Original Rate before Commission"
		},
		{
			"fieldname": "custom_exclude_commission",
			"label": "Exclude Commission",
			"fieldtype": "Check",
			"default": "0",
			"insert_after": "custom_actual_rate",
			"description": "If checked, commission will not be applied to this item"
		},
		{
			"fieldname": "custom_commission_amount",
			"label": "Commission Amount",
			"fieldtype": "Currency",
			"default": "0",
			"read_only": 0,
			"insert_after": "custom_exclude_commission",
			"description": "Allocated Commission Amount"
		}
	]
	
	# Define dictionary for create_custom_fields
	all_custom_fields = {
		"Quotation": header_fields,
		"Sales Order": header_fields,
		"Sales Invoice": header_fields,
		
		"Quotation Item": item_fields,
		"Sales Order Item": item_fields,
		"Sales Invoice Item": item_fields,
	}
	
	# Filter out fields that already exist to avoid overwriting/updating if user modified them
	fields_to_create = {}
	
	for doctype, fields in all_custom_fields.items():
		new_fields = []
		for field in fields:
			if not frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": field["fieldname"]}):
				new_fields.append(field)
		
		if new_fields:
			fields_to_create[doctype] = new_fields
	
	if fields_to_create:
		create_custom_fields(fields_to_create, ignore_validate=True)
		frappe.msgprint("Delight Shade: Commission Custom Fields Created.")

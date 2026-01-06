import frappe
from frappe.utils import flt, getdate

def distribute_commission(doc, method):
	"""
	Distributes custom additional charges to items based on Delight Shade Settings.
	Modes:
	1. Manual: Sum of Item Commissions -> Header Additional Charges.
	2. Qty: Header Additional Charges -> Distribute based on Qty -> Item Commission.
	3. Amount: Header Additional Charges -> Distribute based on Amount -> Item Commission.
	"""
	
	try:
		# Fetch Settings
		settings = frappe.get_single("Delight Shade Settings")
		distribution_mode = settings.additional_charges_based_on or "Amount"
	except Exception:
		# Fallback if settings doctype issue
		distribution_mode = "Amount"

	# Prepare items ensuring custom_actual_rate is set
	_ensure_custom_actual_rate(doc)
	
	# Check for manual rate changes by user and update custom_actual_rate
	_update_actual_rate_from_user_input(doc)

	# Logic for Manual Distribution (Bottom-Up)
	if distribution_mode == "Manual":
		# Sum Item Commissions to Header
		total_commission = 0.0
		for item in doc.items:
			# Skip excluded items - ensure they have 0 commission
			if item.get("custom_exclude_commission"):
				item.custom_commission_amount = 0.0
				continue
				
			total_commission += flt(item.custom_commission_amount)
			# Update Rate based on manual commission
			if flt(item.qty) > 0:
				commission_per_qty = flt(item.custom_commission_amount) / flt(item.qty)
				_set_item_rate(item, flt(item.custom_actual_rate) + commission_per_qty)
			
		doc.custom_additional_charges = total_commission
		# Logic regarding percentage in manual mode:
		# Recalculate percentage based on new Total amount vs Net Total
		# This ensures consistency if they switch back to percentage view
		total_net_amount = sum(flt(item.amount) for item in doc.items)
		# Net amount includes commission currently. 
		# Base net amount = sum(actual_rate * qty)
		base_net_amount = sum(flt(item.custom_actual_rate) * flt(item.qty) for item in doc.items)
		
		if base_net_amount > 0:
			doc.custom_additional_charges_in_percentage = (total_commission / base_net_amount) * 100.0
		return

	# Logic for Auto Distribution (Top-Down)
	
	# Reset rates first to get clean base for calculation
	_reset_item_rates(doc)
	
	# Case 1: Percentage Input - Calculate Absolute Amount first
	if flt(doc.get("custom_additional_charges_in_percentage")) > 0:
		total_amount_base = sum(flt(item.custom_actual_rate or item.rate) * flt(item.qty) for item in doc.items)
		if total_amount_base:
			doc.custom_additional_charges = flt(doc.custom_additional_charges_in_percentage) * total_amount_base / 100.0

	additional_charges = flt(doc.get("custom_additional_charges"))
	
	if not additional_charges:
		# If charges are 0, ensure we clear item commissions
		for item in doc.items:
			item.custom_commission_amount = 0.0
		return

	# Distribute based on Mode - Only include non-excluded items in totals
	eligible_items = [item for item in doc.items if not item.get("custom_exclude_commission")]
	excluded_items = [item for item in doc.items if item.get("custom_exclude_commission")]
	
	# Set excluded items commission to 0
	for item in excluded_items:
		item.custom_commission_amount = 0.0
	
	total_qty = sum(flt(item.qty) for item in eligible_items)
	total_amount = sum(flt(item.custom_actual_rate or item.rate) * flt(item.qty) for item in eligible_items)
	
	remaining_charges = additional_charges
	items_count = len(eligible_items)
	
	for i, item in enumerate(eligible_items):
		allocated_commission = 0.0
		
		# Pro-rate Logic
		if distribution_mode == "Qty":
			if total_qty > 0:
				allocated_commission = additional_charges * (flt(item.qty) / total_qty)
		elif distribution_mode == "Amount":
			if total_amount > 0:
				# Use base amount for proportion
				base_line_amount = flt(item.custom_actual_rate) * flt(item.qty)
				allocated_commission = additional_charges * (base_line_amount / total_amount)
		
		# Rounding
		allocated_commission = flt(allocated_commission, item.precision("custom_commission_amount"))
		
		# Handle Last Item Dust
		if i == items_count - 1:
			# Difference check
			currently_allocated = sum(flt(d.custom_commission_amount) for d in eligible_items[:i])
			allocated_commission = additional_charges - currently_allocated
			allocated_commission = flt(allocated_commission, item.precision("custom_commission_amount"))
		
		item.custom_commission_amount = allocated_commission
		
		# Apply to Rate
		if flt(item.qty) > 0:
			commission_per_qty = allocated_commission / flt(item.qty)
			_set_item_rate(item, flt(item.custom_actual_rate) + commission_per_qty)

def _ensure_custom_actual_rate(doc):
	for item in doc.items:
		if not item.get("custom_actual_rate") and flt(item.qty) > 0:
			# Assuming current rate is the actual rate if not set
			item.custom_actual_rate = item.rate

def _update_actual_rate_from_user_input(doc):
	"""
	Detect if user Manually changed the Rate.
	If Rate has changed, we assume they want to change the BASE price.
	New Base = New Rate - (Previous Commission per Qty)
	"""
	for item in doc.items:
		# Only relevant if we have existing commission
		if flt(item.custom_commission_amount) == 0:
			continue
			
		current_rate = flt(item.rate)
		# Calculate what the rate SHOULD be based on known base + comm
		expected_rate = flt(item.custom_actual_rate) + (flt(item.custom_commission_amount) / flt(item.qty) if flt(item.qty) else 0)
		
		# Allow for tiny floating point differences
		if abs(current_rate - expected_rate) > 0.01:
			# User changed the rate!
			# Infer new base.
			# Rate = Base + (Comm / Qty)  =>  Base = Rate - (Comm / Qty)
			comm_per_qty = flt(item.custom_commission_amount) / flt(item.qty) if flt(item.qty) else 0
			new_base = current_rate - comm_per_qty
			
			# Update the base.
			item.custom_actual_rate = flt(new_base, item.precision("rate"))

def _reset_item_rates(doc):
	"""
	Helper: Resets rates to custom_actual_rate to ensure fresh calculation.
	"""
	for item in doc.items:
		if item.get("custom_actual_rate"):
			_set_item_rate(item, item.custom_actual_rate)

def _set_item_rate(item, new_rate):
	item.rate = flt(new_rate, item.precision("rate"))
	item.amount = flt(item.rate * item.qty, item.precision("amount"))
	
	# Also update Net Values
	item.net_rate = item.rate
	item.net_amount = item.amount

def _get_additional_charges_account():
	"""Get commission account from Delight Shade Settings"""
	try:
		settings = frappe.get_single("Delight Shade Settings")
		return settings.additional_charges_account
	except Exception:
		return None

def create_additional_charges_je(doc, method):
	"""
	On Submit of Sales Order: Create a Draft Journal Entry to track additional charges.
	"""
	if not flt(doc.get("custom_additional_charges")):
		return
	
	commission_amount = flt(doc.custom_additional_charges)
	additional_charges_account = _get_additional_charges_account()
	
	if not additional_charges_account:
		frappe.throw("Please configure Commission Account in Delight Shade Settings.")
	
	# Get Company's default cash/bank account
	company_doc = frappe.get_doc("Company", doc.company)
	cash_account = company_doc.default_cash_account or company_doc.default_bank_account
	
	if not cash_account:
		frappe.throw("Please set a Default Cash or Bank Account in Company settings.")
	
	# Get contact info from Sales Order
	contact_person = doc.get("contact_person") or ""
	contact_mobile = doc.get("contact_mobile") or ""
	contact_email = doc.get("contact_email") or ""
	
	# Create Journal Entry in Draft
	je = frappe.new_doc("Journal Entry")
	je.voucher_type = "Journal Entry"
	je.company = doc.company
	je.posting_date = frappe.utils.today()
	je.user_remark = f"Additional Charges for Sales Order {doc.name}"
	
	# Set custom fields
	je.custom_is_additional_charge = 1
	je.custom_contact_person_name = contact_person
	je.custom_contact_person_no = contact_mobile
	je.custom_contact_person_mail = contact_email
	
	# Add accounts - Dr Commission Account, Cr Cash/Bank
	je.append("accounts", {
		"account": additional_charges_account,
		"debit_in_account_currency": commission_amount,
		"credit_in_account_currency": 0,
		"party_type": "",
		"party": "",
		"cost_center": doc.cost_center
	})
	
	je.append("accounts", {
		"account": cash_account,
		"debit_in_account_currency": 0,
		"credit_in_account_currency": commission_amount,
		"party_type": "",
		"party": "",
		"cost_center": doc.cost_center
	})
	
	je.insert(ignore_permissions=True)
	
	frappe.msgprint(f"Draft Journal Entry <a href='/app/journal-entry/{je.name}'>{je.name}</a> created for Additional Charges.", alert=True)

def make_commission_gl_entries(doc, method):
	"""
	On Submit of Sales Invoice: Create GL Entries for commission.
	"""
	if not flt(doc.get("custom_additional_charges")):
		return
		
	commission_amount = flt(doc.custom_additional_charges)
	additional_charges_account = _get_additional_charges_account()
	
	if not additional_charges_account:
		frappe.throw("Please configure Commission Account in Delight Shade Settings.")

	# Get default expense account
	company_doc = frappe.get_doc("Company", doc.company)
	expense_account = company_doc.default_expense_account
	
	if not expense_account:
		# Fallback to trying to find an account named 'Commission'
		expense_account = frappe.db.get_value("Account", {"account_name": "Commission", "company": doc.company, "is_group": 0}, "name")
	
	if not expense_account:
		frappe.throw("Please set a Default Expense Account in Company or create a 'Commission' account.")

	gl_entries = []
	
	# Credit Commission Account (Liability/Payable)
	gl_entries.append(
		doc.get_gl_dict({
			"account": additional_charges_account,
			"credit": commission_amount,
			"debit": 0.0,
			"credit_in_account_currency": commission_amount,
			"debit_in_account_currency": 0.0,
			"against": expense_account,
			"cost_center": doc.cost_center,
			"remarks": "Commission against Invoice " + doc.name
		})
	)

	# Debit Expense Account
	gl_entries.append(
		doc.get_gl_dict({
			"account": expense_account,
			"credit": 0.0,
			"debit": commission_amount,
			"credit_in_account_currency": 0.0,
			"debit_in_account_currency": commission_amount,
			"against": additional_charges_account,
			"cost_center": doc.cost_center,
			"remarks": "Commission Expense against Invoice " + doc.name
		})
	)
	
	from erpnext.accounts.general_ledger import make_gl_entries
	make_gl_entries(gl_entries, cancel=(doc.docstatus == 2))

def cancel_commission_gl_entries(doc, method):
	"""
	On Cancel of Sales Invoice: Reverse GL entries.
	"""
	if not flt(doc.get("custom_additional_charges")):
		return
		
	make_commission_gl_entries(doc, method)

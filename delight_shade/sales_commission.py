import frappe
from frappe.utils import flt, getdate

def distribute_commission(doc, method):
	"""
	Distributes custom additional charges to items.
	Logic:
	1. If percentage is set, calculate total charges based on Net Total.
	2. Distribute charges to items based on their Net Amount.
	3. Update Item Rate = Actual Rate + Allocated Charge per Qty.
	"""
	if not doc.get("custom_additional_charges") and not doc.get("custom_additional_charges_in_percentage"):
		return

	# Handle Percentage Calculation
	if flt(doc.get("custom_additional_charges_in_percentage")) > 0:
		# Calculate based on Net Total (sum of item net amounts)
		# We need to be careful not to cycle endlessly if we update lines and trigger re-calc.
		# Best to use the sum of *custom_actual_rate * qty* as the base, OR use the existing Net Total before modification.
		# But since this runs on validate, we might run multiple times.
		# Let's rely on Items to get the Total.
		
		# Reset Values to logic base if re-running
		_reset_item_rates(doc)
		
		total_amount = sum(flt(item.amount) for item in doc.items)
		if total_amount:
			doc.custom_additional_charges = flt(doc.custom_additional_charges_in_percentage) * total_amount / 100.0

	additional_charges = flt(doc.get("custom_additional_charges"))
	
	if not additional_charges:
		return

	# Re-calculate total to be safe (after reset)
	total_amount = sum(flt(item.amount) for item in doc.items)
	
	if not total_amount:
		return

	# Distribute
	for item in doc.items:
		# Ensure we have the base rate
		if not item.get("custom_actual_rate"):
			item.custom_actual_rate = item.rate
		
		# Fraction of the total amount
		item_proportion = flt(item.amount) / total_amount
		allocated_commission = additional_charges * item_proportion
		
		# Commission per Unit
		if flt(item.qty) > 0:
			commission_per_qty = allocated_commission / flt(item.qty)
			
			# Update Rate
			item.rate = flt(item.custom_actual_rate) + commission_per_qty
			item.amount = item.rate * item.qty
			
			# Trigger standard calculations for taxes etc if needed? 
			# In 'validate', standard Controller logic usually runs afterwards or we might need to manually trigger calculations 
			# depending on if this hook is before or after standard validation.
			# Ideally hooks are cleaner if we let standard logic handle tax re-calculation.

def _reset_item_rates(doc):
	"""
	Helper: Resets rates to custom_actual_rate to ensure fresh calculation.
	"""
	for item in doc.items:
		if item.get("custom_actual_rate") and flt(item.get("custom_actual_rate")) > 0:
			item.rate = item.custom_actual_rate
			item.amount = item.rate * item.qty

def make_commission_gl_entries(doc, method):
	"""
	On Submit of Sales Invoice: Create GL Entries for commission.
	"""
	if not flt(doc.get("custom_additional_charges")):
		return
		
	commission_amount = flt(doc.custom_additional_charges)
	commission_account = doc.get("custom_commission_account")
	
	if not commission_account:
		frappe.throw("Commission Account is missing but Additional Charges are set.")

	# Debit Account: We need an Expense Account. 
	# Strategy: Look for a default Expense Account or 'Commission' account.
	# For now, let's try to find a default from Company settings or throw if not handled.
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
			"account": commission_account,
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
			"against": commission_account,
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
		
	# Logic is identical to creation, but make_gl_entries with cancel=True will handle reversal 
	# IF we pass the same entries. 
	# However, standard practice to reverse custom GL entries is often to just let the system handle it 
	# via 'make_gl_entries' called again with cancel=True.
	# But since we generated them dynamically, we need to regenerate them to cancel them 
	# matching the original logic.
	
	make_commission_gl_entries(doc, method)

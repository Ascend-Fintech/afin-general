import sys
import unittest
from unittest.mock import MagicMock

# Mock frappe and submodules
mock_frappe = MagicMock()
mock_utils = MagicMock()
sys.modules["frappe"] = mock_frappe
sys.modules["frappe.utils"] = mock_utils

import frappe
from frappe.utils import flt

# Setup flt implementation
def simple_flt(val, precision=None):
    try:
        return float(val) if val else 0.0
    except:
        return 0.0

mock_utils.flt = simple_flt
# Also attach to frappe.utils in case it's accessed that way
mock_frappe.utils.flt = simple_flt

# Import the module to test
# We need to add the app path to sys.path
import sys
import os
sys.path.append("/home/simon/frappe-bench/apps/delight_shade")
from delight_shade.sales_commission import distribute_commission

# Mock Settings
mock_settings = MagicMock()
frappe.get_single.return_value = mock_settings

class TestCommissionDistribution(unittest.TestCase):
	def setUp(self):
		self.doc = MagicMock()
		self.doc.items = []
		self.doc.custom_additional_charges_in_percentage = 0
		self.doc.custom_additional_charges = 0
		
		# Helper to create items
		self.create_item = lambda qty, rate, commission=0: MagicMock(
			qty=qty, 
			rate=rate, 
			amount=qty*rate, 
			custom_actual_rate=rate, 
			custom_commission_amount=commission,
			precision=lambda x: 2,
			get=lambda k: rate if k=="custom_actual_rate" else None
		)

		def doc_get(key, default=None):
			return getattr(self.doc, key, default)
		self.doc.get.side_effect = doc_get

	def test_manual_distribution(self):
		# Setup
		mock_settings.commission_distribution_based_on = "Manual"
		
		item1 = self.create_item(10, 100, 50) # Comm = 50
		item2 = self.create_item(5, 200, 30)  # Comm = 30
		self.doc.items = [item1, item2]
		
		distribute_commission(self.doc, "validate")
		
		# Expect Header Total = 50 + 30 = 80
		self.assertEqual(self.doc.custom_additional_charges, 80)
		
		# Expect Rates to update
		# Item 1: Rate = 100 + (50/10) = 105
		self.assertEqual(item1.rate, 105)
		# Item 2: Rate = 200 + (30/5) = 206
		# Item 2: Rate = 200 + (30/5) = 206
		self.assertEqual(item2.rate, 206)
		
		# Check Net Values
		self.assertEqual(item1.net_rate, 105)
		self.assertEqual(item1.net_amount, 105*10)
		self.assertEqual(item2.net_rate, 206)
		self.assertEqual(item2.net_amount, 206*5)

	def test_qty_distribution(self):
		# Setup
		mock_settings.commission_distribution_based_on = "Qty"
		self.doc.custom_additional_charges = 150
		self.doc.custom_additional_charges_in_percentage = 0
		
		item1 = self.create_item(10, 100) # Qty 10
		item2 = self.create_item(5, 200)  # Qty 5
		# Total Qty = 15
		self.doc.items = [item1, item2]
		
		distribute_commission(self.doc, "validate")
		
		# Item 1: (10/15) * 150 = 100
		self.assertEqual(item1.custom_commission_amount, 100)
		# Item 2: (5/15) * 150 = 50
		self.assertEqual(item2.custom_commission_amount, 50)
		
		# Rates
		# Item 1: 100 + (100/10) = 110
		self.assertEqual(item1.rate, 110)

	def test_amount_distribution(self):
		# Setup
		mock_settings.commission_distribution_based_on = "Amount"
		self.doc.custom_additional_charges = 300
		self.doc.custom_additional_charges_in_percentage = 0
		
		item1 = self.create_item(10, 100) # Amount 1000
		item2 = self.create_item(5, 400)  # Amount 2000
		# Total Amount = 3000
		self.doc.items = [item1, item2]
		
		distribute_commission(self.doc, "validate")
		
		# Item 1: (1000/3000) * 300 = 100
		self.assertEqual(item1.custom_commission_amount, 100)
		# Item 2: (2000/3000) * 300 = 200
		self.assertEqual(item2.custom_commission_amount, 200)

	def test_percentage_calculation(self):
		# Setup
		mock_settings.commission_distribution_based_on = "Amount"
		self.doc.custom_additional_charges_in_percentage = 10
		self.doc.custom_additional_charges = 0 # Should be calc'd
		
		item1 = self.create_item(10, 100) # 1000
		item2 = self.create_item(10, 100) # 1000
		# Total Base = 2000
		self.doc.items = [item1, item2]
		
		distribute_commission(self.doc, "validate")
		
		# Total Charges = 10% of 2000 = 200
		self.assertEqual(self.doc.custom_additional_charges, 200)
		
		# Distributed
		self.assertEqual(item1.custom_commission_amount, 100)

if __name__ == "__main__":
	unittest.main()

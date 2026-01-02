// Delight Shade - Packed Items Editable
// Makes item_code and qty editable in packed_items table if setting is enabled for that doctype

frappe.ui.form.on('Quotation', {
    refresh: function (frm) {
        setup_editable_packed_items(frm, 'Quotation');
    },
    onload: function (frm) {
        setup_editable_packed_items(frm, 'Quotation');
    },
    after_save: function (frm) {
        reload_after_packed_items_edit(frm, 'Quotation');
    }
});

frappe.ui.form.on('Sales Order', {
    refresh: function (frm) {
        setup_editable_packed_items(frm, 'Sales Order');
    },
    onload: function (frm) {
        setup_editable_packed_items(frm, 'Sales Order');
    },
    after_save: function (frm) {
        reload_after_packed_items_edit(frm, 'Sales Order');
    }
});

frappe.ui.form.on('Delivery Note', {
    refresh: function (frm) {
        setup_editable_packed_items(frm, 'Delivery Note');
    },
    onload: function (frm) {
        setup_editable_packed_items(frm, 'Delivery Note');
    },
    after_save: function (frm) {
        reload_after_packed_items_edit(frm, 'Delivery Note');
    }
});

frappe.ui.form.on('Sales Invoice', {
    refresh: function (frm) {
        setup_editable_packed_items(frm, 'Sales Invoice');
    },
    onload: function (frm) {
        setup_editable_packed_items(frm, 'Sales Invoice');
    },
    after_save: function (frm) {
        reload_after_packed_items_edit(frm, 'Sales Invoice');
    }
});

// Handle packed_items item_code change - update all related fields
frappe.ui.form.on('Packed Item', {
    item_code: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row && row.item_code) {
            // Fetch all item details and update the row
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Item',
                    name: row.item_code
                },
                callback: function (r) {
                    if (r.message) {
                        let item = r.message;
                        // Update all relevant fields from Item master
                        // Use item_name for description as requested
                        frappe.model.set_value(cdt, cdn, 'item_name', item.item_name || '');
                        frappe.model.set_value(cdt, cdn, 'description', item.item_name || '');
                        frappe.model.set_value(cdt, cdn, 'uom', item.stock_uom || '');
                        frappe.model.set_value(cdt, cdn, 'stock_uom', item.stock_uom || '');
                        frappe.model.set_value(cdt, cdn, 'conversion_factor', 1);

                        // If item has default warehouse, set it
                        if (item.default_warehouse) {
                            frappe.model.set_value(cdt, cdn, 'warehouse', item.default_warehouse);
                        }

                        // Refresh to show updated values
                        frm.refresh_field('packed_items');
                    } else {
                        frappe.msgprint(__('Item {0} not found', [row.item_code]));
                    }
                }
            });
        }
    }
});

function setup_editable_packed_items(frm, doctype) {
    if (!frm.fields_dict.packed_items) {
        return;
    }

    frappe.call({
        method: 'delight_shade.product_bundle_handler.get_packed_items_edit_setting',
        args: {
            doctype: doctype
        },
        async: false,
        callback: function (r) {
            if (r.message) {
                // Make both item_code and qty editable
                frm.fields_dict.packed_items.grid.update_docfield_property('item_code', 'read_only', 0);
                frm.fields_dict.packed_items.grid.update_docfield_property('qty', 'read_only', 0);

                frm.refresh_field('packed_items');
            }
        }
    });
}

function reload_after_packed_items_edit(frm, doctype) {
    // Only reload if packed items editing is enabled for this doctype
    frappe.call({
        method: 'delight_shade.product_bundle_handler.get_packed_items_edit_setting',
        args: {
            doctype: doctype
        },
        async: false,
        callback: function (r) {
            if (r.message && frm.doc.packed_items && frm.doc.packed_items.length > 0) {
                // Reload the document to show updated packed_items values
                frm.reload_doc();
            }
        }
    });
}

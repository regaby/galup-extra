# -*- coding: utf-8 -*-
# Copyright 2015-17 Eficent Business and IT Consulting Services, S.L.
#           (http://www.eficent.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openerp import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.onchange('product_id')
    def product_id_onchange(self):
        product_supplierinfo_obj = self.env['product.supplierinfo']
        partner = self.order_id.partner_id
        product = self.product_id
        if product and partner:
            supplier_info = product_supplierinfo_obj.search([
                '|', ('product_tmpl_id', '=', product.product_tmpl_id.id),
                ('product_id', '=', product.id),
                ('name', '=', partner.id)], limit=1)
            if supplier_info:
                code = supplier_info.product_code or ''
                self.product_supplier_code = code

    product_supplier_code = fields.Char(string='Product Supplier Code')

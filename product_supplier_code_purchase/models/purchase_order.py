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

    def update_product_info(self, order, product, product_supplier_code):
        product_supplierinfo_obj = self.env['product.supplierinfo']
        supplier_info = product_supplierinfo_obj.search([
            '|', ('product_tmpl_id', '=', product.product_tmpl_id.id),
            ('product_id', '=', product.id),
            ('name', '=', order.partner_id.id)], limit=1)
        if supplier_info:
            supplier_info.product_code = product_supplier_code
        else:
            sup_info = {
                'product_tmpl_id': product.product_tmpl_id.id,
                'product_id': product.id,
                'name': order.partner_id.id,
                'product_code': product_supplier_code,
            }
            product_supplierinfo_obj.create(sup_info)

    @api.model
    def create(self, vals):
        if 'product_supplier_code' in vals and 'product_id' in vals and 'order_id' in vals:
            order = self.env['purchase.order'].browse(vals['order_id'])
            product = self.env['product.product'].browse(vals['product_id'])
            self.update_product_info(order, product, vals['product_supplier_code'])
        return super(PurchaseOrderLine, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'product_id' in vals:
            product = self.env['product.product'].browse(vals['product_id'])
        else:
            product = self.product_id
        order = self.order_id
        if 'product_supplier_code' in vals:
            self.update_product_info(order, product, vals['product_supplier_code'])
        return super(PurchaseOrderLine, self).write(vals)


    product_supplier_code = fields.Char(string='Product Supplier Code')

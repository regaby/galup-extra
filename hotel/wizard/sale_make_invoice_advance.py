# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012-Today Serpent Consulting Services PVT. LTD.
#    (<http://www.serpentcs.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
# ---------------------------------------------------------------------------

from openerp import api, fields, models


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    @api.model
    def _get_advance_payment(self):
        ctx = self.env.context.copy()
        if self._context.get('active_model') == 'hotel.folio':
            hotel_fol = self.env['hotel.folio']
            hotel = hotel_fol.browse(self._context.get('active_ids',
                                                       []))
            ctx.update({'active_ids': [hotel.order_id.id],
                        'active_id': hotel.order_id.id})
        return super(SaleAdvancePaymentInv,
                     self.with_context(ctx))._get_advance_payment_method()

    advance_payment_method = fields.Selection([('delivered',
                                                'Invoiceable lines'),
                                               ('all',
                                                'Invoiceable lines\
                                                (deduct down payments)'),
                                               ('percentage',
                                                'Down payment (percentage)'),
                                               ('fixed',
                                                'Down payment (fixed\
                                                amount)')],
                                              string='What do you want\
                                              to invoice?',
                                              default=_get_advance_payment,
                                              required=True)

    @api.multi
    def create_invoices(self):
        ctx = self.env.context.copy()
        hotel = None
        invoice_obj = self.env['account.invoice']
        tax_obj = self.env['account.tax']
        if self._context.get('active_model') == 'hotel.folio':
            hotel_fol = self.env['hotel.folio']
            hotel = hotel_fol.browse(self._context.get('active_ids',
                                                       []))
            ctx.update({'active_ids': [hotel.order_id.id],
                        'active_id': hotel.order_id.id,
                        'invoice_origin': hotel.name})
        res_id = invoice_obj.search([('origin', '=', hotel.name), ('state', '!=', 'cancel')])
        delete = []
        for r in res_id:
            delete.append(r.id)
        res = super(SaleAdvancePaymentInv,
                    self.with_context(ctx)).create_invoices()
        res_id = invoice_obj.search([('origin', '=', hotel.name), ('state', '!=', 'cancel'),
        	                            ('id', 'not in', delete)])
        ## si está marcado early checkin / checkout, quito el impuesto
        # for line in res_id.invoice_line_ids:
        #     tax_ids = line.invoice_line_tax_ids.ids
        #     if hotel.early_checkin:
        #         tax_id = tax_obj.search([('check_type', '=', 'early'),
        #         	                        ('hour_from', '<=', hotel.early_checkin_hour),
        #         	                        ('hour_to', '>=', hotel.early_checkin_hour)])
        #         tax_ids.remove(tax_id.id)
        #     if hotel.late_checkout:
        #         tax_id = tax_obj.search([('check_type', '=', 'late'),
        #         	                        ('hour_from', '<=', hotel.late_checkout_hour),
        #         	                        ('hour_to', '>=', hotel.late_checkout_hour)])
        #         tax_ids.remove(tax_id.id)
        #     line.invoice_line_tax_ids = [(6, 0, tax_ids)]
        ## fin
        if hotel and res_id:
            if res_id.partner_id.parent_id:
                res_id.partner_id = res_id.partner_id.parent_id.id
            hotel.write({'hotel_invoice_id': res_id.id})
        line_ids = self.env['account.invoice.line'].search([('invoice_id', '=', res_id.id)])
        for line in line_ids:
            line.name = 'NOCHE DE ALOJAMIENTO'
        return res

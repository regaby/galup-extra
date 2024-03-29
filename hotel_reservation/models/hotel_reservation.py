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
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.exceptions import except_orm, ValidationError
from dateutil.relativedelta import relativedelta
from openerp import models, fields, api, _
import datetime
from datetime import timedelta
import time
from openerp.addons.hotel.models import hotel
import openerp.addons.decimal_precision as dp
from openerp import workflow

import logging

LOGGER = logging.getLogger(__name__)

class HotelPayment(models.Model):
    _inherit = 'hotel.payment'

    reservation_id = fields.Many2one('hotel.reservation', string='Reserva',
                               ondelete='cascade')

class HotelFolio(models.Model):

    _inherit = 'hotel.folio'
    _order = 'reservation_id desc'

    reservation_id = fields.Many2one(comodel_name='hotel.reservation',
                                     string='Reservation Id')

    @api.multi
    def write(self, vals):
        """
        Overrides orm write method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        """
        folio_write = super(HotelFolio, self).write(vals)
        reservation_line_obj = self.env['hotel.room.reservation.line']
        for folio_obj in self:
            if folio_obj.reservation_id:
                for reservation in folio_obj.reservation_id:
                    reservation_obj = (reservation_line_obj.search
                                       ([('reservation_id', '=',
                                          reservation.id),
                                         ('state', '=', 'assigned')]))
                    if len(reservation_obj) >= 1:
                        for line_id in reservation.reservation_line:
                            line_id = line_id.reserve
                            for room_id in line_id:
                                vals = {'room_id': room_id.id,
                                        'check_in': folio_obj.checkin_date,
                                        'check_out': folio_obj.checkout_date,
                                        'state': 'assigned',
                                        'reservation_id': reservation.id,
                                        }
                                reservation_obj.write(vals)
        return folio_write


class HotelReservation(models.Model):

    _name = "hotel.reservation"
    _rec_name = "reservation_no"
    _description = "Reservation"
    _order = 'reservation_no desc'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    def _get_dur(self, chckin, chckout):
        myduration = 0
        configured_addition_hours = 0
        if chckin and chckout:
            server_dt = DEFAULT_SERVER_DATETIME_FORMAT
            chkin_dt = datetime.datetime.strptime(chckin, server_dt)
            chkout_dt = datetime.datetime.strptime(chckout, server_dt)
            dur = chkout_dt - chkin_dt
            sec_dur = dur.seconds
            additional_hours = abs((dur.seconds / 60) / 60)
            if additional_hours <= 12:
                myduration = dur.days
            else:
                myduration = dur.days + 1
            if configured_addition_hours > 0:
                additional_hours = abs((dur.seconds / 60) / 60)
                if additional_hours >= configured_addition_hours:
                    myduration += 1
        return myduration


    @api.depends('checkin','checkout')
    def _get_duration(self):
        """
        Compute the total amounts of the SO.
        """
        for folio in self:
            folio.duration = self._get_dur(folio.checkin, folio.checkout)

    @api.depends('reservation_line.reserve', 'duration', 'tax_id', 'dolar_rate')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.reservation_line:
                if line.list_price == 0:
                    for room in line.reserve:
                        amount_untaxed += room.price * order.duration
                else:
                    amount_untaxed += line.list_price * order.duration
            if self.dolar_rate:
                amount_untaxed = amount_untaxed * self.dolar_rate
            if self.tax_id:
                ## aplico iva
                amount_tax = (amount_untaxed * self.tax_id.amount) / 100
            order.update({
                'amount_untaxed': amount_untaxed,
                'amount_tax': amount_tax,
                'amount_total': amount_untaxed + amount_tax,
            })

    reservation_no = fields.Char('Reservation No', size=64, readonly=True)
    date_order = fields.Datetime('Date Ordered', required=True, readonly=True,
                                 states={'draft': [('readonly', False)]},
                                 default=(lambda *a:
                                          time.strftime
                                          (DEFAULT_SERVER_DATETIME_FORMAT)))
    warehouse_id = fields.Many2one('stock.warehouse', 'Hotel', readonly=True,
                                   required=True, default=1,
                                   states={'draft': [('readonly', False)]})
    partner_id = fields.Many2one('res.partner', 'Guest Name', readonly=True,
                                 required=True,
                                 states={'draft': [('readonly', False)]})
    pricelist_id = fields.Many2one('product.pricelist', 'Scheme',
                                   required=True, readonly=True,
                                   states={'draft': [('readonly', False)]},
                                   help="Pricelist for current reservation.")
    partner_invoice_id = fields.Many2one('res.partner', 'Invoice Address',
                                         readonly=True,
                                         states={'draft':
                                                 [('readonly', False)]},
                                         help="Invoice address for "
                                         "current reservation.")
    partner_order_id = fields.Many2one('res.partner', 'Ordering Contact',
                                       readonly=True,
                                       states={'draft':
                                               [('readonly', False)]},
                                       help="The name and address of the "
                                       "contact that requested the order "
                                       "or quotation.")
    partner_shipping_id = fields.Many2one('res.partner', 'Delivery Address',
                                          readonly=True,
                                          states={'draft':
                                                  [('readonly', False)]},
                                          help="Delivery address"
                                          "for current reservation. ",)
    checkin = fields.Datetime('Expected-Date-Arrival', required=True,
                              readonly=True,
                              states={'draft': [('readonly', False)]})
    checkout = fields.Datetime('Expected-Date-Departure', required=True,
                               readonly=True,
                               states={'draft': [('readonly', False)]})
#------
    checkin_date = fields.Date('Entrada', required=False,
                              readonly=True,
                              states={'draft': [('readonly', False)]})
    checkout_date = fields.Date('Salida', required=False,
                               readonly=True,
                               states={'draft': [('readonly', False)]})
    checkin_hour = fields.Integer('Hora Entrada', required=False,
                              readonly=True,
                              states={'draft': [('readonly', False)]},default=lambda *a: 12)
    checkout_hour = fields.Integer('Hora Salida', required=False,
                              readonly=True,
                              states={'draft': [('readonly', False)]},default=lambda *a: 10)
#------
    adults = fields.Integer('Adults', size=64, readonly=True,
                            states={'draft': [('readonly', False)]},
                            help='List of adults there in guest list. ', default=1)
    children = fields.Integer('Children', size=64, readonly=True,
                              states={'draft': [('readonly', False)]},
                              help='Number of children there in guest list.')
    reservation_line = fields.One2many('hotel_reservation.line', 'line_id',
                                       'Reservation Line',
                                       help='Detalle de la reserva. Para modificar, debe volver a borrador',readonly=True,
                              states={'draft': [('readonly', False)]}, copy=True)
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm'),
                              ('cancel', 'Cancel'), ('done', 'Done')],
                             'State', readonly=True,
                             default=lambda *a: 'draft')
    folio_id = fields.Many2many('hotel.folio', 'hotel_folio_reservation_rel',
                                'order_id', 'invoice_id', string='Folio')
    dummy = fields.Datetime('Dummy')
    user_id = fields.Many2one('res.users', string='Creado por', index=True, track_visibility='onchange', default=lambda self: self.env.user)
    observations = fields.Text('Observaciones')
    amount_untaxed = fields.Float(string='Subtotal', store=False, readonly=True, compute='_amount_all', track_visibility='always')
    amount_tax = fields.Float(string='Impuesto', store=False, readonly=True, compute='_amount_all', track_visibility='always')
    amount_total = fields.Float(string='Total', store=False, readonly=True, compute='_amount_all', track_visibility='always')
    payment_lines = fields.One2many('hotel.payment', 'reservation_id','Linea de Pagos')
    duration = fields.Integer(string='Duración', store=False, readonly=True, compute='_get_duration', track_visibility='always')
    tax_id = fields.Many2one('account.tax', string="Impuesto")
    dolar_rate = fields.Float('Cotización dolar', readonly=False, default=0)

    @api.onchange('checkin_date', 'checkin_hour')
    def on_change_checkin_date_our(self):
        if self._context.get('tz'):
            to_zone = self._context.get('tz')
        else:
            to_zone = 'UTC'
        if not self.checkin_hour >=0 or not self.checkin_hour <= 24:
          raise ValidationError(_('Seleccione una hora de entrada entre las 0 y las 23.'))
        if self.checkin_date:
          checkin = '%s %s:00:00'%(self.checkin_date, self.checkin_hour+3)
          self.checkin = checkin

    @api.onchange('checkout_date', 'checkout_hour')
    def on_change_checkout_date_our(self):
        if self._context.get('tz'):
            to_zone = self._context.get('tz')
        else:
            to_zone = 'UTC'
        if not self.checkout_hour >=0 or not self.checkout_hour <= 24:
          raise ValidationError(_('Seleccione una hora de salida entre las 0 y las 23.'))
        if self.checkout_date:
          checkout = '%s %s:00:00'%(self.checkout_date, self.checkout_hour+3)
          self.checkout = checkout

    @api.constrains('reservation_line', 'adults', 'children')
    def check_reservation_rooms(self):
        '''
        This method is used to validate the reservation_line.
        -----------------------------------------------------
        @param self: object pointer
        @return: raise a warning depending on the validation
        '''
        cap = 0
        for reservation in self:
            if len(reservation.reservation_line) == 0:
                raise ValidationError(_('Please Select Rooms \
                For Reservation.'))
            for rec in reservation.reservation_line:
                if len(rec.reserve) == 0:
                    raise ValidationError(_('Please Select Rooms \
                    For Reservation.'))
                # cap = rec.categ_id.capacity
                for room in rec.reserve:
                  room_type_obj = self.env['hotel.room.type']
                  room_type_ids = room_type_obj.search([('cat_id', '=', room.product_id.categ_id.id)])
                  cap += room_type_ids.read(fields=['capacity'])[0]['capacity']
                  # cap += room.product_id.categ_id.capacity
            if (self.adults) > cap and cap != 0:
                    raise ValidationError(_('Room Capacity \
                    Exceeded \n Please Select Rooms According to \
                    Members Accomodation.'))

    @api.model
    def _needaction_count(self, domain=None):
        """
         Show a count of draft state reservations on the menu badge.
         """
        return self.search_count([('state', '=', 'draft')])

#    @api.onchange('date_order', 'checkin')
#    def on_change_checkin(self):
#        '''
#        When you change date_order or checkin it will check whether
#        Checkin date should be greater than the current date
#        ------------------------------------------------------------
#        @param self: object pointer
#        @return: raise warning depending on the validation
#        '''
#        if self.date_order and self.checkin:
#            if self.checkin < self.date_order:
#                raise except_orm(_('Warning'), _('Checkin date should be \
#                greater than the current date.'))

    @api.constrains('checkin', 'checkout')
    def check_in_out_dates(self):
        """
        When date_order is less then checkin date or
        Checkout date should be greater than the checkin date.
        """
        if self.checkout and self.checkin:
            # if self.checkin < self.date_order:
            #     raise ValidationError(_('Checkin date should be \
            #     greater than the current date.'))
            if self.checkout < self.checkin:
                raise ValidationError(_('Checkout date \
                should be greater than Checkin date.'))

    @api.onchange('checkout', 'checkin')
    def on_change_checkout(self):
        '''
        When you change checkout or checkin it will check whether
        Checkout date should be greater than Checkin date
        and update dummy field
        -----------------------------------------------------------
        @param self: object pointer
        @return: raise warning depending on the validation
        '''
        checkout_date = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        checkin_date = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        if not (checkout_date and checkin_date):
            return {'value': {}}
        delta = datetime.timedelta(days=1)
        dat_a = time.strptime(checkout_date,
                              DEFAULT_SERVER_DATETIME_FORMAT)[:5]
        addDays = datetime.datetime(*dat_a) + delta
        self.dummy = addDays.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        '''
        When you change partner_id it will update the partner_invoice_id,
        partner_shipping_id and pricelist_id of the hotel reservation as well
        ---------------------------------------------------------------------
        @param self: object pointer
        '''
        if not self.partner_id:
            self.partner_invoice_id = False
            self.partner_shipping_id = False
            self.partner_order_id = False
        else:
            addr = self.partner_id.address_get(['delivery', 'invoice',
                                                'contact'])
            self.partner_invoice_id = addr['invoice']
            self.partner_order_id = addr['contact']
            self.partner_shipping_id = addr['delivery']
            self.pricelist_id = self.partner_id.property_product_pricelist.id

    @api.multi
    def confirmed_reservation(self):
        """
        This method create a new recordset for hotel room reservation line
        ------------------------------------------------------------------
        @param self: The object pointer
        @return: new record set for hotel room reservation line.
        """
        reservation_line_obj = self.env['hotel.room.reservation.line']
        for reservation in self:
            self._cr.execute("""select hr.reservation_no
                             from hotel_reservation as hr
                              inner join hotel_reservation_line as hrl on hrl.line_id = hr.id
                              inner join hotel_reservation_line_room_rel as hrlrr on hrlrr.room_id = hrl.id
                              where (checkin,checkout) overlaps
                                ( timestamp %s, timestamp %s )
                                and hr.id <> cast(%s as integer)
                                and hr.state = 'confirm'
                                and hrlrr.hotel_reservation_line_id in (
                                  select hrlrr.hotel_reservation_line_id
                                    from hotel_reservation as hr
                                    inner join hotel_reservation_line as hrl on hrl.line_id = hr.id
                                    inner join hotel_reservation_line_room_rel as hrlrr on hrlrr.room_id = hrl.id
                                  where hr.id = cast(%s as integer) )""",
                             (reservation.checkin, reservation.checkout,
                              str(reservation.id), str(reservation.id)))
            res = self._cr.fetchone()
            # print self._cr.query
            print res
            roomcount = res and res[0] or 0.0
            if roomcount:
                raise ValidationError(_('Ha tratado de confirmar \
                una reserva con una habitación que ya ha sido reservada en este\
                periodo de reserva. %s')%(res))
            self._cr.execute("""select hf.name
                                from hotel_folio as hf
                                inner join sale_order so on (hf.order_id=so.id)
                                inner join hotel_folio_line hfl on (hf.id=hfl.folio_id)
                                join sale_order_line sol on (hfl.order_line_id=sol.id)
                                inner join folio_room_line frl on (frl.folio_id=hf.id)
                                join hotel_room hr on (frl.room_id=hr.id)
                                where (check_in,check_out) overlaps
                                                                ( timestamp %s, timestamp %s )
                                and so.partner_id <> cast(%s as integer)
                                                                and so.state not in ('cancel','done')
                                and hr.product_id=sol.product_id
                                and hr.id in ( select hrlrr.hotel_reservation_line_id
                                    from hotel_reservation as hr
                                    inner join hotel_reservation_line as hrl on hrl.line_id = hr.id
                                    inner join hotel_reservation_line_room_rel as hrlrr on hrlrr.room_id = hrl.id
                                  where hr.id = cast(%s as integer))""",
                             (reservation.checkin, reservation.checkout,
                              str(reservation.partner_id.id), str(reservation.id)))
            res = self._cr.fetchone()
            # print self._cr.query
            print res
            roomcount = res and res[0] or 0.0
            if roomcount:
                raise ValidationError(_('Ha tratado de confirmar \
                una reserva con una habitación que ya ha sido ocupada en este\
                periodo de reserva. %s')%res)

            else:
                self.write({'state': 'confirm'})
                for line_id in reservation.reservation_line:
                    line_id = line_id.reserve
                    for room_id in line_id:
                        vals = {
                            'room_id': room_id.id,
                            'check_in': reservation.checkin,
                            'check_out': reservation.checkout,
                            'state': 'assigned',
                            'reservation_id': reservation.id,
                            }
                        # room_id.write({'isroom': False, 'status': 'occupied'})
                        reservation_line_obj.create(vals)
        return True

    @api.multi
    def cancel_reservation(self):
        """
        This method cancel recordset for hotel room reservation line
        ------------------------------------------------------------------
        @param self: The object pointer
        @return: cancel record set for hotel room reservation line.
        """
        room_res_line_obj = self.env['hotel.room.reservation.line']
        hotel_res_line_obj = self.env['hotel_reservation.line']
        self.state = 'cancel'
        room_reservation_line = room_res_line_obj.search([('reservation_id',
                                                           'in', self.ids)])
        room_reservation_line.write({'state': 'unassigned'})
        reservation_lines = hotel_res_line_obj.search([('line_id',
                                                        'in', self.ids)])
        # for reservation_line in reservation_lines:
        #     reservation_line.reserve.write({'isroom': True,
        #                                     'status': 'available'})
        return True

    @api.multi
    def send_reservation_maill(self):
        '''
        This function opens a window to compose an email,
        template message loaded by default.
        @param self: object pointer
        '''
        assert len(self._ids) == 1, 'This is for a single id at a time.'
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = (ir_model_data.get_object_reference
                           ('hotel_reservation',
                            'mail_template_hotel_reservation3')[1])
        except ValueError:
            template_id = False
        try:
            compose_form_id = (ir_model_data.get_object_reference
                               ('mail',
                                'email_compose_message_wizard_form')[1])
        except ValueError:
            compose_form_id = False
        ctx = dict()
        ctx.update({
            'default_model': 'hotel.reservation',
            'default_res_id': self._ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'force_send': True,
            'mark_so_as_sent': True
        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
            'force_send': True
        }

    @api.model
    def reservation_reminder_24hrs(self):
        """
        This method is for scheduler
        every 1day scheduler will call this method to
        find all tomorrow's reservations.
        ----------------------------------------------
        @param self: The object pointer
        @return: send a mail
        """
        now_str = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        now_date = datetime.datetime.strptime(now_str,
                                              DEFAULT_SERVER_DATETIME_FORMAT)
        ir_model_data = self.env['ir.model.data']
        template_id = (ir_model_data.get_object_reference
                       ('hotel_reservation',
                        'mail_template_reservation_reminder_24hrs')[1])
        template_rec = self.env['mail.template'].browse(template_id)
        for travel_rec in self.search([]):
            checkin_date = (datetime.datetime.strptime
                            (travel_rec.checkin,
                             DEFAULT_SERVER_DATETIME_FORMAT))
            difference = relativedelta(now_date, checkin_date)
            if(difference.days == -1 and travel_rec.partner_id.email and
               travel_rec.state == 'confirm'):
                template_rec.send_mail(travel_rec.id, force_send=True)
        return True

    @api.multi
    def set_to_draft_reservation(self):
        self.state = 'draft'
        return True

    @api.multi
    def _create_folio(self):
        """
        This method is for create new hotel folio.
        -----------------------------------------
        @param self: The object pointer
        @return: new record set for hotel folio.
        """
        hotel_folio_obj = self.env['hotel.folio']
        room_obj = self.env['hotel.room']
        for reservation in self:
            folio_lines = []
            checkin_date = reservation['checkin']
            checkout_date = reservation['checkout']
            if not self.checkin < self.checkout:
                raise ValidationError(_('Checkout date should be greater \
                                 than the Checkin date.'))
            duration_vals = (self.onchange_check_dates
                             (checkin_date=checkin_date,
                              checkout_date=checkout_date, duration=False))
            duration = duration_vals.get('duration') or 0.0
            folio_vals = {
                'date_order': reservation.date_order,
                'warehouse_id': reservation.warehouse_id.id,
                'partner_id': reservation.partner_id.id,
                'pricelist_id': reservation.pricelist_id.id,
                'partner_invoice_id': reservation.partner_invoice_id.id,
                'partner_shipping_id': reservation.partner_shipping_id.id,
                'checkin_date': reservation.checkin,
                'checkout_date': reservation.checkout,
                'duration': duration,
                'reservation_id': reservation.id,
                'service_lines': reservation['folio_id'],
                'observations': reservation.observations,
            }
            calculate_check = False
            if reservation.checkin_hour < 12:
                folio_vals['early_checkin'] = True
                folio_vals['early_checkin_hour'] = reservation.checkin_hour
                calculate_check = True
            if reservation.checkout_hour > 10:
                folio_vals['late_checkout'] = True
                folio_vals['late_checkout_hour'] = reservation.checkout_hour
                calculate_check = True
            date_a = (datetime.datetime
                      (*time.strptime(reservation['checkout'],
                                      DEFAULT_SERVER_DATETIME_FORMAT)[:5]))
            date_b = (datetime.datetime
                      (*time.strptime(reservation['checkin'],
                                      DEFAULT_SERVER_DATETIME_FORMAT)[:5]))
            for line in reservation.reservation_line:
                taxed_price = line.list_price
                for r in line.reserve:
                    prod = r.with_context(partner=reservation.partner_id.id,
                                          quantity=1,
                                          date_order=reservation.checkin,
                                          pricelist=reservation.
                                          pricelist_id.id,
                                          uom=r['uom_id'].id
                                          )
                    room_type_obj = self.env['hotel.room.type']
                    room_type_ids = room_type_obj.search([('cat_id', '=', prod.categ_id.id)])
                    if line.list_price and reservation.tax_id:
                        taxed_price += (line.list_price * reservation.tax_id.amount) / 100
                    if reservation.dolar_rate:
                        taxed_price = taxed_price * reservation.dolar_rate
                    folio_lines.append((0, 0, {
                        'checkin_date': checkin_date,
                        'checkout_date': checkout_date,
                        'product_id': r.product_id and r.product_id.id,
                        'name': reservation['reservation_no'],
                        'product_uom': r['uom_id'].id,
                        'price_unit': line.list_price == 0 and room_type_ids.read(fields=['list_price'])[0]['list_price'] or taxed_price,
                        # 'categ_id' : room_type_ids and room_type_ids[0].id,
                        'product_uom_qty': ((date_a - date_b).days) + 1,
                        'discount_id': reservation.partner_id.discount_id and reservation.partner_id.discount_id.id,
                        'discount' : reservation.partner_id.discount_id and reservation.partner_id.discount_id.discount,
                    }))
                    res_obj = room_obj.browse([r.id])
                    res_obj.write({'status': 'occupied', 'isroom': False})
            folio_vals.update({'room_lines': folio_lines})
            folio = hotel_folio_obj.create(folio_vals)
            ## confirmo el folio...
            folio.action_confirm()
            ## escribo bb_id
            if calculate_check:
                folio.calculate_check()
            if reservation.payment_lines:
              for payment in reservation.payment_lines:
                payment.folio_id = folio
            self._cr.execute('insert into hotel_folio_reservation_rel'
                             '(order_id, invoice_id) values (%s,%s)',
                             (reservation.id, folio.id)
                             )
            reservation.write({'state': 'done'})
        return folio.action_view_folio()
        # return True

    @api.multi
    def onchange_check_dates(self, checkin_date=False, checkout_date=False,
                             duration=False):
        '''
        This mathod gives the duration between check in checkout if
        customer will leave only for some hour it would be considers
        as a whole day. If customer will checkin checkout for more or equal
        hours, which configured in company as additional hours than it would
        be consider as full days
        --------------------------------------------------------------------
        @param self: object pointer
        @return: Duration and checkout_date
        '''
        value = {}
        company_obj = self.env['res.company']
        configured_addition_hours = 0
        company_ids = company_obj.search([])
        if company_ids.ids:
            configured_addition_hours = company_ids[0].additional_hours
        duration = 0
        if checkin_date and checkout_date:
            chkin_dt = (datetime.datetime.strptime
                        (checkin_date, DEFAULT_SERVER_DATETIME_FORMAT))
            chkout_dt = (datetime.datetime.strptime
                         (checkout_date, DEFAULT_SERVER_DATETIME_FORMAT))
            dur = chkout_dt - chkin_dt
            duration = dur.days + 1
            if configured_addition_hours > 0:
                additional_hours = abs((dur.seconds / 60) / 60)
                if additional_hours >= configured_addition_hours:
                    duration += 1
        value.update({'duration': duration})
        return value

    @api.model
    def create(self, vals):
        """
        Overrides orm create method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        """
        if not vals:
            vals = {}
        if self._context is None:
            self._context = {}
        seq_obj = self.env['ir.sequence']
        hotel_reserve = seq_obj.next_by_code('hotel.reservation') or 'New'
        vals['reservation_no'] = hotel_reserve
        return super(HotelReservation, self).create(vals)

    @api.multi
    def copy(self, default=None):
        '''
        @param self: object pointer
        @param default: dict of default values to be set
        '''
        default['folio_id'] = False
        return super(HotelReservation, self).copy(default=default)


class HotelReservationLine(models.Model):

    _name = "hotel_reservation.line"
    _description = "Reservation Line"

    @api.multi
    def copy(self, default=None):
        '''
        @param self: object pointer
        @param default: dict of default values to be set
        '''
        return super(HotelReservationLine, self).copy(default=default)

    @api.model
    def get_categ(self):
        if 'default_adults' in self._context.keys() and 'default_children' in self._context.keys():
            pax = self._context['default_adults'] + self._context['default_children']
            hotel_room_type_obj = self.env['hotel.room.type']
            type_id = hotel_room_type_obj.search([('capacity','=',pax)])
            if type_id:
                if len(type_id)>1:
                    type_id = type_id[0]
                return type_id.id

    name = fields.Char('Name', size=64)
    line_id = fields.Many2one('hotel.reservation')
    reserve = fields.Many2many('hotel.room',
                               'hotel_reservation_line_room_rel',
                               'room_id', 'hotel_reservation_line_id',
                               domain="[('categ_id','=',categ_id)]")
    categ_id = fields.Many2one('hotel.room.type', 'Room Type',
                               domain="[('isroomtype','=',True)]",
                               default=get_categ)
    list_price = fields.Float('Precio Opcional', digits_compute=dp.get_precision('Product Price'))



    @api.onchange('categ_id')
    def on_change_categ(self):
        '''
        When you change categ_id it check checkin and checkout are
        filled or not if not then raise warning
        -----------------------------------------------------------
        @param self: object pointer
        '''
        hotel_room_obj = self.env['hotel.room']
        reservation_line_obj = self.env['hotel.room.reservation.line']
        if self.categ_id.cat_id.id:
          hotel_room_ids = hotel_room_obj.search([('categ_id', '=',
                                                  self.categ_id.cat_id.id)])
        else:
          hotel_room_ids = hotel_room_obj.search([])
        assigned = False
        room_ids = []
        if not self.line_id.checkin:
            raise ValidationError(_('Before choosing a room,\n You have to select \
                             a Check in date or a Check out date in \
                             the reservation form.'))
        for room in hotel_room_ids:
            assigned = False
            reservline_ids = [i.ids for i in
                              room.room_reservation_line_ids]
            reservline_ids = (reservation_line_obj.search
                              ([('id', 'in', reservline_ids),
                                ('state','=','assigned'),
                                ('status','<>','cancel'),
                                ]))
            for line in reservline_ids:
                if(line.check_in >= self.line_id.checkin and
                   line.check_in <= self.line_id.checkout or
                   line.check_out <= self.line_id.checkout and
                   line.check_out >= self.line_id.checkin) or (line.check_in <= self.line_id.checkin and line.check_out >= self.line_id.checkout):
                    assigned = True
            if not assigned:
                room_ids.append(room.id)
        domain = {'reserve': [('id', 'in', room_ids)]}
        return {'domain': domain}

    @api.multi
    def unlink(self):
        """
        Overrides orm unlink method.
        @param self: The object pointer
        @return: True/False.
        """
        hotel_room_reserv_line_obj = self.env['hotel.room.reservation.line']
        for reserv_rec in self:
            for rec in reserv_rec.reserve:
                hres_arg = [('room_id', '=', rec.id),
                            ('reservation_id', '=', reserv_rec.line_id.id)]
                myobj = hotel_room_reserv_line_obj.search(hres_arg)
                if myobj.ids:
                    # rec.write({'isroom': True, 'status': 'available'})
                    myobj.unlink()
        return super(HotelReservationLine, self).unlink()


class HotelRoomReservationLine(models.Model):

    _name = 'hotel.room.reservation.line'
    _description = 'Hotel Room Reservation'
    _rec_name = 'room_id'

    room_id = fields.Many2one(comodel_name='hotel.room', string='Room id')
    check_in = fields.Datetime('Check In Date', required=True)
    check_out = fields.Datetime('Check Out Date', required=True)
    state = fields.Selection([('assigned', 'Assigned'),
                              ('unassigned', 'Unassigned')], 'Room Status')
    reservation_id = fields.Many2one('hotel.reservation',
                                     string='Reservation')
    status = fields.Selection(string='state', related='reservation_id.state')


class HotelRoom(models.Model):

    _inherit = 'hotel.room'
    _description = 'Hotel Room'

    room_reservation_line_ids = fields.One2many('hotel.room.reservation.line',
                                                'room_id',
                                                string='Room Reserv Line')

    @api.model
    def cron_room_line(self):
        """
        This method is for scheduler
        every 1min scheduler will call this method and check Status of
        room is occupied or available
        --------------------------------------------------------------
        @param self: The object pointer
        @return: update status of hotel room reservation line
        """
        reservation_line_obj = self.env['hotel.room.reservation.line']
        folio_room_line_obj = self.env['folio.room.line']
        now = datetime.datetime.now()
        curr_date = now.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        for room in self.search([]):
            sql = """select rl.id from hotel_room_reservation_line rl
                                inner join hotel_reservation r on (rl.reservation_id=r.id)
                                where rl.id in (%s)
                                and check_in <= '%s'
                                and check_out >= '%s'
                                and r.state not in ('cancel','done')
                                and rl.state not in ('unassigned')"""%(\
                                  ','.join(str(x) for x in room.room_reservation_line_ids.ids), \
                                  curr_date, curr_date)
            self._cr.execute(sql)
            line_ids = self._cr.fetchone()
            reservation_line_ids = reservation_line_obj.browse(line_ids)
            rooms_ids = [room_line.ids for room_line in room.room_line_ids]
            rom_args = [('id', 'in', rooms_ids),
                        ('check_in', '<=', curr_date),
                        ('check_out', '>=', curr_date),
                        ('status', '<>', 'cancel')]
            room_line_ids = folio_room_line_obj.search(rom_args)
            if room.status == 'blocked':
                continue
            status = {'isroom': True, 'color': 5, 'status': 'available'}
            if reservation_line_ids.ids:
                status = {'isroom': False, 'color': 2, 'status': 'occupied'}
            room.write(status)
            if room_line_ids.ids:
                status = {'isroom': False, 'color': 2, 'status': 'occupied'}
            room.write(status)
            # if reservation_line_ids.ids and room_line_ids.ids:
            #     raise ValidationError(_('Please Check Rooms Status \
            #                      for %s.' % (room.name)))
        return True


class RoomReservationSummary(models.Model):

    _name = 'room.reservation.summary'
    _description = 'Room reservation summary'

    date_from = fields.Datetime('Date From')
    date_to = fields.Datetime('Date To')
    summary_header = fields.Text('Summary Header')
    room_summary = fields.Text('Room Summary')
    categ_id = fields.Many2one('hotel.room.type', 'Room Type',
                               domain="[('isroomtype','=',True)]")
    # month = fields.Selection([(1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'), (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'),
    #                           (8, 'Agosto'), (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')],'Mes',
    #                           default=lambda *a: time.gmtime()[1])
    # year = fields.Integer('Año', default=lambda *a: time.gmtime()[0])

    @api.model
    def default_get(self, fields):
        """
        To get default values for the object.
        @param self: The object pointer.
        @param fields: List of fields for which we want default values
        @return: A dictionary which of fields with values.
        """
        if self._context is None:
            self._context = {}
        res = super(RoomReservationSummary, self).default_get(fields)
        if not self.date_from and not self.date_to:
            date_today = datetime.datetime.today()
            first_day = datetime.datetime(date_today.year,
                                          date_today.month, 1, 0, 0, 0)
            first_temp_day = first_day + relativedelta(months=1)
            last_temp_day = first_temp_day - relativedelta(days=1)
            last_day = datetime.datetime(last_temp_day.year,
                                         last_temp_day.month,
                                         last_temp_day.day, 23, 59, 59)
            date_froms = date_today.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            to_date = date_today + timedelta(days=6)
            date_ends = to_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            res.update({'date_from': date_froms, 'date_to': date_ends})
        return res

    @api.multi
    def room_reservation(self):
        '''
        @param self: object pointer
        '''
        mod_obj = self.env['ir.model.data']
        if self._context is None:
            self._context = {}
        model_data_ids = mod_obj.search([('model', '=', 'ir.ui.view'),
                                         ('name', '=',
                                          'view_hotel_reservation_form')])
        resource_id = model_data_ids.read(fields=['res_id'])[0]['res_id']
        return {'name': _('Reconcile Write-Off'),
                'context': self._context,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'hotel.reservation',
                'views': [(resource_id, 'form')],
                'type': 'ir.actions.act_window',
                'target': 'new',
                }

    def replace_char(self, output):
        output = (output.encode('utf-8')).replace('°','.')
        output = output.replace('Ñ','N')
        output = output.replace('ñ','n')
        output = output.replace('á','a')
        output = output.replace('é','e')
        output = output.replace('í','i')
        output = output.replace('ó','o')
        output = output.replace('ú','u')
        output = output.replace('Á','A')
        output = output.replace('É','E')
        output = output.replace('Í','I')
        output = output.replace('Ó','O')
        output = output.replace('Ú','U')
        return output

    def check_reservation(self, cat_id, date_from, date_to):
        '''
        @param self: object pointer
         '''
        res = {}
        all_detail = []
        room_obj = self.env['hotel.room']
        date_range_list = []
        main_header = []
        summary_header_list = ['Habitaciones']
        if date_from and date_to:
            if date_from > date_to:
                raise ValidationError(_('Please Check Time period Date \
                                 From can\'t be greater than Date To !'))
            d_frm_obj = (datetime.datetime.strptime
                         (date_from, DEFAULT_SERVER_DATETIME_FORMAT))
            d_to_obj = (datetime.datetime.strptime
                        (date_to, DEFAULT_SERVER_DATETIME_FORMAT))
            temp_date = d_frm_obj
            while temp_date <= d_to_obj:
                val = ''
                val = (str(temp_date.strftime("%a")) + ' ' +
                       str(temp_date.strftime("%b")) + ' ' +
                       str(temp_date.strftime("%d")))
                val = self.replace_char(val)
                summary_header_list.append(val)
                date_range_list.append(temp_date.strftime
                                       (DEFAULT_SERVER_DATETIME_FORMAT))
                temp_date = temp_date + datetime.timedelta(days=1)
            all_detail.append(summary_header_list)
            if cat_id:
                room_ids = room_obj.search([('categ_id', 'in', cat_id)])
            else:
                room_ids = room_obj.search([], order="sequence")
            all_room_detail = []
            for room in room_ids:
                price = room.price
                room_detail = {}
                room_list_stats = []
                room_detail.update({'name': "%s (%s)"%(room.name, room.categ_id.name[0:13]) or ''})
                room_detail.update({'categ_id': room.categ_id.id or False})
                # habitacion bloqueada
                if room.status == 'blocked':
                    for chk_date in date_range_list:
                        room_list_stats.append({'state': 'Bloqueado',
                                                'date': chk_date,
                                                'room_id': room.id})
                    room_detail.update({'value': room_list_stats})
                    all_room_detail.append(room_detail)
                    continue
                if not room.room_reservation_line_ids and not room.room_line_ids:
                    for chk_date in date_range_list:
                        room_list_stats.append({'state': 'Libre',
                                                'date': chk_date,
                                                'room_id': room.id})
                else:
                    for chk_date in date_range_list:
                        chk_date2 = (datetime.datetime.strptime
                                     (chk_date, DEFAULT_SERVER_DATETIME_FORMAT))

                        chk_date = chk_date[0:10]
                        ocupado = False
                        reservado = False
                        late_checkout = False
                        early_checkin = False
                        self._cr.execute("""SELECT f.id
                                                FROM "folio_room_line"
                                                join hotel_folio f on (folio_room_line.folio_id=f.id)
                                                join sale_order s on (f.order_id=s.id)
                                                WHERE (((("folio_room_line"."room_id" = %s)
                                                AND  ("folio_room_line"."check_in" <= '%s  23:59:59'))
                                                AND  ("folio_room_line"."check_out" > '%s 23:59:59'))
                                                and s.state not in ('cancel','draft')
                                                ) ORDER BY "folio_room_line"."id"
                          """%(room.id, chk_date, chk_date))
                        folline_ids = self._cr.fetchone()
                        if folline_ids:
                            room_list_stats.append({'state': 'Ocupado',
                                                    'room_id': room.id,
                                                    'date': chk_date,
                                                    'res_id': folline_ids[0]
                                                   })
                            ocupado = True

                        if not ocupado:
                            self._cr.execute("""SELECT r.id
                                                FROM "hotel_room_reservation_line"
                                                join hotel_reservation r on ("hotel_room_reservation_line".reservation_id=r.id)
                                                WHERE ((((("hotel_room_reservation_line"."room_id" = %s)
                                                AND  ("hotel_room_reservation_line"."check_in" <= '%s  23:59:59'))
                                                AND  ("hotel_room_reservation_line"."check_out" > '%s  23:59:59'))
                                                AND  ("hotel_room_reservation_line"."state" = 'assigned'))
                                                and r.state != 'cancel'
                                                ) ORDER BY "hotel_room_reservation_line"."id"
                              """%(room.id, chk_date, chk_date))
                            reservline_ids = self._cr.fetchone()
                            if reservline_ids:
                                room_list_stats.append({'state': 'Reservado',
                                                        'date': chk_date,
                                                        'room_id': room.id,
                                                        'res_id': reservline_ids[0]
                                                       })
                                reservado = True
                        if not ocupado and not reservado:
                            pre_date = chk_date2.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                            self._cr.execute("""SELECT "folio_room_line".id
                                                FROM "folio_room_line"
                                                join hotel_folio f on (folio_room_line.folio_id=f.id)
                                                join sale_order s on (f.order_id=s.id)
                                                WHERE ((((("folio_room_line"."room_id" = %s)
                                                AND  ("folio_room_line"."check_in" <= '%s 23:59:59'))
                                                AND  ("folio_room_line"."check_out" > '%s 15:00:00'))
                                                AND  ("folio_room_line"."check_out" <= '%s 23:59:59'))
                                                and s.state not in ('cancel','draft')
                                                ) ORDER BY "folio_room_line"."id"
                              """%(room.id, pre_date[0:10], pre_date[0:10], pre_date[0:10]))
                            folline_ids = self._cr.fetchone()
                            self._cr.execute("""SELECT "hotel_room_reservation_line".id
                                                FROM "hotel_room_reservation_line"
                                                join hotel_reservation r on ("hotel_room_reservation_line".reservation_id=r.id)
                                                WHERE (((((("hotel_room_reservation_line"."room_id" = %s)
                                                AND  ("hotel_room_reservation_line"."check_in" <= '%s'))
                                                AND  ("hotel_room_reservation_line"."check_out" > '%s 15:00:00'))
                                                AND  ("hotel_room_reservation_line"."check_out" <= '%s 23:59:59'))
                                                AND  ("hotel_room_reservation_line"."state" = 'assigned'))
                                                and r.state != 'cancel'
                                                ) ORDER BY "hotel_room_reservation_line"."id"
                              """%(room.id, pre_date[0:10], pre_date[0:10], pre_date[0:10]))
                            reservline_ids = self._cr.fetchone()
                            if reservline_ids or folline_ids:
                                room_list_stats.append({'state': 'Late Checkout',
                                                        'date': chk_date,
                                                        'room_id': room.id})
                                late_checkout = True
                        # if not ocupado and not reservado and not late_checkout:
                        #     temp_date = chk_date2 + datetime.timedelta(days=1)
                        #     pre_date = temp_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                        #     reservline_ids = (reservation_line_obj.search
                        #                       ([('id', 'in', reservline_idss),
                        #                         ('check_out', '>=', pre_date[0:10]),
                        #                         ('check_in', '<', "%s %s"%(pre_date[0:10], '13:00:00')),
                        #                         ('check_in', '>=', "%s %s"%(pre_date[0:10], '00:00:00')),
                        #                         ('state','=','assigned'),
                        #                         ('status','<>','cancel'),
                        #                         # ('status','not in',['cancel','done']),
                        #                         ]))
                        #     folline_ids = (folio_line_obj.search
                        #                   ([('id', 'in', folline_idss),
                        #                     ('check_out', '>=', pre_date[0:10]),
                        #                     ('check_in', '<', "%s %s"%(pre_date[0:10], '13:00:00')),
                        #                     ('check_in', '>=', "%s %s"%(pre_date[0:10], '00:00:00')),
                        #                     ('status', 'not in', ['cancel','draft'])
                        #                     ]))
                        #     if reservline_ids or folline_ids:
                        #         room_list_stats.append({'state': 'Early Checkin',
                        #                                 'date': chk_date,
                        #                                 'room_id': room.id})
                        #         early_checkin = True

                        if not ocupado and not reservado and not late_checkout and not early_checkin :
                            room_list_stats.append({'state': 'Libre',
                                                    'date': chk_date,
                                                    'room_id': room.id,
                                                    'tooltip': 'Precio: $%s'%(price),
                                                   })
                room_detail.update({'value': room_list_stats})
                all_room_detail.append(room_detail)
            main_header.append({'header': summary_header_list})
            res = {
                'summary_header': main_header,
                'room_summary': all_room_detail,
            }
        return res

    def get_tooltip(self, state, res_id):
        if state == 'Ocupado':
            sql = """select f.name || ' - ' || p.name || ' ' || duration || ' noche(s) desde ' ||
                        substring(checkin_date::text,0,11) || ' hasta ' || substring(checkout_date::text,0,11) || ' ' ||
                        coalesce(f.observations,'')
                        from hotel_folio f
                        join sale_order s on (f.order_id=s.id)
                        join res_partner p on (s.partner_id=p.id)
                        where f.id = %s"""%res_id
        else:
            sql = """select reservation_no || ' - ' || p.name || ' desde ' || checkin_date || '
                        hasta ' || checkout_date || ' ' || coalesce(r.observations,'')
                        from hotel_reservation r
                        join res_partner p on (r.partner_id=p.id)
                        where r.id = %s"""%res_id
        self._cr.execute(sql)
        ress = self._cr.fetchone()
        return ress[0]

    @api.onchange('date_from', 'date_to', 'categ_id')
    def get_room_summary(self):
        '''
        @param self: object pointer
         '''
        ahora = time.time()
        cat_id = self.categ_id and [self.categ_id.cat_id.id] or False
        res = self.check_reservation(cat_id, self.date_from, self.date_to)
        for room in res['room_summary']:
            for value in room['value']:
                if value['state'] in ['Ocupado', 'Reservado']:
                    value['tooltip'] = self.get_tooltip(value['state'], value['res_id'])
        self.summary_header = str(res['summary_header'])
        self.room_summary = str(res['room_summary'])
        LOGGER.info("--- %s seconds ---" % (time.time() - ahora))
        return {}


class QuickRoomReservation(models.TransientModel):
    _name = 'quick.room.reservation'
    _description = 'Quick Room Reservation'

    partner_id = fields.Many2one('res.partner', string="Customer",
                                 required=True)
    check_in = fields.Datetime('Check In', required=False)
    check_out = fields.Datetime('Check Out', required=False)
    room_id = fields.Many2one('hotel.room', 'Room', required=True)
    warehouse_id = fields.Many2one('stock.warehouse', 'Hotel', required=True,default=1)
    pricelist_id = fields.Many2one('product.pricelist', 'pricelist',
                                   required=True)
    partner_invoice_id = fields.Many2one('res.partner', 'Invoice Address',
                                         required=True)
    partner_order_id = fields.Many2one('res.partner', 'Ordering Contact',
                                       required=True)
    partner_shipping_id = fields.Many2one('res.partner', 'Delivery Address',
                                          required=True)
    #------
    checkin_date = fields.Date('Entrada', required=True)
    checkout_date = fields.Date('Salida', required=True)
    checkin_hour = fields.Integer('Hora Entrada', required=True,default=lambda *a: 12)
    checkout_hour = fields.Integer('Hora Salida', required=True,default=lambda *a: 10)
    list_price = fields.Float('Precio Opcional', digits_compute=dp.get_precision('Product Price'))
    observations = fields.Text('Observaciones')
    #------

    @api.onchange('check_out', 'check_in')
    def on_change_check_out(self):
        '''
        When you change checkout or checkin it will check whether
        Checkout date should be greater than Checkin date
        and update dummy field
        -----------------------------------------------------------
        @param self: object pointer
        @return: raise warning depending on the validation
        '''
        if self.check_out and self.check_in:
            if self.check_out < self.check_in:
                raise ValidationError(_('Checkout date should be greater \
                                 than Checkin date.'))

    @api.onchange('partner_id')
    def onchange_partner_id_res(self):
        '''
        When you change partner_id it will update the partner_invoice_id,
        partner_shipping_id and pricelist_id of the hotel reservation as well
        ---------------------------------------------------------------------
        @param self: object pointer
        '''
        if not self.partner_id:
            self.partner_invoice_id = False
            self.partner_shipping_id = False
            self.partner_order_id = False
        else:
            addr = self.partner_id.address_get(['delivery', 'invoice',
                                                'contact'])
            self.partner_invoice_id = addr['invoice']
            self.partner_order_id = addr['contact']
            self.partner_shipping_id = addr['delivery']
            self.pricelist_id = self.partner_id.property_product_pricelist.id

    @api.model
    def default_get(self, fields):
        """
        To get default values for the object.
        @param self: The object pointer.
        @param fields: List of fields for which we want default values
        @return: A dictionary which of fields with values.
        """
        if self._context is None:
            self._context = {}
        res = super(QuickRoomReservation, self).default_get(fields)
        if self._context:
            keys = self._context.keys()
            if 'date' in keys:
                date_out = datetime.datetime.strptime(self._context['date'][0:10], '%Y-%m-%d') + datetime.timedelta(days=1)
                res.update({
                    'check_in': self._context['date'],
                    'checkin_date': self._context['date'][0:10],
                    'checkout_date': str(date_out)[0:10],
                })
            if 'room_id' in keys:
                roomid = self._context['room_id']
                res.update({'room_id': int(roomid)})
        return res

    @api.multi
    def room_reserve(self):
        """
        This method create a new record for hotel.reservation
        -----------------------------------------------------
        @param self: The object pointer
        @return: new record set for hotel reservation.
        """
        hotel_res_obj = self.env['hotel.reservation']
        for res in self:
            if not res.checkin_hour >=0 or not res.checkin_hour <= 24:
                raise ValidationError(_('Seleccione una hora de entrada entre las 0 y las 23.'))
            if not res.checkout_hour >=0 or not res.checkout_hour <= 24:
                raise ValidationError(_('Seleccione una hora de salida entre las 0 y las 23.'))
            date_order = time.strftime('%Y-%m-%d')
            if res.checkin_date < date_order:
               raise except_orm(_('Warning'), _('La fecha de entrada debe ser \
               mayor o igual que la fecha del día.'))
            reservation = {'partner_id': res.partner_id.id,
               'partner_invoice_id': res.partner_invoice_id.id,
               'partner_order_id': res.partner_order_id.id,
               'partner_shipping_id': res.partner_shipping_id.id,
               'checkin' : '%s %s:00:00'%(res.checkin_date, res.checkin_hour+3),
               'checkout' : '%s %s:00:00'%(res.checkout_date, res.checkout_hour+3),
               'checkin_date': res.checkin_date,
               'checkin_hour': res.checkin_hour,
               'checkout_date': res.checkout_date,
               'checkout_hour': res.checkout_hour,
               'warehouse_id': res.warehouse_id.id,
               'pricelist_id': res.pricelist_id.id,
               'reservation_line': [(0, 0,
                                     {'reserve': [(6, 0, [res.room_id.id])],
                                      'name': (res.room_id and
                                               res.room_id.name or ''),
                                      'list_price': res.list_price and res.list_price or False,
                                      })],
               'observations': res.observations,
               }
            reservation_id = hotel_res_obj.create(reservation)
            workflow.trg_validate(self._uid, 'hotel.reservation', reservation_id.id,
                                      'confirm', self._cr)
        return True

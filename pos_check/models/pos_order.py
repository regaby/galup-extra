# -*- coding: utf-8 -*-
from openerp import models, fields
from openerp.tools import float_is_zero
from openerp.exceptions import UserError, ValidationError
import time
from openerp.tools.translate import _

class PosOrder(models.Model):
    _inherit = "pos.order"

    def _payment_fields(self, cr, uid, ui_paymentline, context=None):
        res = super(PosOrder, self)._payment_fields(cr, uid, ui_paymentline, context)
        res.update({
            'check_bank_id': ui_paymentline.get('check_bank_id'),
            'check_bank_acc': ui_paymentline.get('check_bank_acc'),
            'check_number': ui_paymentline.get('check_number'),
            'check_owner': ui_paymentline.get('check_owner'),
            'check_owner_vat': ui_paymentline.get('check_owner_vat'),
            'check_pay_date': ui_paymentline.get('check_pay_date'),
            'check_cbu': ui_paymentline.get('check_cbu'),
            'reference': ui_paymentline.get('reference'),
        })
        return res

    def _add_operation(
            self, cr, uid, check_id, operation, partner=None, date=False):
        for rec in check_id:
            rec._check_state_change(operation)
            # agregamos validacion de fechas
            date = date or fields.Datetime.now()
            if rec.operation_ids and rec.operation_ids[0].date > date:
                raise ValidationError(_(
                    'The date of a new check operation can not be minor than '
                    'last operation date.\n'
                    '* Check Id: %s\n'
                    '* Check Number: %s\n'
                    '* Operation: %s\n'
                    '* Operation Date: %s\n'
                    '* Last Operation Date: %s') % (
                    rec.id, rec.name, operation, date,
                    rec.operation_ids[0].date))
            vals = {
                'operation': operation,
                'date': date,
                'check_id': rec.id,
                'partner_id': partner and partner.id or False,
            }
            rec.operation_ids.create(vals)

    def add_payment(self, cr, uid, order_id, data, context=None):
        statement_id = super(PosOrder, self).add_payment(cr, uid, order_id, data, context)
        StatementLine = self.pool.get('account.bank.statement.line')
        checkObj = self.pool.get('account.check')
        journalObj = self.pool.get('account.journal')
        statement_lines = StatementLine.search(cr, uid, [
            ('statement_id', '=', statement_id),
            ('pos_statement_id', '=', order_id),
            ('journal_id', '=', data['journal']),
            ('amount', '=', data['amount'])
        ])
        partner = StatementLine.browse(cr, uid, statement_lines).partner_id
        journal = journalObj.browse(cr, uid, data['journal'])
        if 'check_number' in data.keys() and data['check_number'] and journal.is_check:
            print '\n\n\ncreando cheque'
            check = {
                'name' : data['check_number'],
                'bank_id': data['check_bank_id'],
                'journal_id': data['journal'],
                'number': data['check_number'],
                'amount': data['amount'],
                'owner_name': data['check_owner'],
                'owner_vat':  data['check_owner_vat'],
                'issue_date': data['payment_date'][0:10],
                'payment_date': data['check_pay_date'],
                'type': 'third_check',
                'partner_id': partner and partner.id or False,
            }
            check_id = checkObj.create(cr, uid, check,context)
            check_id = checkObj.browse(cr, uid, check_id)
            self._add_operation(cr, uid, check_id, 'holding', partner, data['check_pay_date'])
        else:
            print '\n\n\nno es cheque'
        for line in StatementLine.browse(cr, uid, statement_lines):
            if line.journal_id.check_info_required and not line.check_bank_id:
                check_bank_id = data.get('check_bank_id')
                if isinstance(check_bank_id, (tuple, list)):
                    check_bank_id = check_bank_id[0]

                check_vals = {
                    'check_bank_id': check_bank_id,
                    'check_bank_acc': data.get('check_bank_acc'),
                    'check_number': data.get('check_number') and data.get('check_number') or '-',
                    'check_owner': data.get('check_owner'),
                    'check_owner_vat': data.get('check_owner_vat'),
                    'check_pay_date': data.get('check_pay_date'),
                    'check_cbu': data.get('check_cbu'),
                    'reference': data.get('reference') and data.get('reference') or '-',
                }
                line.write(check_vals)
                break

        return statement_id

    def _process_order(self, cr, uid, order, context=None):
        """
            Heredo este método para corregir referencia en pago negativo (retirar dinero)
        """
        prec_acc = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')
        session = self.pool.get('pos.session').browse(cr, uid, order['pos_session_id'], context=context)

        if session.state == 'closing_control' or session.state == 'closed':
            session_id = self._get_valid_session(cr, uid, order, context=context)
            session = self.pool.get('pos.session').browse(cr, uid, session_id, context=context)
            order['pos_session_id'] = session_id

        order_id = self.create(cr, uid, self._order_fields(cr, uid, order, context=context),context)
        journal_ids = set()
        v_payment = False
        for payments in order['statement_ids']:
            if not float_is_zero(payments[2]['amount'], precision_digits=prec_acc):
                self.add_payment(cr, uid, order_id, self._payment_fields(cr, uid, payments[2], context=context), context=context)
                v_payment = payments[2]
            else:
                v_payment = payments[2]
            journal_ids.add(payments[2]['journal_id'])

        if session.sequence_number <= order['sequence_number']:
            session.write({'sequence_number': order['sequence_number'] + 1})
            session.refresh()

        if not float_is_zero(order['amount_return'], precision_digits=prec_acc):
            cash_journal = session.cash_journal_id.id
            if not cash_journal:
                # Select for change one of the cash journals used in this payment
                cash_journal_ids = self.pool['account.journal'].search(cr, uid, [
                    ('type', '=', 'cash'),
                    ('id', 'in', list(journal_ids)),
                ], limit=1, context=context)
                if not cash_journal_ids:
                    # If none, select for change one of the cash journals of the POS
                    # This is used for example when a customer pays by credit card
                    # an amount higher than total amount of the order and gets cash back
                    cash_journal_ids = [statement.journal_id.id for statement in session.statement_ids
                                        if statement.journal_id.type == 'cash']
                    if not cash_journal_ids:
                        raise UserError(_("No cash statement found for this session. Unable to record returned cash."))
                cash_journal = cash_journal_ids[0]
            v_dicc = self._payment_fields(cr, uid, v_payment, context=context)
            v_dicc.update({'amount': -order['amount_return'],
                'payment_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'payment_name': _('return'),
                'journal': cash_journal,
            })
            self.add_payment(cr, uid, order_id, v_dicc, context=context)

        return order_id

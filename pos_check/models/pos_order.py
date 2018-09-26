# -*- coding: utf-8 -*-
from openerp import models, fields

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
        }
        check_id = checkObj.create(cr, uid, check,context)
        check_id = checkObj.browse(cr, uid, check_id)
        self._add_operation(cr, uid, check_id, 'holding', False, data['check_pay_date'])
        statement_lines = StatementLine.search(cr, uid, [
            ('statement_id', '=', statement_id),
            ('pos_statement_id', '=', order_id),
            ('journal_id', '=', data['journal']),
            ('amount', '=', data['amount'])
        ])
        for line in StatementLine.browse(cr, uid, statement_lines):
            if line.journal_id.check_info_required and not line.check_bank_id:
                check_bank_id = data.get('check_bank_id')
                if isinstance(check_bank_id, (tuple, list)):
                    check_bank_id = check_bank_id[0]

                check_vals = {
                    'check_bank_id': check_bank_id,
                    'check_bank_acc': data.get('check_bank_acc'),
                    'check_number': data.get('check_number'),
                    'check_owner': data.get('check_owner'),
                    'check_owner_vat': data.get('check_owner_vat'),
                    'check_pay_date': data.get('check_pay_date'),
                }
                line.write(check_vals)
                break

        return statement_id

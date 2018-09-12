# -*- coding: utf-8 -*-
from openerp import models

class PosOrder(models.Model):
    _inherit = "pos.order"

    def _payment_fields(self, cr, uid, ui_paymentline, context=None):
        res = super(PosOrder, self)._payment_fields(cr, uid, ui_paymentline, context)
        res.update({
            'check_bank_id': ui_paymentline.get('check_bank_id'),
            'check_bank_acc': ui_paymentline.get('check_bank_acc'),
            'check_number': ui_paymentline.get('check_number'),
            'check_owner': ui_paymentline.get('check_owner')
        })
        return res

    def add_payment(self, cr, uid, order_id, data, context=None):
        statement_id = super(PosOrder, self).add_payment(cr, uid, order_id, data, context)
        StatementLine = self.pool.get('account.bank.statement.line')
        checkObj = self.pool.get('account.check')
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
                    'check_owner': data.get('check_owner')
                }
                line.write(check_vals)
                break

        return statement_id

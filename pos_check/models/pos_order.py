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
            'check_owner': ui_paymentline.get('check_owner'),
            'check_owner_vat': ui_paymentline.get('check_owner_vat'),
            'check_pay_date': ui_paymentline.get('check_pay_date'),
        })
        return res

    def add_payment(self, cr, uid, order_id, data, context=None):
        statement_id = super(PosOrder, self).add_payment(cr, uid, order_id, data, context)
        StatementLine = self.pool.get('account.bank.statement.line')
        checkObj = self.pool.get('account.check')
        ## {'payment_date': u'2018-09-12 02:35:43', 
        # 'payment_name': False, 
        # 'statement_id': 42, 
        # 'journal': 10, 
        # 'amount': 173, 
        # 'check_bank_acc': u'111', 
        # 'check_owner': u'11111', 
        # 'check_bank_id': 3, 
        # 'check_number': u'1111'}
        print data
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
        checkObj.create(cr, uid, check,context)
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

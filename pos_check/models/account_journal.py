# -*- coding: utf-8 -*-
from openerp import fields, models, api


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    check_info_required = fields.Boolean('Check info required?', default=False)
    check_auto_fill_amount = fields.Boolean('Auto fill amount?', default=False)
    check_bank_name_visible = fields.Boolean('Bank name visible?', default=True)
    check_bank_name_required = fields.Boolean('Bank name required?', default=True)
    check_bank_acc_visible = fields.Boolean('Bank account number visible?', default=True)
    check_bank_acc_required = fields.Boolean('Bank account number required?', default=True)
    check_owner_visible = fields.Boolean('Check owner visible?', default=True)
    check_owner_required = fields.Boolean('Check owner required?', default=True)
    check_owner_vat_visible = fields.Boolean('Check owner vat visible?', default=True)
    check_owner_vat_required = fields.Boolean('Check owner vat required?', default=True)
    check_pay_date_visible = fields.Boolean('Check pay date visible?', default=True)
    check_pay_date_required = fields.Boolean('Check pay date required?', default=True)
    is_check = fields.Boolean('Es cheque?', default=False)

    @api.onchange('check_bank_name_visible', 'check_bank_name_required', 'check_bank_acc_visible',
    'check_bank_acc_required', 'check_owner_visible', 'check_owner_required', 'check_owner_vat_visible', 'check_owner_vat_required',
    'check_pay_date_visible', 'check_pay_date_required')
    def _onchange_check_visible_and_required(self):
        if not self.check_bank_name_visible and self.check_bank_name_required:
            self.check_bank_name_required = False
        if not self.check_bank_acc_visible and self.check_bank_acc_required:
            self.check_bank_acc_required = False
        if not self.check_owner_visible and self.check_owner_required:
            self.check_owner_required = False
        if not self.check_owner_vat_visible and self.check_owner_vat_required:
            self.check_owner_vat_required = False
        if not self.check_pay_date_visible and self.check_pay_date_required:
            self.check_pay_date_required = False

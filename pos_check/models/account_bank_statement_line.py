# -*- coding: utf-8 -*-
from openerp import fields, models


class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    check_bank_id = fields.Many2one('res.bank', string="Check bank")
    check_bank_acc = fields.Char('Check bank account')
    check_number = fields.Char()
    check_owner = fields.Char()
    check_owner_vat = fields.Char()
    check_pay_date = fields.Date()
    check_cbu = fields.Char('CBU')
    reference = fields.Char('Referencia')
    check_info_required = fields.Boolean(related='journal_id.check_info_required', readonly=True)
    check_bank_name_visible = fields.Boolean(related='journal_id.check_bank_name_visible', readonly=True)
    check_bank_name_required = fields.Boolean(related='journal_id.check_bank_name_required', readonly=True)
    check_bank_acc_visible = fields.Boolean(related='journal_id.check_bank_acc_visible', readonly=True)
    check_bank_acc_required = fields.Boolean(related='journal_id.check_bank_acc_required', readonly=True)
    check_owner_visible = fields.Boolean(related='journal_id.check_owner_visible', readonly=True)
    check_owner_required = fields.Boolean(related='journal_id.check_owner_required', readonly=True)
    check_owner_vat_visible = fields.Boolean(related='journal_id.check_owner_vat_visible', readonly=True)
    check_owner_vat_required = fields.Boolean(related='journal_id.check_owner_vat_required', readonly=True)
    check_pay_date_visible = fields.Boolean(related='journal_id.check_pay_date_visible', readonly=True)
    check_pay_date_required = fields.Boolean(related='journal_id.check_pay_date_required', readonly=True)
    check_cbu_visible = fields.Boolean(related='journal_id.check_cbu_visible', readonly=True)
    check_cbu_required = fields.Boolean(related='journal_id.check_cbu_required', readonly=True)
    reference_visible = fields.Boolean(related='journal_id.reference_visible', readonly=True)
    reference_required = fields.Boolean(related='journal_id.reference_required', readonly=True)
    check_number_visible = fields.Boolean(related='journal_id.check_number_visible', readonly=True)
    check_number_required = fields.Boolean(related='journal_id.check_number_required', readonly=True)

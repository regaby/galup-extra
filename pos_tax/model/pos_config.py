# -*- coding: utf-8 -*-
from openerp import api, fields, models, _

class pos_config(models.Model):
    _inherit = "pos.config"

    display_tax_orderline = fields.Boolean('Display tax orderline', default=1)
    display_tax_receipt = fields.Boolean('Display tax receipt', default=1)
    update_tax = fields.Boolean('Change tax of order', default=1)
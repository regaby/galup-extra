# -*- coding: utf-8 -*-
from openerp import models,fields

class account_tax(models.Model):
    _inherit = 'account.tax'
    
    pos_enable = fields.Boolean("Usar en el POS?",default=False)
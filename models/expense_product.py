# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class ExpenseProduct(models.Model):
    _inherit = 'product.template'
    
    is_product = fields.Boolean(string='Est un produit')



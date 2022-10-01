# -*- coding: utf-8 -*-
 
from odoo import api, fields, models, _
 
class Department(models.Model):
    _inherit = 'hr.department'
     
    acronyms = fields.Char(string='Sigle')
    timbre = fields.Text('Timbre')
    prefix = fields.Char(string='Préfix')
    
    _sql_constraints = [
        ('departement_uniq', 'UNIQUE (name, company_id)',  'Un nom de Direction/Service à la fois par une structure!'),
        ('timbre_uniq', 'UNIQUE (timbre)',  'Le timbre doit être unique!')
        ]
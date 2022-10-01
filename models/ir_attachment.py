# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
 

class NaturePJ(models.Model):
    _name = 'cim.nature.pj'
    _description = 'Nature pj'
    
    name = fields.Char(string="Intitilé", required=True)
    code = fields.Char("Code", required=True)
    description = fields.Text(string="Description")
    
    _sql_constraints = [
        ('name_naturepj_uniq', 'UNIQUE (name)',  "L'intitulé de la nature des PJ doit être unique!"),
        ('code_naturepj_uniq', 'UNIQUE (code)',  "Le code de la nature des PJ doit être unique!")
        ]


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'
    
    
    name = fields.Char('Name', required=True)
    nature_pj_id = fields.Many2one('cim.nature.pj', string='Nature PJ')
    
    @api.onchange('nature_pj_id')
    def _set_name(self):
        self.name = self.nature_pj_id.name
    
    
    
     
    

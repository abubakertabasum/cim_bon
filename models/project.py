# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

STATE_PROJECT_SELECTION = [
                    ('new', "Nouveau"),
                    ('validated', "Validé")]

class Project(models.Model):
    _name = 'cim.project'
    _description = "Programme d'activités"

    name = fields.Char(string='Nom', required=True)
    code = fields.Char(string='Code', required=True)
    date_from = fields.Datetime(string='Date début', required=False)
    date_to = fields.Datetime(string='Date fin', required=False)
    state = fields.Selection(STATE_PROJECT_SELECTION, string='Statut',default='new')
    company_id = fields.Many2one('res.company', string='Structure', readonly=True, default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True, default=lambda self: self.env.user.company_id.currency_id)
    description = fields.Text('Description')
    active = fields.Boolean('Active', default=True)
    budget_line_ids = fields.One2many("cim.budget.line", "programme_id", string="Budgets")
    
    _sql_constraints = [
        ('prog_acti_name_uniq', 'UNIQUE (name, company_id)',  "Un programme d'activité à la fois pour une structure!"),
        ('prog_acti_code_uniq', 'UNIQUE (code, company_id)',  "Un code unique par programme d'activité et par structure!")
        ]
    
        
    
    
    @api.multi
    def act_validate(self):
        '''
        Valider le programme d'activite
        '''
        for record in self:
            record.write({'state': 'validated'})
            
    @api.multi
    def act_annuler(self):
        for record in self:
            record.write({'state': 'new'})
            
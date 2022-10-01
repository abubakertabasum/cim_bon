# -*- coding: utf-8 -*

from odoo import models,fields,api,_
from odoo.exceptions import ValidationError


class Employee(models.Model):
    _inherit = 'hr.employee'
    _rec_name = 'default_name'
    
    default_name = fields.Char(string="Nom - Matricule", compute="_compute_default_name")
    matricule = fields.Char(string="Matricule")
    categ_id = fields.Many2one('cim.employee.categ', string='Catégorie', required=True)
    work_location_id = fields.Many2one('cim.localite', string='Lieu de travail')
    categ_grade_id = fields.Many2one('cim.agent.categ', string='Catégorie')
    echelle_grade_id = fields.Many2one('cim.agent.echelle', string='Echelle')
    echelon_grade_id = fields.Many2one('cim.agent.echelon', string='Echelon')
    emploi_agent_id = fields.Many2one('cim.emploi.agent', string='Emploi')
    type_agent = fields.Selection([('interne','Interne'),('externe','Externe')], string="Type d'agent", required=True, default='interne')
    # type_agent = fields.Selection([('interne','Interne'),('externe','Externe')], string="Type d'agent", compute="_compute_type_agent", store=True)
    distinction = fields.Text(string='Distinction')
    signature = fields.Html('Signature')
    civilite = fields.Selection([('M.', 'Monsieur'),('Mme', 'Madame'),('Mlle', 'Mademoiselle')], 'Civilité', required=True, default='M.')
    
    user_id = fields.Many2one('res.users', 'User', related='resource_id.user_id', store=True, readonly=False
                              , domain="[('employee_ids', '=', False)]")
    
    _sql_constraints = [
        ('matricule_structure', 'UNIQUE (matricule, company_id)',  'Un numéro matricule unique est requis par agent et par structure')
        ]
    
    @api.one
    @api.depends('name','matricule')
    def _compute_default_name(self):
        if self.matricule:
            self.default_name = self.name + " - " + self.matricule
        else:
            self.default_name = self.name
    
    def _set_signature_employee(self, fonction, name, distinction):
        signature_html = '''
            <p><strong>%s.</strong></p>
            <p>&nbsp;</p>
            <p>&nbsp;</p>
            <p><strong>%s.</strong></p>
            <p><em>%s</em></p>
        ''' %(fonction, name, distinction)
        return signature_html
    
    @api.one
    def act_generate_signature(self):
        signature = self._set_signature_employee(self.job_id.name, self.name, self.distinction)
        self.write({'signature': signature})


    @api.constrains('matricule')
    def _check_matricule(self):
        if self.matricule:
            print(self.matricule)
            count_matricule = self.env['hr.employee'].search_count([('matricule', '=', self.matricule)])
            print(count_matricule)
            if count_matricule > 1:
                raise ValidationError(_("Le nnuméro matricule de l'agent doit être unique!"))
    
    
    @api.one
    @api.depends('company_id.etatique')
    def _compute_type_agent(self):
        if self.company_id.etatique:
            self.type_agent = 'interne'
        else:
            self.type_agent = 'externe'
    

class EmployeeCateg(models.Model):
    _name = 'cim.employee.categ'
    _description = 'Catégorie'
    
    name = fields.Char(string='Intitulé', required=True)
    
    _sql_constraints = [
        ('name_categ_employee_uniq', 'UNIQUE (name)',  "L'intitulé de la catégorie de mission doit être unique")
        ]

class AgentCateg(models.Model):
    _name = 'cim.agent.categ'
    _description = "Catégorie du grade de l'agent"
    
    name = fields.Char(string='Intitulé', required=True)
    
    _sql_constraints = [
        ('name_categ_agent_uniq', 'UNIQUE (name)',  "L'intitulé de la catégorie du grade doit être unique")
        ]

class AgentEchelle(models.Model):
    _name = 'cim.agent.echelle'
    _description = "Echelle du grade de l'agent"
    
    name = fields.Integer(string="Nom de l'échelle", required=True)
    
    _sql_constraints = [
        ('name_echelle_agent_uniq', 'UNIQUE (name)',  "L'intitulé de l'échelle doit être unique"),
        ('name_positiv', 'CHECK (name > 0 )',  "La valeur de l'échelle est toujours supérieure à 0!")
        ]

class AgentEchelon(models.Model):
    _name = 'cim.agent.echelon'
    _description = "Echelon du grade de l'agent"
    
    name = fields.Integer(string="Nom de l'échelon", required=True)
    
    _sql_constraints = [
        ('name_echelon_agent_uniq', 'UNIQUE (name)',  "L'intitulé de l'échelon doit être unique"),
        ('name_positiv', 'CHECK (name > 0 )',  "La valeur de l'échelon est toujours supérieure à 0!")
        ]
    
class Job(models.Model):
    _inherit = 'hr.job'
    
    name = fields.Char(string="Intitulé de la fonction")
    _sql_constraints = [
        ('name_uniq', 'UNIQUE (name,company_id)',  'Le nom de la fonction doit être unique dans la structure!')
        ]
    
class Emploi(models.Model):
    _name = 'cim.emploi.agent'
    
    name = fields.Char(string="Intitulé de l'emploi")
    active = fields.Boolean(string="Est activé", default=True)
    _sql_constraints = [
        ('name_uniq', 'UNIQUE (name)',  "Le nom de l'emploi  doit être unique pour tous les agent!")
        ]
    

# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import datetime
from email.policy import default

STATE_BUDGET_SELECTION = [
                    ('new', "Nouveau"),
                    ('validated', "Validé")]


STATE_EXERCICE_BUDGETAIRE_SELECTION = [
                    ('elaboration', "En saisie"),
                    ('execution', "En exécution"),
                    ('clos', "Clos")]

YEAR_SELECTION = [
        ('2018', "2018"),
        ('2019', "2019"),
        ('2020', "2020"),
        ('2021', "2021"),
        ('2022', "2022"),
        ('2023', "2023"),
        ('2024', "2024"),
        ('2025', "2025"),
        ('2026', "2026"),
        ('2027', "2027"),
        ('2028', "2028"),
        ('2029', "2029"),
        ('2030', "2030"),
        ('2031', "2031"),
        ('2032', "2032"),
        ('2033', "2033"),
        ('2034', "2034"),
        ('2035', "2035"),
        ('2036', "2036"),
        ('2037', "2037"),
        ('2038', "2038"),
        ('2039', "2039"),
        ('2040', "2040"),
        ('2041', "2041"),
        ('2042', "2042"),
        ('2043', "2043"),
        ('2044', "2044"),
        ('2045', "2045"),
        ('2046', "2046"),
        ('2046', "2046"),
        ('2047', "2047"),
        ('2048', "2048"),
        ('2049', "2049"),
        ('2050', "2050"),]

def get_years():
    year_list = []
    for i in range(2019, 2040):
        year_list.append((i, str(i)))
    return year_list

class Budget(models.Model):
    _name = 'cim.budget'
    _inherit = ['mail.thread']
    _description = 'Budget'
    
    @api.model
    def _default_exercice_budgetaire(self):
        return self.env['cim.exercice.budgetaire'].search([('state','=','execution'),('active','=',True)], limit=1)
    
    name = fields.Char(string='Intitulé', track_visibility='onchange', copy=False, compute="_compute_budget_name")
    company_id = fields.Many2one('res.company', string='Structure' , default=lambda self: self.env.user.company_id)
    budget_type_id = fields.Many2one('cim.budget.type', string='Type de budget', required=True, track_visibility='onchange')
    state = fields.Selection(STATE_BUDGET_SELECTION, string='Statut', default='new', index=True, readonly=True, track_visibility='onchange', copy=False)
    budget_line_ids = fields.One2many("cim.budget.line","budget_id", string="Lignes budgétaires")
    exercice_id = fields.Many2one('cim.exercice.budgetaire', string='Exercice budgetaire', default=_default_exercice_budgetaire, required=True, track_visibility='onchange')
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True, default=lambda self: self.env.user.company_id.currency_id)
    montant_budget = fields.Monetary(string='Montant global budget', currency_field='currency_id', required=True, track_visibility='onchange')   
    total = fields.Monetary(string='Montant total de PA', store=True, currency_field='currency_id', readonly=True, compute="_compute_total", track_visibility='onchange')   
    
    _sql_constraints = [
        ('exercice_id_uniq', 'UNIQUE (exercice_id,company_id)',  'Un seul budget est autorisé par exercice et par structure!')
        ]
    
    @api.one
    @api.depends('company_id','exercice_id')
    def _compute_budget_name(self):
        self.name = 'Budget global des missions de la structure %s, exercice budgétaire %s' %(self.company_id.name, self.exercice_id.name)
    
    @api.depends('budget_line_ids.montant')
    def _compute_total(self):
        self.total = sum(line.montant for line in self.budget_line_ids)
    
    @api.constrains('montant_budget','total')
    def _check_montant_budget(self):
        if self.montant_budget < self.total:      
            raise ValidationError(_("Le montant total des rubriques doit être inférieur ou égal au montant global du budget."))
      
    
    @api.multi
    def act_validate(self):
        '''
        Valider le budget
        '''
        for record in self:
            record.write({'state': 'validated'})
            
    @api.multi
    def act_annuler(self):
        for record in self:
            record.write({'state': 'new'})
    
            
class BudgetType(models.Model):
    _name = 'cim.budget.type'
    
    name = fields.Char(string='Intitulé', required=True)
    code = fields.Char("Code", required=True, size=5)
    description = fields.Text(string='Description')
    active = fields.Boolean("Est Activé", default=True)
    
    _sql_constraints = [
        ('code_budgettype_uniq', 'UNIQUE (code)',  'Le code est unique sur 5 caractères max!'),
        ('name_budgettype_uniq', 'UNIQUE (name)',  "L'intitulé du type de budget doit être unique")
        ]
    
            
            
class CimBudgetLine(models.Model):
    _name = 'cim.budget.line'
    _inherit = ['mail.thread']
    _description = 'Lignes budgetaires'
    _rec_name = "programme_id"
    
    @api.model
    def _default_exercice_budgetaire(self):
        return self.env['cim.exercice.budgetaire'].search([('state','=','execution'),('active','=',True)], limit=1)
    
    programme_id = fields.Many2one('cim.project', "Programme d'activités", required=True, domain="[('state', '=', 'validated')]", index=True, track_visibility='onchange')
    budget_id = fields.Many2one("cim.budget", string="Budget", index=True)  
    sectionbudgetaire_id = fields.Many2one('cim.sectionbudgetaire', "Section budgétaire", index=True, required=True )
    programmechapitre_id = fields.Many2one('cim.programmechapitre', "Programme/Chapitre", index=True, required=True )
    actionarticle_id = fields.Many2one('cim.actionarticle', "Action/Article", index=True, required=True)
    activiteparagraphe_id = fields.Many2one('cim.activiteparagraphe', "Activite/Paragraphe", index=True, required=True)
    paragrapherubrique_id = fields.Many2one('cim.paragrapherubrique', "Paragraphe/Rubrique", index=True, required=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True, default=lambda self: self.env.user.company_id.currency_id)
    montant = fields.Monetary(string='Montant', currency_field='currency_id', required=True, track_visibility='onchange')
    
    mission_ids = fields.One2many("cim.mission", "budget_line_id", string="Missions")
    credit_dispo = fields.Monetary(string='Credit disponible', currency_field='currency_id', readonly=True, track_visibility='onchange')
    exercice_id = fields.Many2one('cim.exercice.budgetaire', string='Exercice budgetaire', default=_default_exercice_budgetaire, track_visibility='onchange')
    
    
    _sql_constraints = [
        ('budgline_uniq', 'UNIQUE (sectionbudgetaire_id, programmechapitre_id, actionarticle_id, activiteparagraphe_id, paragrapherubrique_id, budget_id, company_id )',  "Une seule rubrique budgétaire est autorisée par budget"),
        ('budgline_prog_uniq', 'UNIQUE (sectionbudgetaire_id, programmechapitre_id, actionarticle_id, activiteparagraphe_id, paragrapherubrique_id, budget_id, company_id, programme_id )', "Une seule rubrique par programme d'activité")
        ]
    
    @api.model
    def create(self, vals):
        vals['credit_dispo'] = vals['montant'] or 0.0
        return super(CimBudgetLine, self).create(vals)
    
    @api.model
    def edit(self, vals):
        vals['credit_dispo'] = vals['credit_dispo'] + vals['montant'] or 0.0
        return super(CimBudgetLine, self).edit(vals)
    
class ExerciceBudgetaire(models.Model):
    _name = 'cim.exercice.budgetaire'
    _description = 'Exercice Budgetaire'
    
    def _default_year(self):
        now = datetime.datetime.now()
        return str(now.year)
    
    name = fields.Selection(YEAR_SELECTION, string="Année budgétaire", required=True, default=_default_year)
    date_from = fields.Date('Date début', compute="_compute_date", store=True)
    date_to = fields.Date('Date fin', compute="_compute_date", store=True)
    state = fields.Selection(STATE_EXERCICE_BUDGETAIRE_SELECTION, string="Statut", default="elaboration")
    description = fields.Text(string='Description')
    active = fields.Boolean("Ouvert", default=True)
    
    
    _sql_constraints = [
        ('name_uniq', 'UNIQUE (name)', "Un seul numéro d'exercice est autorisé!"),
        ('name_positiv', 'CHECK (name > 0)',  "Un exercice budgétaire est toujours positif")
        ]
    
    @api.depends('name')
    def _compute_date(self):
        self.date_from = datetime.date(int(self.name), 1, 1)
        self.date_to = datetime.date(int(self.name), 12, 31)
        

    @api.model
    def create(self, vals):
        exo = vals.get('name', False)
        if exo :
            exercice = self.env['cim.exercice.budgetaire'].search([('name','=', exo)])
            if exercice:
                raise ValidationError(_('Un exercice ayant ce même numéro exixte déjà. Veuillez en créer un autre!'))
        return super(ExerciceBudgetaire, self).create(vals)
    
    @api.multi
    def act_execute(self):
        '''
        Executer l'exercice budgetaire
        '''
        for record in self:
            record.write({'state': 'execution'})
            
    @api.multi
    def act_annuler(self):
        for record in self:
            record.write({'state': 'elaboration'})
            
    @api.multi
    def act_cloturer(self):
        '''
        Clôturer l'exercice budgetaire
        '''
        for record in self:
            self.active = False
            record.write({'state': 'clos'})
    
    @api.multi
    def write(self, values):
        result = super(ExerciceBudgetaire, self).write(values)
        if values.get('state', False) == 'execution':
            exercice = self.env['cim.exercice.budgetaire'].search_count([('state','=', 'execution'),('active','=', True)])
            if exercice > 1:
                raise ValidationError(_("Un exercice budgétaire est déjà en exécution!"))
        return result   
    
    @api.constrains('date_from','date_to')
    def _check_date_exercice(self):
        if self.date_from > self.date_to:
            raise ValidationError(_('La date du début doit être inférieure à date de fin!'))
        
    @api.multi
    def _check_name_exercice(self, values):
        result = super(ExerciceBudgetaire, self).write(values)
        if values.get('state', False) == 'elaboration':
            exercice = self.env['cim.exercice.budgetaire'].search_count([('name','=', self.name)])
            if exercice > 1:
                raise ValidationError(_("Ce numéro d'exercice existe déjà!"))
        return result  
    
        
class Sectionbudgetaire(models.Model):
    _name = 'cim.sectionbudgetaire'
    _description = 'Section de la nomenclature budgétaire'
    
    name = fields.Char("Intitulé", required=True)
    code_section = fields.Char("Code", required=True, size=2)
    
    company_id = fields.Many2one('res.company', string='Structure', readonly=True, default=lambda self: self.env.user.company_id, track_visibility='onchange')
    budget_line_ids = fields.One2many("cim.budget.line", "programme_id", string="Lignes budgétaires")
    
    _sql_constraints = [
        ('code_uniq_section', 'UNIQUE (code_section, company_id)',  "Le code de la section doit être unique par structure!"),
        ('name_uniq_section', 'UNIQUE (name, company_id)',  "L'intitulé de la section doit être unique par structure")
        ]
    
    
class Programmechapitre(models.Model):
    _name = 'cim.programmechapitre'
    _description = 'Programme ou chapitre de la nomenclature budgétaire'
    
    name = fields.Char("Intitulé", required=True)
    code_programmechapitre = fields.Char("Code", required=True, size=3)
    sectionbudgetaire_id = fields.Many2one("cim.sectionbudgetaire", string="Section budg.", required=True)  
    
    company_id = fields.Many2one('res.company', string='Structure', readonly=True, default=lambda self: self.env.user.company_id, track_visibility='onchange')
    budget_line_ids = fields.One2many("cim.budget.line", "programme_id", string="Lignes budgétaires")
    
    _sql_constraints = [
        ('code_uniq_programmechapitre', 'UNIQUE (code_programmechapitre, company_id)',  'Un code unique par structure!'),
        ('name_uniq_programmechapitre', 'UNIQUE (name, company_id)',  "Un intitulé unique par structure est requis!")
        ]
    
class Actionarticle(models.Model):
    _name = 'cim.actionarticle'
    _description = 'Action ou article de la nomenclature budgétaire'
    
    name = fields.Char("Intitulé", required=True)
    code_actionarticle = fields.Char("Code", required=True, size=5)
    programmechapitre_id = fields.Many2one("cim.programmechapitre", string="Prog./Chap.", required=True)
    
    company_id = fields.Many2one('res.company', string='Structure', readonly=True, default=lambda self: self.env.user.company_id, track_visibility='onchange')
    budget_line_ids = fields.One2many("cim.budget.line", "programme_id", string="Lignes budgétaires")
    
    _sql_constraints = [
        ('code_uniq_actionarticle', 'UNIQUE (code_actionarticle, company_id)',  "Un code unique par structure!"),
        ('name_uniq_actionarticle', 'UNIQUE (name, company_id)',  "Un intitulé unique par structure!")
        ]
   
class Activiteparagraphe(models.Model):
    _name = 'cim.activiteparagraphe'
    _description = 'Activité ou paragraphe de la nomenclature budgétaire'
    
    name = fields.Char("Intitulé", required=True)
    code_activiteparagraphe = fields.Char("Code", required=True, size=7)
    actionarticle_id = fields.Many2one("cim.actionarticle", string="Action/Article", required=True)
    
    company_id = fields.Many2one('res.company', string='Structure', readonly=True, default=lambda self: self.env.user.company_id, track_visibility='onchange')
    budget_line_ids = fields.One2many("cim.budget.line", "programme_id", string="Lignes budgétaires")
    
    _sql_constraints = [
        ('code_uniq_activiteparagraphe', 'UNIQUE (code_activiteparagraphe, company_id)',  'Le code doit être unique par structure!'),
        ('name_uniq_activiteparagraphe', 'UNIQUE (name, company_id)',  "Un intitulé unique par structure!")
        ]
   
class Paragrapherubrique(models.Model):
    _name = 'cim.paragrapherubrique'
    _description = 'Paragraphe ou rubrique de la nomenclature budgétaire'
    
    name = fields.Char("Intitulé", required=True)
    code_paragrapherubrique = fields.Char("Code", required=True, size=10)
    activiteparagraphe_id = fields.Many2one("cim.activiteparagraphe", string="Acti./Parag.", required=True)
    
    company_id = fields.Many2one('res.company', string='Structure', readonly=True, default=lambda self: self.env.user.company_id, track_visibility='onchange')
    budget_line_ids = fields.One2many("cim.budget.line", "programme_id", string="Lignes budgétaires")
    
    _sql_constraints = [
        ('code_uniq_paragrapherubrique', 'UNIQUE (code_paragrapherubrique, company_id)',  "Un code unique par structure!")
#         ('name_uniq_paragrapherubrique', 'UNIQUE (name, company_id)',  "Un intitulé unique par structure!")
        ]
    


    
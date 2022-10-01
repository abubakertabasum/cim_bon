# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class Company(models.Model):
    _inherit = 'res.company'
    
    
    localite_id = fields.Many2one('cim.localite', string='Localité')
    sigle = fields.Char(string='Sigle')
    company_type_id = fields.Many2one('cim.company.type', string='Type de structure')
    timbre = fields.Text('Timbre')
    prefix = fields.Char(string='Préfix')
    etatique = fields.Boolean(string='Est étatique', default=True)
    ordonnateur_id = fields.Many2one('hr.employee', string='Ordonnateur')
    ordonnateur_externe_id = fields.Many2one('hr.employee', string='Ordonnateur externe')
    regisseur_id = fields.Many2one('hr.employee', string='Régisseur')
    
    auto_number_mission = fields.Boolean('Numéro automatique')
    show_signature = fields.Boolean('Signature')
    #show_logo = fields.Boolean('Affichage du Logo')
    auto_compute_carb = fields.Boolean('Frais de carburant')
    taux_journalier = fields.Monetary(string='Taux journalier', currency_field='currency_id')
    pj_ids = fields.Many2many('cim.nature.pj', relation='res_company_nature_pj_rel', string='Pièces justificatives')
    
    # Délais de traitement
    
    delais_approbation = fields.Integer("Approbation")
    delais_budgetisation = fields.Integer("Budgétisation")
    delais_validation = fields.Integer("Validation")
    delais_paiement = fields.Integer("Paiement")
    delais_verification = fields.Integer("Vérification")
    delais_cloture = fields.Integer("Clôture")
    
    @api.model
    def _get_user_currency(self):
        currency_id = self.env['res.currency'].search([('name','=','XOF')])
        return currency_id or self._get_euro()

class CompanyType(models.Model):
    _name = 'cim.company.type'
    
    name = fields.Char(string='Intitulé', required=True)
    description = fields.Text(string='Description')
    cocm = fields.Boolean(string='COCM', default=False)
    active = fields.Boolean("Est actif", default=True)
    
    _sql_constraints = [
        ('name_uniq', 'UNIQUE (name)',  'Un type de structure doit être unique!')
        ]

class ZoneMission(models.Model):
    _name = 'cim.zone.mission'
    
    name = fields.Char(string='Intitulé', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean("Est Activé", default=True)
    mission_type_id = fields.Many2one('cim.mission.type', string='Type de mission', required=False)
    
    _sql_constraints = [
        ('name_zone_uniq', 'UNIQUE (name)',  'Le nom de la zone doit être unique!')
        ]


class Localite(models.Model):
    _name = "cim.localite"
    _description = "Localités"

    name = fields.Char(string="Nom de la localité", required=True)
    typelocalite_id = fields.Many2one("cim.typelocalite", string="Type de localité")
    zone_mission_id = fields.Many2one("cim.zone.mission", string="Zone de mission", required=True)
    localite_mere_id = fields.Many2one("cim.localite", string="Localité mère")
    active = fields.Boolean("Est Activé", default=True)
    
    _sql_constraints = [
        ('name_uniq', 'UNIQUE (name)',  'Le nom de la localité doit être unique!')
        ]


class Typelocalite(models.Model):
    _name = "cim.typelocalite"
    _description = "Types de localité"

    name = fields.Char(required=True, string="Intitulé")
    description = fields.Text(string="Description")
    active = fields.Boolean("Est Activé", default=True)

    _sql_constraints = [
        ('name_uniq', 'UNIQUE (name)',  'Le libellé du type de la localité doit être unique!')
        ]

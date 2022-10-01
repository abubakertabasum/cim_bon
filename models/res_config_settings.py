# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    auto_number_mission = fields.Boolean('Numéro automatique', related='company_id.auto_number_mission', readonly=False)
    currency_id = fields.Many2one('res.currency', string='Devise', default=lambda self: self.env.user.company_id.currency_id)
    auto_compute_carb = fields.Boolean('Frais de carburant', related='company_id.auto_compute_carb', readonly=False)
    taux_journalier = fields.Monetary(string='Taux journalier', currency_field='currency_id', related="company_id.taux_journalier", readonly=False)
    show_signature = fields.Boolean('Signature', related="company_id.show_signature", readonly=False)
    #show_logo = fields.Boolean('Afficher logo', related="company_id.show_logo", readonly=False)
    pj_ids = fields.Many2many('cim.nature.pj', relation='config_settings_nature_pj_rel', string='Pièces justificatives', related="company_id.pj_ids", readonly=False)
    
    # Délais de traitement
    
    delais_approbation = fields.Integer("Approbation", related="company_id.delais_approbation", readonly=False)
    delais_budgetisation = fields.Integer("Budgétisation", related="company_id.delais_budgetisation", readonly=False)
    delais_validation = fields.Integer("Validation", related="company_id.delais_validation", readonly=False)
    delais_paiement = fields.Integer("Paiement", related="company_id.delais_paiement", readonly=False)
    delais_verification = fields.Integer("Vérification", related="company_id.delais_verification", readonly=False)
    delais_cloture = fields.Integer("Clôture", related="company_id.delais_cloture", readonly=False)
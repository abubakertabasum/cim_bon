# -*- coding: utf-8 -*-

from odoo import tools
from odoo import fields, models, tools, api

STATE_MISSION_SELECTION = [
    ('new', "Nouvelle"),
    ('initiation', "Initiée"),
    ('approbation', "Approuvée"), 
    ('budgeting', "Budgétisée"), 
    ('validate_sg', "Validée"),
    ('daf_payment', "Payée par le régisseur"),
    ('checked', "Vérifiée"),  
    ('done', "Clôturée"),
    ('canceled', "Annulée")]

STATE_MISSION_EVALUATION = [
    ('new_eval', "En cours"),
    ('validated_eval', "Evaluée")]


class MissionReport(models.Model):
    _name = "cim.mission.report"
    _description = "Statistiques des missions"
    _auto = False
    
    
    name = fields.Char(string='N° Mission', readonly=True)
    mission_type_id = fields.Many2one('cim.mission.type', string='Type de la mission', readonly=True)
    motif_mission_id = fields.Many2one('cim.motif.mission', string='Motif de mission', readonly=True)
    department_id = fields.Many2one('hr.department', string='Service demandeur', readonly=True)
    company_id = fields.Many2one('res.company', string='Structure', readonly=True)
    project_id = fields.Many2one('cim.project', "Programme d'activités", readonly=True)
    budget_line_id = fields.Many2one('cim.budget.line', string="Budget", readonly=True)
    bailleur_id = fields.Many2one('cim.bailleur', string='Bailleur', readonly=True)
    cocm_id = fields.Many2one('cim.cocm', string='COCM', readonly=True)
    
    # periode de la mission
    date_from = fields.Date(string='Date début', readonly=True)
    date_to = fields.Date(string='Date fin', readonly=True)
    duree_mission = fields.Integer(string="Durée (en jour)", readonly=True)
    
    with_financial_impact = fields.Boolean("Avec incidence financière", readonly=True)
    total_carb_mission = fields.Float(string='Total Carburant Mission', readonly=True)
    frais_mission_total = fields.Float(string='Montant total des frais', readonly=True)
    montant_total_paye = fields.Float(string='Montant total payé', readonly=True)
    is_paid = fields.Boolean(string="Payé", readonly=True)
    
    state = fields.Selection(STATE_MISSION_SELECTION, string='Statut', readonly=True)
    
    #évaluation des missions
    taux_moyen = fields.Float(string="Taux moyen de l'évaluation", readonly=True)
    state_eval = fields.Selection(STATE_MISSION_EVALUATION, string='Evaluation', readonly=True)
    
    # Localite des missions
#     loc_id = fields.One2many("cim.localite", string="Localité", readonly=True)
    distance_mission = fields.Float(string="Distance (en km)", readonly=True)
    
#     mission_id = fields.Many2one('cim.mission', string='Mission', readonly=True)
    
#     # Participant des missions
#     participant_id = fields.Many2one('hr.employee', "Participant", readonly=True)
#     role_mission_id = fields.Many2one('cim.role.mission', 'Rôle', readonly=True)
#     
#     # Véhicule des missions
#     vehicule_id = fields.Many2one('cim.vehicule', string='Véhicule', readonly=True)
    
    # Activités des missions
#     mail_activity_type_id = fields.Many2one('mail.activity.type', "Type d'activité", readonly=True)
#     date = fields.Datetime('Date', readonly=True)
    
    
    def _select(self):
        return """
            SELECT
                c.id,
                c.name,
                c.mission_type_id,
                c.motif_mission_id,
                c.department_id,
                c.company_id,
                c.project_id,
                c.budget_line_id,
                c.bailleur_id,
                c.cocm_id,
                c.date_from,
                c.date_to,
                c.duree_mission,
                c.with_financial_impact,
                c.total_carb_mission,
                c.frais_mission_total,
                c.montant_total_paye,
                c.is_paid,
                c.state,
                c.taux_moyen,
                c.state_eval,
                c.distance_mission
        """

    def _from(self):
        return """
            FROM cim_mission AS c
        """
    
    def _join(self):
        return """
            LEFT JOIN cim_mission_itineraire AS i ON i.mission_id = c.id
        """
    
    def _group_by(self):
        group_by_str = """
                GROUP BY c.id, i.loc_id
        """
        return group_by_str
    
    def _where(self):
        return """
            WHERE
                i.mission_id IS NOT NULL
        """

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                %s
                %s
            )
        """ % (self._table, self._select(), self._from())
        )
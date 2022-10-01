# -*- coding: utf-8 -*-

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

class AgentReport(models.Model):
    """ Mission Analysis (AGENT) """

    _name = "cim.agent.mission.report"
    _auto = False
    _description = "Analyse d'agent"
    _rec_name = 'id'

    mission_id = fields.Many2one('cim.mission', "Mission", readonly=True)
    participant_id = fields.Many2one('hr.employee', "Agent", readonly=True)
    role_mission_id = fields.Many2one('cim.role.mission', 'Rôle', readonly=True)
    
    name = fields.Char(string='N° Mission', readonly=True)
    mission_type_id = fields.Many2one('cim.mission.type', string='Type de la mission', readonly=True)
    motif_mission_id = fields.Many2one('cim.motif.mission', string='Motif de mission', readonly=True)
    department_id = fields.Many2one('hr.department', string='Service demandeur', readonly=True)
    company_id = fields.Many2one('res.company', string='Structure', readonly=True)
    project_id = fields.Many2one('cim.project', "Programme d'activités", readonly=True)
    budget_line_id = fields.Many2one('cim.budget.line', string="Budget", readonly=True)
    bailleur_id = fields.Many2one('cim.bailleur', string='Bailleur', readonly=True)
    cocm_id = fields.Many2one('cim.cocm', string='COCM', readonly=True)
    state = fields.Selection(STATE_MISSION_SELECTION, string='Statut', readonly=True)
    
    # periode de la mission
    date_from = fields.Date(string='Date début', readonly=True)
    date_to = fields.Date(string='Date fin', readonly=True)
    duree_mission = fields.Integer(string="Durée (en jour)", readonly=True)
    
    frais_mission = fields.Float(string='Frais de mission', readonly=True)

    def _select(self):
        return """
            SELECT
                p.id,
                p.mission_id,
                p.participant_id,
                p.role_mission_id,
                c.name,
                c.mission_type_id,
                c.motif_mission_id,
                c.department_id,
                c.company_id,
                c.project_id,
                c.budget_line_id,
                c.bailleur_id,
                c.cocm_id,
                c.state,
                c.date_from,
                c.date_to,
                c.duree_mission,
                (SELECT SUM(total_amount) FROM cim_expense WHERE mission_id=p.mission_id AND employee_id=p.participant_id) AS frais_mission
        """

    def _from(self):
        return """
            FROM cim_mission_participant AS p
        """

    def _join(self):
        return """
            JOIN cim_mission AS c ON p.mission_id = c.id
        """

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                %s
                %s
                %s
            )
        """ % (self._table, self._select(), self._from(), self._join())
        )

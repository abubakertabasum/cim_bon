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

class AgentSyntheseReport(models.Model):
    """ Mission Analysis (AGENT) """

    _name = "cim.agent.synthese.mission.report"
    _auto = False
    _description = "Analyse d'agent"
    _rec_name = 'id'

    participant_id = fields.Many2one('hr.employee', "Agent", readonly=True)
    exercice_id = fields.Many2one('cim.exercice.budgetaire', string='Exercice budgetaire', readonly=True)    
    department_id = fields.Many2one('hr.department', string='Service demandeur', readonly=True)
    company_id = fields.Many2one('res.company', string='Structure', readonly=True) 
    # periode de la mission
    date_from = fields.Date(string='Date début', readonly=True)
    date_to = fields.Date(string='Date fin', readonly=True)
    duree_mission = fields.Integer(string="Durée (en jour)", readonly=True)    
    frais_mission = fields.Float(string='Frais de mission', readonly=True)

    def _select(self):
        return """
            SELECT
                p.id,
                p.participant_id,
                c.exercice_id,
                c.department_id,
                c.company_id,
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

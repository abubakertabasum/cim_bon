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

class AgentsReport(models.Model):
    """ Mission Analysis (AGENT) """

    _name = "cim.agents.mission.report"
    _auto = False
    _description = "Analyse d'agent"
    # _rec_name = 'id'

    participant_id = fields.Many2one('hr.employee', "Agent", readonly=True)
    nombre_total = fields.Integer(string="Nombre total", readonly=True)    
    duree_totale = fields.Integer(string="Durée totale (en jour)", readonly=True)    
    montant_total = fields.Float(string='Total frais de mission', readonly=True)

    def _select(self):
        return """
            SELECT
                p.id,
                p.participant_id,
                COUNT(p.mission_id) as nombre_total,
                SUM(p.nbr_jour) as duree_totale,
                (SELECT SUM(total_amount) FROM cim_expense WHERE mission_id=p.mission_id AND employee_id=p.participant_id) as montant_total,
                m.exercice_id ,
                m.department_id ,
                m.company_id 
        """

    def _from(self):
        return """
            FROM cim_mission_participant AS p
        """

    def _join(self):
        return """
            JOIN cim_mission AS c ON p.mission_id = c.id
        """
    
    def _group_by(self):
        group_by_str = """
                GROUP BY p.id, p.participant_id, m.exercice_id, m.department_id, m.company_id
        """
        return group_by_str
    
    def _where(self):
        return """
            WHERE
                c.state in ('daf_payment', 'checked', 'done')
        """

    # @api.model_cr
    # def init(self):
    #     tools.drop_view_if_exists(self._cr, self._table)
    #     self._cr.execute("""
    #         CREATE OR REPLACE VIEW %s AS (
    #             %s
    #             %s
    #             %s
    #             %s
    #             %s
    #         )
    #     """ % (self._table, self._select(), self._from(), self._join(), self._where(), self._group_by)
    #     )
    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE view %s as
              %s
              FROM cim_mission_participant p, cim_mission m
                WHERE m.id = p.mission_id and m.state in ('daf_payment', 'checked', 'done')
                    and p.mission_id is not null and p.nbr_jour is not null and m.exercice_id is not null
                %s
        """ % (self._table, self._select(), self._group_by()))

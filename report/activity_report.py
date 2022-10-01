# -*- coding: utf-8 -*-

from odoo import fields, models, tools, api


class ActivityReport(models.Model):
    """ Mission Analysis """

    _name = "cim.activity.mission.report"
    _auto = False
    _description = "Analyse d'activité"
    _rec_name = 'id'

    date = fields.Datetime('Date', readonly=True)
    author_id = fields.Many2one('res.partner', 'Créé par', readonly=True)
    mission_id = fields.Many2one('cim.mission', "Mission", readonly=True)
#     subtype_id = fields.Many2one('mail.message.subtype', 'Subtype', readonly=True)
    mail_activity_type_id = fields.Many2one('mail.activity.type', "Type d'activité", readonly=True)
    
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

    def _select(self):
        return """
            SELECT
                m.id,
                m.mail_activity_type_id,
                m.author_id,
                m.date,
                c.id as mission_id,
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
                c.duree_mission
        """

    def _from(self):
        return """
            FROM mail_message AS m
        """

    def _join(self):
        return """
            JOIN cim_mission AS c ON m.res_id = c.id
        """

    def _where(self):
        return """
            WHERE
                m.model = 'cim.mission' AND m.mail_activity_type_id IS NOT NULL
        """

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                %s
                %s
                %s
                %s
            )
        """ % (self._table, self._select(), self._from(), self._join(), self._where())
        )

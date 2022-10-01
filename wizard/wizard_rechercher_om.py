# -*- coding: utf-8 -*-

from odoo import models, fields


class RechercherOM(models.TransientModel):
    _name = 'rechercher.om.wizard'
    _description = 'Rechercher Mission Wizard'
    
    name = fields.Char('N° Mission')
    
    def action_search(self):
        act = {
                'name': 'Ordres de mission',
                'view_mode': 'tree',
                'res_model': 'cim.mission.participant',
                'type': 'ir.actions.act_window',
                'domain': [('mission_id','like', self.name),('state_mission', '=', 'daf_payment')],
                }
        return act
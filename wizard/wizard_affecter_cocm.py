# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AffecterCOCM(models.TransientModel):
    _name = 'affecter.cocm.wizard'
    _description = 'Affecter COCM Wizard'
    
    @api.model
    def default_get(self, fields):
        
        result = super(AffecterCOCM, self).default_get(fields)
        if self._context.get('active_id'):
            mission = self.env['cim.mission'].browse(self._context['active_id'])
            result['mission_id'] = mission.id
        return result
    
    mission_id = fields.Many2one('cim.mission', 'Mission', index=True, readonly=True)
    cocm_id = fields.Many2one('cim.cocm', 'COCM', required=True)
    
    project_id = fields.Many2one('cim.project', "Programme d'activités", related='cocm_id.project_id')
    bailleur_id = fields.Many2one('cim.bailleur', string='Bailleur', related='cocm_id.bailleur_id')
    department_id = fields.Many2one('hr.department', string='Service demandeur', related='cocm_id.department_id')
    establishment_id = fields.Many2one('res.company', string='Structure', related='cocm_id.establishment_id')
    date_from = fields.Date(string='Date début', related='cocm_id.date_from')
    date_to = fields.Date(string='Date fin', related='cocm_id.date_to')
    duree_mission = fields.Integer(string="Durée (en jour)", related='cocm_id.duree_mission')
    loc_depart = fields.Many2one("cim.localite", string="Départ", related='cocm_id.loc_depart')
    loc_destination = fields.Many2one("cim.localite", string="Destination", related='cocm_id.loc_destination')
    
    def action_confirm(self):
        self.mission_id.write({'cocm_id': self.cocm_id.id})
        return
# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class InitiationCOCM(models.TransientModel):
    _name = 'initiation.cocm.wizard'
    _description = 'Initiation COCM Wizard'
    
    @api.model
    def default_get(self, fields):
        
        result = super(InitiationCOCM, self).default_get(fields)
        if self._context.get('active_id'):
            mission = self.env['cim.mission'].browse(self._context['active_id'])
            result['mission_id'] = mission.id
        return result
    
    mission_id = fields.Many2one('cim.mission', 'Mission', index=True, readonly=True)
    
    def action_yes(self):
        if self.mission_id:
            vals = {
                'object': self.mission_id.object,
                'motif_mission_id': self.mission_id.motif_mission_id.id,
                'description': self.mission_id.description,
                'date_from': self.mission_id.date_from,
                'date_to': self.mission_id.date_to,
                'department_id': self.mission_id.department_id.id,
                'company_id': self.mission_id.company_id.id,
                'loc_depart': self.mission_id.loc_depart.id,
                'loc_destination': self.mission_id.loc_destination.id,
                'bailleur_id': self.mission_id.bailleur_id.id,
                'project_id': self.mission_id.project_id.id,
                'employee_id': self.mission_id.employee_id.id,
                'itineraire_mission_ids' : [(6, 0, self.mission_id.itineraire_mission_ids.ids)],
                'participant_ids' : [(6, 0, self.mission_id.participant_ids.ids)],
                }
            cocm = self.env['cim.cocm'].create(vals)
            if self.mission_id.num_demande == False:
                seq = self.env['ir.sequence'].next_by_code('cim.dmd.mission.seq')
                seq = seq.replace("prefix1", str(self._get_prefix_structure(self.company_id.id)))
                seq = seq.replace("prefix2", str(self._get_prefix_service(self.department_id.id)))
                self.mission_id.write({'num_demande': seq, 'name': seq,'cocm_id': cocm.id, 'state': 'initiation'})
            else:
                self.mission_id.write({'name': self.mission_id.num_demande,'cocm_id': cocm.id, 'state': 'initiation'})
        return
    
    def action_no(self):
        self.mission_id.write({'state': 'initiation'})
        return
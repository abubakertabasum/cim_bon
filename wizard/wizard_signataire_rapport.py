# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

TYPE_RAPPORT_SELECTION = [
    ('dam', "DAM"),
    ('om', "OM"),
    ('epcf', "EPCF"), 
    ('epfc', "EPFC")]

class SignataireRapport(models.TransientModel):
    _name = 'signataire.rapport.wizard'
    _description = 'Signataire Rapport Wizard'
    
    @api.model
    def default_get(self, fields):
        
        result = super(SignataireRapport, self).default_get(fields)
        if self._context.get('active_id'):
            type_rapport = self._context.get('default_type_rapport')
            mission = self.env['cim.mission'].browse(self._context['active_id'])
            result['mission_id'] = mission.id
            if type_rapport:
                if type_rapport in ['dam','om'] and mission.mission_type_id.id == self.env.ref('cim.data_mission_type_internal').id:
                    result['signataire1_id'] = mission.department_id.manager_id.id
                    result['signataire2_id'] = mission.establishment_id.ordonnateur_id.id
                elif type_rapport in ['dam','om'] and mission.mission_type_id.id == self.env.ref('cim.data_mission_type_internal').id and mission.type_ordre_mission_id.id == self.env.ref('cim.data_mission_order_type_grouped').id:
                    result['signataire1_id'] = mission.department_id.manager_id.id
                    result['signataire2_id'] = mission.establishment_id.ordonnateur_externe_id.id
                elif type_rapport in ['dam','om'] and mission.mission_type_id.id == self.env.ref('cim.data_mission_type_external').id:
                    result['signataire1_id'] = mission.department_id.manager_id.id
                    result['signataire2_id'] = mission.establishment_id.ordonnateur_externe_id.id
                elif type_rapport in ['epcf','epfc'] and mission.mission_type_id.id == self.env.ref('cim.data_mission_type_internal').id:
                    result['signataire1_id'] = mission.establishment_id.regisseur_id.id
                    result['signataire2_id'] = mission.establishment_id.ordonnateur_id.id
                elif type_rapport in ['epcf','epfc'] and mission.mission_type_id.id == self.env.ref('cim.data_mission_type_external').id:
                    result['signataire1_id'] = mission.establishment_id.regisseur_id.id
                    result['signataire2_id'] = mission.establishment_id.ordonnateur_externe_id.id
        return result
    
    mission_id = fields.Many2one('cim.mission', 'Mission', index=True)
    signataire1_id = fields.Many2one('hr.employee', string='Signataire 1', required=True)
    signataire2_id = fields.Many2one('hr.employee', string='Signataire 2', required=True)
    type_rapport = fields.Selection(TYPE_RAPPORT_SELECTION, string='Type')
    
    
    
    def action_generate(self):
        self.mission_id.sudo().write({'signataire1_id':self.signataire1_id.id, 'signataire2_id':self.signataire2_id.id})
        if self.type_rapport == 'dam':
            action = self.mission_id.act_generate_mission_dam()
        elif self.type_rapport == 'om':
            action = self.mission_id.act_generate_ordre_mission()
        elif self.type_rapport == 'epcf':
            action = self.mission_id.act_generate_etat_prise_en_charge()
        elif self.type_rapport == 'epfc':
            action = self.mission_id.act_generate_etat_carburant()
        action.update({'close_on_report_download': True})
        return action

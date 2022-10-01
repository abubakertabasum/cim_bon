# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

STATE_MISSION_REJET_SELECTION = [
    ('new', "Nouvelle"),
    ('initiation', "Initiée"),
    ('approbation', "Approuvée"), 
    ('budgeting', "Budgétisée"), 
    ('validate_sg', "Validée"),
    ('daf_payment', "Payée par le régisseur"),
    ('checked', "Vérifiée"),  
    ('done', "Clôturée"),
    ('canceled', "Annulée")]

class MissionRejet(models.TransientModel):
    _name = 'cim.mission.rejet.wizard'
    _description = 'Mission Rejet Wizard'
    
    @api.model
    def default_get(self, fields):
        
        result = super(MissionRejet, self).default_get(fields)
        if self._context.get('active_id') and self._context.get('default_type'):
            mission = self.env['cim.mission'].browse(self._context['active_id'])
            result['mission_id'] = mission.mission_id.id
        return result
    
    motif_rejet_id = fields.Many2one('cim.motif.rejet', "Motif de rejet", index=True, required=True)
    mission_id = fields.Many2one('cim.mission', 'Mission', index=True)
    cocm_id = fields.Many2one('cim.cocm', 'COCM', index=True)
    description_rejet = fields.Text("Description")
    date_rejet = fields.Date('Date rejet')
    state_rejet_debut = fields.Selection(STATE_MISSION_REJET_SELECTION, string='Avant rejet', index=True, readonly=True, copy=False)
    state_rejet_fin = fields.Selection(STATE_MISSION_REJET_SELECTION, string='Après rejet', index=True, readonly=True, copy=False)
    type = fields.Selection([('mission', "Mission"),('cocm', "COCM")], string='Type')
    
    def action_confirm(self):
        vals = {
            'motif_rejet_id': self.motif_rejet_id.id,
            'mission_id': self.mission_id.id,
            'description_rejet': self.description_rejet,
            'date_rejet': self.date_rejet,
            'state_rejet_debut': self.state_rejet_debut,
            'state_rejet_fin': self.state_rejet_fin,
            'num_rejet': self.num_rejet
            }
        #self.env['cim.mission.rejet'].create(vals)
        if self.motif_rejet_id:
            self.env['cim.mission.rejet'].create(vals)
        else:
            raise ValidationError(_('Veuillez choisir un motif de rejet!'))
        return
    
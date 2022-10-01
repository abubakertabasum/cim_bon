# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import api, fields, models, _

STATE_COCM_SELECTION = [
    ('new', "Nouvelle"),
    ('initiation', "Initiée"),
    ('approbation', "Approuvée"), 
    ('budgeting', "Budgétisée"), 
    ('validate_sg', "Validée"),
    ('autorise', "Autorisée"),
    ('canceled', "Annulée")]

class COCM(models.Model):
    _name = 'cim.cocm'
    _inherit = 'cim.mission'
    _description = 'Communication Orale en Conseil des Ministres'
    
    name = fields.Char(string='N° COCM', readonly=True, track_visibility='onchange', copy=False)
    mission_type_id = fields.Many2one('cim.mission.type', string='Type de la mission', required=False)
    motif_mission_id = fields.Many2one('cim.motif.mission', string='Motif', required=True)
    object = fields.Text(string='Objet', required=True)
    project_id = fields.Many2one('cim.project', "Programme d'activités", required=True, track_visibility='onchange')
    state = fields.Selection(STATE_COCM_SELECTION, string='Statut', default='new', index=True, readonly=True, track_visibility='onchange', copy=False)
    itineraire_mission_ids = fields.One2many('cim.mission.itineraire','cocm_id', string='Itinéraires')
    participant_ids = fields.One2many('cim.mission.participant', 'cocm_id',string='Participants')
    date_creation = fields.Date(string='Date création', default=fields.Date.today(), required=True, track_visibility='onchange')
    date_autorisation = fields.Date(string='Date autorisation', track_visibility='onchange')
    type_ordre_mission_id = fields.Many2one('cim.type.ordre.mission', string="Type de l'ordre de mission", required=False)
    
    # pieces justificatives
    attachment_ids = fields.Many2many('ir.attachment', relation='cim_cocm_attachment_rel', string='Piéces justificatives')
    
    # Nombre de rejet
    rejet_ids = fields.One2many('cim.mission.rejet','cocm_id', string='Rejets')
    nbr_rejet = fields.Integer("Rejet", compute="_compute_nbr_rejet")
    
    
    def _compute_nbr_rejet(self):
        rejet_data = self.env['cim.mission.rejet'].sudo().read_group([('cocm_id', 'in', self.ids)], ['cocm_id'], ['cocm_id'])
        result = dict((data['cocm_id'][0], data['cocm_id_count']) for data in rejet_data)
        for cocm in self:
            cocm.nbr_rejet = result.get(cocm.id, 0)
    
    @api.model
    def create(self, vals):
        seq = self.env['ir.sequence'].next_by_code('cim.cocm.seq')
        seq = seq.replace("prefix1", str(self._get_prefix_structure(vals['company_id'])))
        seq = seq.replace("prefix2", str(self._get_prefix_service(vals['department_id'])))
        vals['name'] = seq
        return super(COCM, self).create(vals)
    
    @api.multi
    def act_check_budget(self):
        '''
        Check the budget
        '''
        for record in self:
            record.write({'state': 'budgeting'})
    
    @api.multi
    def act_autoriser_cocm(self):
        '''
        Check the budget
        '''
        if self.itineraire_mission_ids and self.participant_ids:
            for record in self:
                self.date_autorisation = fields.Date.today();
                record.write({'state': 'autorise'})
            
    @api.multi
    def act_launch_cocm(self):
        '''
        launch the cocm by the applicant
        '''
        if self.itineraire_mission_ids and self.participant_ids:            
            for record in self:
                record.write({'previous_state': record.state, 'state': 'initiation'})
                
    @api.multi
    def act_confirm_cocm(self):
        '''
        confirm the cocm by the applicant
        '''
        if self.itineraire_mission_ids and self.participant_ids:            
            for record in self:
                record.write({'previous_state': record.state, 'state': 'approbation'})
            
    @api.multi
    def act_budget_cocm(self):
        '''
        budget the cocm by the applicant
        '''
        if self.itineraire_mission_ids and self.participant_ids:            
            for record in self:
                record.write({'previous_state': record.state, 'state': 'budgeting'})
                
    @api.multi
    def act_validate_cocm(self):
        '''
        validate the cocm by the applicant
        '''
        if self.itineraire_mission_ids and self.participant_ids:            
            for record in self:
                record.write({'previous_state': record.state, 'state': 'validate_sg'}) 
                
                
    @api.multi
    def act_cancel_cocm(self):
        '''
        Cancel the cocm by the supervisor
        '''
        for record in self:
            record.write({'previous_state': record.state, 'state': 'canceled'})
            
    
    @api.multi
    def act_rejeter_cocm(self, rejet_id):
        '''
        Reject the COCM
        '''
        if rejet_id:
            print(rejet_id)
            cocm_rejet = self.env['cim.mission.rejet'].browse(rejet_id)
            print(cocm_rejet)
            cocm_rejet.write({'state_rejet_debut' : self.state})
        for state in STATE_COCM_SELECTION:
            if self.state == state[0]:
                index = STATE_COCM_SELECTION.index(state) - 1
                previous_state = STATE_COCM_SELECTION[index][0]
                cocm_rejet.write({'state_rejet_fin' : previous_state})
                self.write({'state': previous_state})
    
    
                
                

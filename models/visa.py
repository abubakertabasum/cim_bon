# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class Visa(models.Model):
    _name = 'cim.visa'
    _description = 'Visa'
    _rec_name = 'num_om'
    
    def _default_employee(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
    
    num_om = fields.Char('N° OM', related='participant_id.num_om')
    participant_id = fields.Many2one('cim.mission.participant', "Agent", required=True)
    mission_id = fields.Many2one('cim.mission', "Mission", related='participant_id.mission_id')
    loc_id = fields.Many2one("cim.mission.itineraire", string="Localité", required=True)
    type = fields.Selection([('entrer', 'Entrée'),('sortie', 'Sortie')], 'Type', required=True, default='entrer')
    date_visa = fields.Date(string='Date', default=fields.Date.today(), required=True)
    employee_id = fields.Many2one('hr.employee', string='Créer par', index=True, default=_default_employee)
    nom_autorite = fields.Char("Nom de l'autorité", required=True)
    
    @api.model
    def create(self, vals):
        loc_id = vals.get('loc_id', False)
        type = vals.get('type', False)
        if loc_id and self._context.get('default_participant_id'):
            participant = self.env['cim.mission.participant'].browse(self._context.get('default_participant_id'))
            visa = self.env['cim.visa'].search([('mission_id','=', participant.mission_id.id),
                                                ('loc_id','=', loc_id),
                                                ('type','=', type)])
            if visa:
                raise ValidationError(_('Un visa a déjà été enregistré pour cette localité en %s' %(type)))
        return super(Visa, self).create(vals)
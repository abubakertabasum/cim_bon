# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PaiementParticipant(models.TransientModel):
    _name = 'paiement.participant.wizard'
    _description = 'Paiement Participant Wizard'
    
    @api.model
    def default_get(self, fields):
        
        result = super(PaiementParticipant, self).default_get(fields)
        if self._context.get('active_id') and self._context.get('default_type'):
            participant = self.env['cim.mission.participant'].browse(self._context['active_id'])
            result['participant_id'] = participant.id
            result['mission_id'] = participant.mission_id.id
            frais = self.env['cim.expense'].search([('mission_id','=', participant.mission_id.id),('employee_id','=',participant.participant_id.id)])
            result['frais_ids'] = [(6, 0, frais.ids)]
            paiements = self.env['cim.paiement.participant'].search([('mission_id','=', participant.mission_id.id),('participant_id','=',participant.participant_id.id)])
            if paiements:
                result['have_payment'] = True
                if self._context.get('default_type') == 'frais':
                    montant_paye = sum(item.montant_paye for item in paiements)
                    result['montant_a_payer'] = sum(item.total_amount for item in frais) - montant_paye
                elif self._context.get('default_type') == 'remboursement':
                    result['montant_a_payer'] = participant.trop_percu
            else:
                result['montant_a_payer'] = sum(item.total_amount for item in frais)
        return result
    
    participant_id = fields.Many2one('cim.mission.participant', 'Participant', readonly=True)
    mission_id = fields.Many2one('cim.mission', 'Mission', index=True, readonly=True)
    frais_ids = fields.Many2many('cim.expense', string='Frais', readonly=True)
    frais_total = fields.Monetary(string='Montant Total', currency_field='currency_id', compute='_compute_frais_total')
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True, default=lambda self: self.env.user.company_id.currency_id)
    montant_a_payer = fields.Monetary(string='Montant à payer', currency_field='currency_id', readonly=True)
    montant_paye = fields.Monetary(string='Montant payé', currency_field='currency_id', required=True)
    reste_a_payer = fields.Monetary(string='Reste à payer', currency_field='currency_id', compute='_compute_reste_a_payer')
    date_paiement = fields.Date('Date paiement', default=fields.Date.today(), required=True)
    have_payment = fields.Boolean('Avoir un paiement')
    type = fields.Selection([('frais', 'Indemnités de mission'),
                             ('remboursement', 'Remboursement'),
                             ('complement', 'Complement')], 'Type', default='frais')
    
    @api.one
    @api.depends('frais_ids.total_amount')
    def _compute_frais_total(self):
        self.frais_total = sum(item.total_amount for item in self.frais_ids)
    
    @api.one
    @api.depends('frais_ids.total_amount','montant_paye')
    def _compute_reste_a_payer(self):
        self.reste_a_payer = self.montant_a_payer - self.montant_paye
        
    
    def action_confirm(self):
        vals = {
            'participant_id': self.participant_id.participant_id.id,
            'mission_id': self.mission_id.id,
            'currency_id': self.currency_id.id,
            'montant_a_payer': self.montant_a_payer,
            'montant_paye': self.montant_paye,
            'reste_a_payer': self.reste_a_payer,
            'date_paiement': self.date_paiement,
            'type': self.type
            }
        self.env['cim.paiement.participant'].create(vals)
        if self.montant_paye != 0.0:
            if self.type == 'remboursement':
                if self.montant_paye == self.montant_a_payer:
                    self.participant_id.write({'is_refunded': True})
                else:
                    raise ValidationError(_('Il faut payer tout le montant!'))
            elif self.type == 'frais': 
                if self.montant_paye == self.montant_a_payer:
                    if self.participant_id.state == 'checked':
                        self.participant_id.write({'is_paid': True})
                    else:
                        self.participant_id.write({'state': 'paid'})
                elif (self.montant_paye > self.montant_a_payer):
                    raise ValidationError(_('Veuillez verifier le montant payé!'))
        else:
            raise ValidationError(_('Veuillez verifier le montant payé!'))
        return
    
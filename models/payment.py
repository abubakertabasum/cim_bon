# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class PaiementParticipant(models.Model):
    _name = 'cim.paiement.participant'
    _description = 'Paiement de participant'
    
    participant_id = fields.Many2one('hr.employee', "Participant")
    mission_id = fields.Many2one('cim.mission', 'Mission', index=True)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True, default=lambda self: self.env.user.company_id.currency_id)
    montant_a_payer = fields.Monetary(string='Montant à payer', currency_field='currency_id', required=True)
    montant_paye = fields.Monetary(string='Montant payé', currency_field='currency_id', required=True)
    reste_a_payer = fields.Monetary(string='Reste à payer', currency_field='currency_id', required=True)
    date_paiement = fields.Date('Date paiement')
    type = fields.Selection([('frais', 'Indemnités de mission'),
                             ('remboursement', 'Remboursement'),
                             ('complement', 'Complement')], 'Type', default='frais')
    
    
    
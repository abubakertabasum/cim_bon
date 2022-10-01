# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class VerificationParticipant(models.TransientModel):
    _name = 'verification.participant.wizard'
    _description = 'Vérification Participant Wizard'
    
    @api.model
    def default_get(self, fields):
         
        result = super(VerificationParticipant, self).default_get(fields)
        
        if self._context.get('active_id'):
            participant = self.env['cim.mission.participant'].browse(self._context['active_id'])
            result['participant_id'] = participant.id
            result['matricule'] = participant.matricule
            result['work_phone'] = participant.work_phone
            result['company_id'] = participant.company_id.id
            result['department_id'] = participant.department_id.id
            result['role_mission_id'] = participant.role_mission_id.id
            result['est_pec'] = participant.est_pec
            
            result['mission_id'] = participant.mission_id.id
            
            result['itineraire_prevu_ids'] = [(6, 0, participant.mission_id.itineraire_mission_ids.ids)]
            
            frais = self.env['cim.expense'].search([('mission_id','=', participant.mission_id.id),('employee_id','=',participant.participant_id.id)])
            result['frais_mission'] = sum(item.total_amount for item in frais)
            
            frais_paye = self.env['cim.paiement.participant'].search([('mission_id','=', participant.mission_id.id),('participant_id','=',participant.participant_id.id)])
            result['frais_paye'] = sum(item.montant_paye for item in frais_paye)
            
            itineraires = []
            for loc in participant.mission_id.itineraire_mission_ids:
                vals = {'loc_id': loc.loc_id.id,
                       'depart': loc.depart,
                       'date_arrivee': loc.date_arrivee,
                       'duree': loc.duree,
                       'description': loc.description}
                reel = self.env['itineraire.reel.wizard'].create(vals)
                itineraires.append(reel.id)
            result['itineraire_reel_ids'] =  [(6, 0, itineraires)]
#             obj = []
#             for pj in participant.company_id.pj_ids:
#                 print (pj)
#                 obj.append((0,0,{'nature_pj_id': pj.id, 'is_exist': False}))
#                 print(obj)
#
#             result['pj_ids'] = obj
            
        return result
    
    num_om = fields.Char('N° OM')
    participant_id = fields.Many2one('cim.mission.participant', "Participant", readonly=True)
    matricule = fields.Char('Matricule', readonly=True)
    work_phone = fields.Char('Télephone', readonly=True)
    company_id = fields.Many2one('res.company', string='Structure', readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True, default=lambda self: self.env.user.company_id.currency_id)
    department_id = fields.Many2one('hr.department', 'Service', readonly=True)
    role_mission_id = fields.Many2one('cim.role.mission', 'Rôle', readonly=True)
    mission_id = fields.Many2one('cim.mission', 'Mission', readonly=True)
    mission_type_id = fields.Many2one('cim.mission.type', string='Type de la mission', related='mission_id.mission_type_id')
    est_pec = fields.Boolean('Est PEC', readonly=True)
    
    itineraire_prevu_ids = fields.Many2many('cim.mission.itineraire', relation='verification_itineraire_prevu_rel', string='Itinéraires prévus', readonly=True)
    frais_mission = fields.Monetary(string='Frais de mission', currency_field='currency_id', readonly=True)
    frais_paye = fields.Monetary(string='Frais payé', currency_field='currency_id', readonly=True)
    
    itineraire_reel_ids = fields.Many2many('itineraire.reel.wizard', string='Itinéraires réels')
    frais_reel_participant_ids = fields.Many2many('frais.reel.participant.wizard', 'frais_reel_verification_participant_wizard_rel', string="Frais réel de participant", compute="_compute_frais_reel_participant", store=True)
    
    duree_reel = fields.Integer(string='Durée réelle (en jour)', compute="_compute_duree", store=True)
    observation = fields.Text(string='Observation')
    frais_reel = fields.Monetary(string='Frais réel', currency_field='currency_id', compute='_compute_frais_reel', store=True)
    trop_percu = fields.Monetary(string='Trop perçu', currency_field='currency_id', compute='_compute_ecart', store=True)
    reste_a_paye = fields.Monetary(string='Reste à payer', currency_field='currency_id', compute='_compute_ecart', store=True)
    
    #pj_ids = fields.One2many('res.config.settings', 'pj_ids', string='Pièces justificatives')
    pj_ids = fields.One2many('pj.participant.wizard', 'verification_participant_id', string='Pièces justificatives')
    
    @api.one
    @api.depends('itineraire_reel_ids','itineraire_prevu_ids')
    def _compute_duree(self):
        self.duree_reel = sum(itineraire.duree for itineraire in self.itineraire_reel_ids)
    
    
    @api.one
    @api.depends('frais_mission','frais_reel')
    def _compute_ecart(self):
        ecart = self.frais_paye - self.frais_reel
        if ecart <= 0:
            self.reste_a_paye = abs(ecart)
        else:
            self.trop_percu = ecart
    
    @api.one
    @api.depends('itineraire_reel_ids.duree')
    def _compute_frais_reel_participant(self):
        obj = []
        for itineraire in self.itineraire_reel_ids:
            if not itineraire.depart:
                products = self.mission_id._get_expense_product_of_employee(self.participant_id.participant_id, itineraire.loc_id.zone_mission_id)
                for product in products:
                    if product.product_tmpl_id.id == self.env.ref('cim.cim_expense_product_accommodation').id:
                        quantity = itineraire.duree - 1
                    else:
                        quantity = itineraire.duree
                    vals = {
                            'name' : '%s (%s)' %(itineraire.loc_id.name,product.name) ,
                            'product_id': product.id,
                            'unit_amount' : product.standard_price,
                            'quantity' : quantity,
                            'total_amount': product.standard_price * quantity,
                        }
                    obj.append((0,0,vals))
        
        if self.company_id.auto_compute_carb and self.participant_id.role_mission_id.code == 'M':
            montant_carburant = sum(item.montant_carb_mission for item in self.mission_id.vehicule_mission_ids)
            vals_car = {
                    'name' : 'Frais Carburant',
                    'unit_amount' : montant_carburant,
                    'total_amount': montant_carburant,
                }
            obj.append((0,0,vals_car))
        
        self.frais_reel_participant_ids = obj
    
    @api.one
    @api.depends('frais_reel_participant_ids.total_amount')
    def _compute_frais_reel(self):
        self.frais_reel = sum(frais.total_amount for frais in self.frais_reel_participant_ids)
    
    
    def action_confirm(self):
        itineraires = []
        new_pj = []
        current_user = self.env.user.id
        list_pj_config = []
        list_pj_wizard = []
        for pj_id in self.pj_ids:
            list_pj_wizard.append(pj_id.nature_pj_id.id)
        for pj in self.env['res.users'].browse(current_user).company_id.pj_ids:
            list_pj_config.append(pj.id)
        if self.pj_ids:
            if list_pj_wizard == list_pj_config:
                for loc_reel,loc_prevu in zip(self.itineraire_reel_ids,self.itineraire_prevu_ids):
                    vals = {'loc_id': loc_reel.loc_id.id,
                       'depart': loc_reel.depart,
                       'date_arrivee': loc_reel.date_arrivee,
                       'duree': loc_reel.duree,
                       'description': loc_reel.description,
                       'participant_id': self.participant_id.id}
                    itineraires.append((0,0, vals))
                    if self.mission_type_id.id  == self.env.ref('cim.data_mission_type_external').id:
                        vals = {
                            'duree_reel': self.duree_reel,
                            'frais_reel': self.frais_reel,
                            'trop_percu': self.trop_percu,
                            'reste_a_paye': self.reste_a_paye,
                            'observation': self.observation,
                            'pj_ids': new_pj,
                            'state': 'checked',
                            }
                        self.participant_id.write(vals)
                        for frais in self.frais_reel_participant_ids:
                            expense = self.env['cim.expense'].search([('employee_id', '=', self.participant_id.participant_id.id),
                                                                      ('product_id', '=', frais.product_id.id),
                                                                      ('mission_id', '=', self.mission_id.id),
                                                                      ('other', '=', False)])
                            if frais.total_amount != expense.total_amount:
                                expense.write({'unit_amount' : frais.unit_amount,'quantity' : frais.quantity, 'total_amount': frais.total_amount})
                            
                    else:
                        # condition sur les missions internes
                        if loc_prevu.duree < loc_reel.duree:
                            raise ValidationError(_('La durée réelle doit être inférieure ou égale à la durée prévue!'))
                        else:
                            vals = {
                                'duree_reel': self.duree_reel,
                                'frais_reel': self.frais_reel,
                                'trop_percu': self.trop_percu,
                                'observation': self.observation,
                                'pj_ids': new_pj,
                                'state': 'checked',
                                }
                            self.participant_id.write(vals)
                self.sudo().participant_id.itineraire_reel_ids.unlink()
                self.participant_id.write({'itineraire_reel_ids': itineraires})   
            else:
                raise ValidationError(_('Il faut ajouter les mêmes pièces justificatives de la configuration!'))
        else:
            raise ValidationError(_('Il faut remplir les pièces justificatives!'))

        return


class ItineraireReel(models.TransientModel):
    _name = 'itineraire.reel.wizard'
    _description = 'Itinéraire réel de participant'
    _rec_name = 'loc_id'

    
    loc_id = fields.Many2one("cim.localite", string="Localité", required=True, store=True)
    depart = fields.Boolean("Départ")
    date_arrivee = fields.Date(string="Date d'arrivée", default=fields.Date.today(), required=False)
    duree = fields.Integer(string="Durée (en jour)")
    description = fields.Char(string='Description')
             

class FraisReelParticipant(models.TransientModel):
    _name = 'frais.reel.participant.wizard'
    _description = 'Frais reel de participant Wizard'
    
    name = fields.Char(string="Elément de dépense", readonly=True)
    product_id = fields.Many2one('product.product', string='Elément de dépense')
    quantity = fields.Float(string="Quantité", readonly=True, default=1)
    unit_amount = fields.Float("Montant unitaire", readonly=True)
    total_amount = fields.Float("Montant total", readonly=True)

class PJParticipant(models.TransientModel):
    _name = 'pj.participant.wizard'
    _description = 'PJ de participant Wizard'
    _rec_name = 'nature_pj_id'
    
    @api.multi
    def _get_domain_nature_pj(self):
        if self.env.user.company_id:
            return [('id', 'in', self.env.user.company_id.pj_ids.ids)]

    nature_pj_id = fields.Many2one('cim.nature.pj', string='Nature PJ', domain=_get_domain_nature_pj, required=True)
    is_exist = fields.Boolean('Existe') 
    verification_participant_id = fields.Many2one('verification.participant.wizard', string='Participant')
    
    
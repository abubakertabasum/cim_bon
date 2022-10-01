# -*- coding: utf-8 -*-

import logging
from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from num2words import num2words
import collections

_logger = logging.getLogger(__name__)


STATE_MISSION_SELECTION = [
    ('new', "Demande"),
    ('initiation', "Initié"),
    ('approbation', "Approuvé"), 
    ('budgeting', "Budgétisé"), 
    ('validate_sg', "Validé"),
    ('daf_payment', "Payé"),
    ('checked', "Vérifié"),  
    ('done', "Clôturé"),
    ('canceled', "Annulé")]

STATE_MISSION_EVALUATION = [
    ('new_eval', "En saiaie"),
    ('validated_eval', "Evaluée")]

STATE_MISSION_RAPPORT = [
    ('new_rapport', "En saiaie"),
    ('validated_rapport', "Validé")]


class Mission(models.Model):
    _name = 'cim.mission'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Mission'
    _order = "create_date desc, id desc"
    
    @api.model
    def _default_department(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1).department_id
    
    @api.model
    def _default_employee(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
    
    @api.model
    def _default_loc_depart(self):
        return self.env['res.company'].search([('id','=',self.env.user.company_id.id)]).localite_id

    @api.model
    def _default_exercice_budgetaire(self):
        return self.env['cim.exercice.budgetaire'].search([('state','=','execution'),('active','=',True)], limit=1)
    
    name = fields.Char(string='Projet de mission n° ', readonly=True, track_visibility='onchange', copy=False)
    num_demande = fields.Char(string='N° demande', readonly=True, copy=False)
    num_mission = fields.Char(string='N° Mission', readonly=True, copy=False)
    default_name = fields.Char(string='N° Mission', readonly=True, copy=False)
    object = fields.Text(string='Objet de la mission', required=True)
    description = fields.Text(string='Description')
    date_from = fields.Date(string='Date début', default=fields.Date.today(), required=True, track_visibility='onchange')
    date_to = fields.Date(string='Date fin', default=fields.Date.today(), required=True, track_visibility='onchange')
    mission_type_id = fields.Many2one('cim.mission.type', string='Type de la mission', required=False)
    motif_mission_id = fields.Many2one('cim.motif.mission', string='Motif de mission', required=True)
    department_id = fields.Many2one('hr.department', string='Service demandeur', default=_default_department, required=True)
    participant_ids = fields.One2many('cim.mission.participant', 'mission_id',string='Participants')
    
    #évaluation des missions
    evaluation_ids = fields.One2many('cim.mission.evaluation', 'mission_id',string='Evaluation')
    taux_moyen = fields.Float(string="Taux moyen de l'évaluation", readonly=True, compute='_compute_taux_moyen', store=True)
    state_eval = fields.Selection(STATE_MISSION_EVALUATION, string='Evaluation', default='new_eval', index=True, readonly=True, track_visibility='onchange', copy=False)
    #critere_evaluation_ids = fields.One2many('cim.mission.evaluation', 'mission_id',string="Critère d'évaluation")
    
    #Objectifs des missions
    objectif_missions = fields.One2many('cim.mission.objectif', 'mission_id',string='Objectifs à atteindre')
    sondage_objectif = fields.Float(string="Objectifs atteints à", readonly=True, compute='_compute_taux_objectif', store=True)
        
    state_rapport = fields.Selection(STATE_MISSION_RAPPORT, string='Rapport', default='new_rapport', index=True, readonly=True, track_visibility='onchange', copy=False)
    
    establishment_id = fields.Many2one('res.company', string='Structure', related='company_id', readonly=False, track_visibility='onchange')
    project_id = fields.Many2one('cim.project', "Programme d'activités", required=True, track_visibility='onchange', domain="[('state', '=', 'validated')]")
    
    #Ajout des elements du calcul de la disponibilité des crédits des lignes budgétaires
    sectionbudgetaire_id = fields.Many2one('cim.sectionbudgetaire', "Section budgétaire")
    programmechapitre_id = fields.Many2one('cim.programmechapitre', "Programme/Chapitre")
    actionarticle_id = fields.Many2one('cim.actionarticle', "Action/Article")
    activiteparagraphe_id = fields.Many2one('cim.activiteparagraphe', "Activite/Paragraphe")
    paragrapherubrique_id = fields.Many2one('cim.paragrapherubrique', "Paragraphe/Rubrique")
    exercice_id = fields.Many2one('cim.exercice.budgetaire', string='Exercice budgetaire', default=_default_exercice_budgetaire, track_visibility='onchange')
    
    active = fields.Boolean('Active', default=True) 
    state = fields.Selection(STATE_MISSION_SELECTION, string='Statut', default='new', index=True, readonly=True, track_visibility='onchange', copy=False)
    
    company_id = fields.Many2one('res.company', string='Structure', default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one('res.currency', string='Devise', default=lambda self: self.env.user.company_id.currency_id)
    is_paid = fields.Boolean(string="Payé")
    
    #vehicules
    vehicule_mission_ids = fields.One2many('cim.mission.vehicule','mission_id', string='Vehicules')
    total_carb_mission = fields.Monetary(string='Total Carburant Mission', store=True, currency_field='currency_id', compute='_compute_total_carb_mission')
    
    #Frais de mission
    frais_ids = fields.One2many('cim.expense', 'mission_id', string='Frais de mission', domain=lambda self: [('other', '=', False)])
    
    #autre Frais
    other_frais_ids = fields.One2many('cim.expense', 'mission_id', string='Autre frais', domain=lambda self: [('other', '=', True)])
    
    frais_mission_total = fields.Monetary(string='Montant total des frais',
        store=True, currency_field='currency_id', readonly=True, compute='_compute_total')
    total_lettre = fields.Char("Total lettré", compute="_lettrer_frais_mission_total")
    
    total_only_frais_mission = fields.Monetary(string='Montant total des frais', store=True, currency_field='currency_id', readonly=True, compute='_compute_total_fm')
    
    with_financial_impact = fields.Boolean("Avec incidence financière", default=True)
    is_auto = fields.Boolean("Auto", related="establishment_id.auto_number_mission")
    is_draft = fields.Boolean("is draft", default=True)
    
    # duree de la mission
    duree_mission = fields.Integer(string="Durée (en jour)", compute="_compute_duree_mission", store=True)
    
    # Itinéraire
    loc_depart = fields.Many2one("cim.localite", string="Départ", required=False, default=_default_loc_depart)
    loc_destination = fields.Many2one("cim.localite", string="Destination", required=False)
    itineraire_mission_ids = fields.One2many('cim.mission.itineraire','mission_id', string='Itinéraires')
    distance_mission = fields.Float(string="Distance (en km)", compute="_compute_distance_mission", store=True)
    duree_total_itineraire = fields.Integer(string="Durée (en jour)", compute="_compute_duree_total_itineraire", store=True)
    
    # pieces justificatives
    attachment_ids = fields.Many2many('ir.attachment', relation='cim_mission_attachment_rel', string='Piéces justificatives')
    
    # budget_line
    budget_line_id = fields.Many2one('cim.budget.line', string="Budget", compute="_compute_budget_line_id", store=True)
    credit_dispo = fields.Monetary(string='Crédits disponibles', store=True, currency_field='currency_id', compute='_compute_credits_disponibles')
    
    # Paiement
    paiement_ids = fields.One2many('cim.paiement.participant', 'mission_id', string="Paiements")
    montant_total_paye = fields.Monetary(string='Montant total payé', store=True, currency_field='currency_id', compute='_compute_montant_total_paye')
    
    # Bailleur
    bailleur_id = fields.Many2one('cim.bailleur', string='Bailleur')
    
    # COCM
    cocm_id = fields.Many2one('cim.cocm', string='COCM', index=True, track_visibility='onchange')
    cocm = fields.Boolean(string='COCM', related='company_id.company_type_id.cocm', store=True)
    
    # Previous status
    previous_state = fields.Char("Statut précédent", readonly=True)
    
    #champs pour le rapport de synthèse
    rs_redacteur = fields.Many2one('hr.employee', string='Rédacteur')
    rs_resume = fields.Text(string='Résumé succint de la mission')
    rs_enseignements = fields.Text(string='Enseignements de la mission')
    rs_limites = fields.Text(string='Limites de la mission')
    rs_suggestions = fields.Text(string='Suggestions pour la prochaine fois')
    
    #Relation avec les ordres de missions
    ordre_mission_ids = fields.One2many('cim.ordre.mission', 'mission_id',string='Ordre de mission')
    type_ordre_mission_id = fields.Many2one('cim.type.ordre.mission', string="Type de l'ordre de mission", required=True)
    
    
    # Nombre de rejet
    rejet_ids = fields.One2many('cim.mission.rejet','mission_id', string='Rejets')
    nbr_rejet = fields.Integer("Rejet", compute="_compute_nbr_rejet")
    
    # Initiateur
    employee_id = fields.Many2one('hr.employee', string='Initiateur', index=True, default=_default_employee)
    
    # signataires
    signataire1_id = fields.Many2one('hr.employee', string='Signataire 1', index=True)
    signataire2_id = fields.Many2one('hr.employee', string='Signataire 2', index=True)
    
    def _compute_nbr_rejet(self):
        rejet_data = self.env['cim.mission.rejet'].sudo().read_group([('mission_id', 'in', self.ids)], ['mission_id'], ['mission_id'])
        result = dict((data['mission_id'][0], data['mission_id_count']) for data in rejet_data)
        for mission in self:
            mission.nbr_rejet = result.get(mission.id, 0)
    
    @api.one
    @api.depends('evaluation_ids.taux_evaluation')
    def _compute_taux_moyen(self):
        size = len(self.evaluation_ids)
        if size > 0:
            self.taux_moyen = sum(taux.taux_evaluation for taux in self.evaluation_ids) / size

    @api.one
    @api.depends('objectif_missions')
    def _compute_taux_objectif(self):
        size_objectif = len(self.objectif_missions)
        if size_objectif > 0:
            objectifatteint = len(self.objectif_missions.filtered(lambda o: o.objectif_atteint == True))
            moyenneatteint = (objectifatteint/size_objectif)*100
            self.sondage_objectif = moyenneatteint 
        else:
            self.sondage_objectif = 0

    @api.one
    @api.depends('vehicule_mission_ids.montant_carb_mission')
    def _compute_total_carb_mission(self):
        if self.with_financial_impact:
            self.total_carb_mission = sum(item.montant_carb_mission for item in self.vehicule_mission_ids)
        else:
            self.total_carb_mission = 0
        
    
    def _get_distance_ab(self, loc_depart, loc_destination):
        distance = self.env['cim.distance.localite'].search([('loc_a_id', '=', loc_depart.id),('loc_b_id', '=', loc_destination.id)], limit=1)
        if not distance:
            distance = self.env['cim.distance.localite'].search([('loc_a_id', '=', loc_destination.id),('loc_b_id', '=', loc_depart.id),('distance_symetrique', '=', True)], limit=1)
        return distance.distance_ab
    
    @api.one
    @api.depends('itineraire_mission_ids.loc_id')
    def _compute_distance_mission(self):
        distance = 0
        size = len(self.itineraire_mission_ids.ids)
        if size > 0:
            for index, value in enumerate(self.itineraire_mission_ids):
                if size > index+1:
                    loc_a = value.loc_id
                    loc_b = self.itineraire_mission_ids[index + 1].loc_id
                    distance = distance + self._get_distance_ab(loc_a,loc_b)
            loc_a = self.itineraire_mission_ids[size-1].loc_id
            loc_b = self.itineraire_mission_ids[0].loc_id
            
            distance = distance + self._get_distance_ab(loc_a, loc_b)
            self.distance_mission = distance
        
         
    @api.one
    @api.depends('paiement_ids.montant_paye')
    def _compute_montant_total_paye(self):
        self.montant_total_paye = sum(item.montant_paye for item in self.paiement_ids)
    
    
    @api.one
    @api.depends('exercice_id','project_id','sectionbudgetaire_id','programmechapitre_id','actionarticle_id','activiteparagraphe_id','paragrapherubrique_id')
    def _compute_budget_line_id(self):
        if self.exercice_id and self.project_id and self.sectionbudgetaire_id and self.programmechapitre_id and self.actionarticle_id and self.activiteparagraphe_id and self.paragrapherubrique_id:
            self.credit_dispo = self.budget_line_id.credit_dispo 
            exercice = self.exercice_id.id 
            projet = self.project_id.id
            section = self.sectionbudgetaire_id.id
            programme = self.programmechapitre_id.id
            action = self.actionarticle_id.id
            activite = self.activiteparagraphe_id.id
            paragraphe = self.paragrapherubrique_id.id
            structure = self.env.user.company_id
            if exercice and projet and section and programme and action and activite and paragraphe:
                budget_line = self.env['cim.budget.line'].search([('exercice_id','=', exercice),('programme_id','=', projet),('sectionbudgetaire_id','=', section),('programmechapitre_id','=', programme),('actionarticle_id','=', action),('activiteparagraphe_id','=', activite),('paragrapherubrique_id','=', paragraphe)], limit=1)
                self.budget_line_id = budget_line.id
                self.credit_dispo = budget_line.credit_dispo
    
    @api.one
    @api.depends('project_id')
    def _compute_credits_disponibles(self):
        if self.project_id:
            self.credit_dispo = self.budget_line_id.credit_dispo  

    @api.one
    @api.depends('date_from','date_to')
    def _compute_duree_mission(self):
        duree = self.date_to - self.date_from
        self.duree_mission = duree.days + 1
        

    @api.one
    @api.depends('itineraire_mission_ids')
    def _compute_duree_total_itineraire(self):
        duree = 0
        if self.itineraire_mission_ids :            
            for itineraire in self.itineraire_mission_ids :
                duree = duree + itineraire.duree
        self.duree_total_itineraire = duree

    @api.one
    @api.constrains('duree_total_itineraire','duree_mission')
    def _check_duree_total_itineraire(self):
        if self.duree_total_itineraire > self.duree_mission: 
            raise ValidationError(_("La durée totale de l'itinéraire est supérieure à la durée de la mission!"))

    
    @api.one
    @api.constrains('date_from','date_to')
    def _check_date_mission(self):
        participants = self.participant_ids
        date_from = self.date_from
        date_to = self.date_to
        year_from = int(self.date_from.year)
        year_to = int(self.date_to.year)
        budget_year = self.env['cim.exercice.budgetaire'].sudo().search([('state','=','execution'),('active','=',True)], limit=1).name
        if year_from != int(budget_year) or year_to != int(budget_year):
            raise ValidationError(_("La période de la mission ne doit pas être antérieur à l'Exercice budgétaire!"))
        if date_from > date_to:
            raise ValidationError(_('La date de départ doit être inférieure ou égale date de retour.'))
        if participants:
            for participant in participants:
                query = """
                        SELECT count(DISTINCT id)
                        FROM cim_mission_participant WHERE participant_id = (SELECT id FROM hr_employee WHERE id=%s)
                        and mission_id in (SELECT id FROM cim_mission WHERE state <> 'canceled' and date_from <= '%s'::date and date_to > '%s'::date);
                    """ %(participant.participant_id.id,self.date_to,self.date_from)
                self._cr.execute(query)
                count = self._cr.dictfetchall()
                if count[0]['count'] > 1:
                    raise ValidationError(_("%s ne peut pas participer à plusieurs missions pendant la même période!" %(participant.participant_id.name)))
    
    @api.one
    @api.constrains('duree_mission')
    def _check_duree_mission(self):
        if (self.mission_type_id.nbr_jours_max != 0) and (self.duree_mission > self.mission_type_id.nbr_jours_max):
            raise ValidationError(_('La durée autorisée pour ce type de mission est de %s jours.' %(self.mission_type_id.nbr_jours_max)))
    
    @api.one
    @api.constrains('vehicule_mission_ids')
    def _check_nombre_vehicule(self):
        vehicules = self.vehicule_mission_ids
        if vehicules:
            place_count = 0
            for vehicule in vehicules:
                place_count = place_count + vehicule.vehicule_id.seats
            agent_count = len(self.participant_ids.ids)
            if place_count < agent_count:
                raise ValidationError(_("Le nombre total de places est inférieur au nombre total des participants!"))
            if len(vehicules) > 1:
                list_passager = []
                for vehicule in vehicules:
                    for passager in vehicule.passager_ids:
                        list_passager.append(passager)
                if [item for item, count in collections.Counter(list_passager).items() if count > 1]:
                    raise ValidationError(_("Un agent ne peut pas être à la fois dans plusieurs véhicules"))
                
    @api.one
    @api.depends('frais_ids.total_amount','other_frais_ids.total_amount')
    def _compute_total(self):
        expense_total = sum(line.total_amount for line in self.frais_ids)
        other_expense_total = sum(line.total_amount for line in self.other_frais_ids) 
        self.frais_mission_total = expense_total + other_expense_total

    @api.model
    def _compute_other_frais_total(self, employee_id):
        return sum(line.total_amount for line in self.other_frais_ids.filtered(lambda f: f.employee_id.id == employee_id))

    @api.model
    @api.depends('participant_ids.montant_total')
    def _compute_frais_mission_total_agent(self, employee_id):
        return sum(line.total_amount for line in self.frais_ids.filtered(lambda f: f.employee_id.id == employee_id))

    
    @api.one
    @api.depends('frais_mission_total')
    def _compute_total_fm(self):
        self.total_only_frais_mission = sum(line.total_amount for line in self.frais_ids)
#     def _compute_total_fm(self):
#         self.total_only_frais_mission = self.frais_mission_total - self.total_carb_mission
#     
    
    def _get_prefix_structure(self, company_id):
        return self.env['res.company'].search([('id', '=', company_id)]).prefix
    
    def _get_prefix_service(self, department_id):
        return self.env['hr.department'].search([('id', '=', department_id)]).prefix   

    @api.model
    def create(self, vals):
        if self._name != 'cim.cocm':
#             seq = self.env['ir.sequence'].next_by_code('cim.name.mission.seq')
#             vals['default_name'] = seq
#             vals['name'] = seq
            
            seq = self.env['ir.sequence'].next_by_code('cim.dmd.mission.seq')
            seq = seq.replace("prefix1", self.env.user.company_id.prefix )
            seq = seq.replace("prefix2", self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1).department_id.prefix  )
            vals['default_name'] = seq
            vals['name'] = seq
            vals['num_demande'] = seq
            
            vals['distance_mission'] = self._compute_distance_mission()
            vals['total_carb_mission'] = self._compute_total_carb_mission()
            vals['credit_dispo'] = self._compute_credits_disponibles()
            
        return super(Mission, self).create(vals)
    
    @api.model
    def edit(self, vals):
        vals['distance_mission'] = self._compute_distance_mission()
        vals['total_carb_mission'] = self._compute_total_carb_mission()
        vals['credit_dispo'] = self._compute_credits_disponibles()
        vals['frais_mission_total'] = self._compute_total()
        vals['total_only_frais_mission'] = self._compute_total_fm()
        return super(Mission, self).edit(vals)
    
    @api.multi
    def act_launch_mission(self, vals):
        '''
        launch the mission by the applicant
        '''
        if self.itineraire_mission_ids and self.participant_ids:      
            if self.mission_type_id.id == self.env.ref('cim.data_mission_type_external').id:
                if not self.cocm_id and self.cocm: 
                    return {
                        'name': 'Initiation COCM',
                        'view_mode': 'form',
                        'view_type': 'form',
                        'res_model': 'initiation.cocm.wizard',
                        'type': 'ir.actions.act_window',
                        'target': 'new',
                        }
            
            if self.num_demande == False:
                seq = self.env['ir.sequence'].next_by_code('cim.dmd.mission.seq')
                seq = seq.replace("prefix1", self.env.user.company_id.prefix )
                seq = seq.replace("prefix2", self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1).department_id.prefix)
                self.num_demande = seq
                self.name = seq
            else:
                self.name = self.num_demande
            self.write({'state': 'initiation'})
            self.sudo().activity_update()
        else:
            raise ValidationError(_("Veuillez remplir les champs obligatoires! Notamment, l'itinéraire et les participants"))
    
    
    def _get_expense_product_of_employee(self, employee, zone):
#         zone_id = self.loc_destination.zone_mission_id
        categ_id = employee.categ_id
        attribute_value = self.env['product.attribute.value'].search(['|',('name','=', categ_id.name),('name','=', zone.name)])
        products = self.env['product.product'].search([('attribute_value_ids','in', attribute_value.ids[0]),('attribute_value_ids','in', attribute_value.ids[1])])
        return products
    
    
    @api.multi
    def act_confirm_mission(self):
        '''
        Confirm the mission by the applicant
        '''
        for record in self:
            if record.with_financial_impact:
                for participant in record.participant_ids:
                    if participant.est_pec:
                        for itineraire in self.itineraire_mission_ids:
                            if not itineraire.depart:
                                if itineraire.duree > 0:
                                    products = self._get_expense_product_of_employee(participant.participant_id, itineraire.loc_id.zone_mission_id)
                                    for product in products:
                                        if product.product_tmpl_id.id == self.env.ref('cim.cim_expense_product_accommodation').id and itineraire.fin:
                                            quantity = itineraire.duree - 1
                                        else:
                                            quantity = itineraire.duree
                                        vals = {
                                                'name' : '%s (%s)' %(itineraire.loc_id.name,product.name) ,
                                                'product_id' : product.id,
                                                'localite_id' : itineraire.loc_id.id,
                                                'unit_amount' : product.standard_price,
                                                'quantity' : quantity,
                                                'employee_id': participant.participant_id.id,
                                                'date' : datetime.today(),
                                                'mission_id' : record.id
                                            }
                                        record.env['cim.expense'].create(vals)
                        
#                         if record.company_id.auto_compute_carb and participant.role_mission_id.code == 'M':
#                             montant_carburant = sum(item.montant_carb_mission for item in self.vehicule_mission_ids)
#                             vals_car = {
#                                     'name' : 'Frais Carburant',
# #                                     'product_id' : self.env.ref('cim.cim_expense_product_fuel').id,
#                                     'unit_amount' : montant_carburant,
#                                     'employee_id': participant.participant_id.id,
#                                     'date' : datetime.today(),
#                                     'mission_id' : record.id
#                                 }
#                             record.env['cim.expense'].create(vals_car)
                        
                        section = "%s / %s" %(participant.participant_id.name,participant.participant_id.matricule or '')
                        vals = {
                            'name' :  section,
                            'display_type': 'line_section',
                            'employee_id': participant.participant_id.id,
                            'mission_id' : record.id
                        }
                        record.env['cim.expense'].create(vals)
                        
            record.write({'previous_state': record.state, 'state': 'approbation'})
            record.sudo().activity_update()
    
    @api.multi
    def act_check_budget(self):
        '''
        Check the budget by the DAF
        '''
        for record in self:
            if record.mission_type_id.id == record.env.ref('cim.data_mission_type_internal').id:
                if record.budget_line_id and (record.budget_line_id.credit_dispo >= record.frais_mission_total):
                    credit_dispo = record.budget_line_id.credit_dispo - record.frais_mission_total
                    record.budget_line_id.write({'credit_dispo' : credit_dispo})
                else:
                    raise ValidationError(_('Le montant de la source de financement est inférieur au montant total des dépenses de la mission.\n Veuillez modifier le montant de la source de finacement ou veuillez choisir une autre source de financement.'))
               
            record.write({'previous_state': record.state, 'state': 'budgeting'})
            record.sudo().activity_update()
    
    @api.multi
    def act_cancel_mission(self):
        '''
        Cancel the mission by the supervisor
        '''
        for record in self:
            if record.state == 'budgeting':
                frais_mission = record.frais_mission_total + record.total_carb_mission
                credit_dispo = frais_mission + record.budget_line_id.credit_dispo
                record.budget_line_id.write({'credit_dispo': credit_dispo})
                
            record.write({'previous_state': record.state, 'state': 'canceled'})
    
    @api.multi
    def act_rejeter_mission(self, rejet_id):
        '''
        Reject the mission
        '''
        if rejet_id:
            mission_rejet = self.env['cim.mission.rejet'].browse(rejet_id)
            mission_rejet.write({'state_rejet_debut' : self.state})
        for state in STATE_MISSION_SELECTION:
            if self.state == state[0]:
                index = STATE_MISSION_SELECTION.index(state) - 1
                previous_state = STATE_MISSION_SELECTION[index][0]
                self.sudo().activity_unlink(['cim.mail_activity_mission_approbation',
                                              'cim.mail_activity_mission_budgetisation',
                                              'cim.mail_activity_mission_validation',
                                              'cim.mail_activity_mission_paiement',
                                              'cim.mail_activity_mission_verification',
                                              'cim.mail_activity_mission_cloture'])
                if self.state == 'approbation':
                    self.frais_ids.sudo().unlink()
                # Restauration des frais déduits du credit disponible de la ligne budgétaire
                if self.state == 'budgeting':                    
                    credit_a_restaurer = self.budget_line_id.credit_dispo + self.frais_mission_total
                    self.budget_line_id.write({'credit_dispo' : credit_a_restaurer})
                    
                    # self._cr.execute('update ')             
                elif self.state == 'initiation':
                    self.name = self.default_name
                mission_rejet.write({'state_rejet_fin' : previous_state})
                self.write({'state': previous_state})
                self.sudo().activity_update()
    
    @api.multi
    def act_generate_ordre_mission(self):
        if self.type_ordre_mission_id.code == 'I' :
            if self.mission_type_id.id == self.env.ref('cim.data_mission_type_internal').id:
                return self.env.ref('cim.cim_mission_interieur').report_action(self)
            if self.mission_type_id.id == self.env.ref('cim.data_mission_type_external').id:
                return self.env.ref('cim.cim_mission_exterieur').report_action(self)
        if self.type_ordre_mission_id.code == 'G' :
            if self.mission_type_id.id == self.env.ref('cim.data_mission_type_internal').id:
                if len(self.vehicule_mission_ids) != 0 :
                    return self.env.ref('cim.cim_mission_interieur_group').report_action(self)
                if len(self.vehicule_mission_ids) == 0 :
                    return self.env.ref('cim.cim_mission_interieur_group_nocar').report_action(self) 
            if self.mission_type_id.id == self.env.ref('cim.data_mission_type_external').id:
                return self.env.ref('cim.cim_mission_interieur_group').report_action(self)
    
    @api.multi
    def act_generate_mission_dam(self):
        return self.env.ref('cim.cim_mission_order').report_action(self)

    @api.multi
    def act_generate_mission_interieur(self):
        return self.env.ref('cim.cim_mission_interieur').report_action(self)

    @api.multi
    def act_generate_mission_interieur_group(self):
        return self.env.ref('cim.cim_mission_interieur_group').report_action(self)

    @api.multi
    def act_generate_mission_exterieur(self):
        return self.env.ref('cim.cim_mission_exterieur').report_action(self)
    
    @api.multi
    def act_generate_etat_prise_en_charge(self):
        for p in self.participant_ids:
            montant_hebergement = sum(line.unit_amount 
                                       for line in self.frais_ids.filtered(lambda f: f.product_id.product_tmpl_id.id == self.env.ref('cim.cim_expense_product_accommodation').id and f.employee_id == p.participant_id))
            nbr_nuit = sum(line.quantity 
                            for line in self.frais_ids.filtered(lambda f: f.product_id.product_tmpl_id.id == self.env.ref('cim.cim_expense_product_accommodation').id and f.employee_id == p.participant_id))
            montant_restauration = sum(line.unit_amount 
                                        for line in self.frais_ids.filtered(lambda f: f.product_id.product_tmpl_id.id == self.env.ref('cim.cim_expense_product_restoration').id and f.employee_id == p.participant_id))
            nbr_jour = sum(line.quantity 
                            for line in self.frais_ids.filtered(lambda f: f.product_id.product_tmpl_id.id == self.env.ref('cim.cim_expense_product_restoration').id and f.employee_id == p.participant_id))
            montant_autre = sum(line.mission_id.frais_mission_total
                                 for line in self.other_frais_ids.filtered(lambda f: f.employee_id == p.participant_id)) 
            montant_total = (montant_hebergement*nbr_nuit) + (montant_restauration*nbr_jour) + montant_autre
            p.sudo().write({'montant_hebergement': montant_hebergement,
                            'nbr_nuit': nbr_nuit,
                            'montant_restauration': montant_restauration,
                            'nbr_jour': nbr_jour,
                            'montant_autre': montant_autre,
                            'montant_total': montant_total})
            
        return self.env.ref('cim.cim_etat_prise_en_charge').report_action(self)
    
    @api.multi
    def act_generate_etat_carburant(self):
        return self.env.ref('cim.cim_etat_carburant').report_action(self)

    @api.multi
    def act_generate_mission_synthese(self):
        return self.env.ref('cim.cim_mission_synthese').report_action(self)

    @api.multi
    def act_pay_expense_mission(self):
        for expense in self.frais_ids:
            expense.write({'state': 'done'})
        if self.frais_mission_total == self.montant_total_paye:
            self.write({'is_paid': True, 'state': 'daf_payment'})
        else:
            raise ValidationError(_('Veuillez effectuer le paiement total de la mission!'))
        self.sudo().activity_update()
    
    @api.multi
    def act_validate_mission(self, vals):
        if self.mission_type_id.id == self.env.ref('cim.data_mission_type_external').id:
            if not self.cocm_id and self.cocm: 
                return {
                    'name': 'Affectation COCM',
                    'view_mode': 'form',
                    'view_type': 'form',
                    'res_model': 'affecter.cocm.wizard',
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                    }
        self.write({'previous_state': self.state, 'state': 'validate_sg'})
        #Génération du numéro de mission
        if  self.num_mission == False :
            seq = self.env['ir.sequence'].next_by_code('cim.mission.seq')
            seq = seq.replace("prefix1", self.company_id.prefix )
            seq = seq.replace("prefix2", self.department_id.prefix )
            self.num_mission = seq 
            self.name = seq
        else:
            self.name = self.num_mission
        
        self.sudo().activity_update()
        #Génération des numéro d'ordre de mission par participant selon le type
        if self.type_ordre_mission_id.code == 'I' :
            for p in self.participant_ids :
                seq = self.env['ir.sequence'].next_by_code('cim.ordre.mission.seq')
                p.num_om = "%s-%s" %(seq, self.num_mission)
        if self.type_ordre_mission_id.code == 'G' :
            if len(self.vehicule_mission_ids) != 0 :
                for v in self.vehicule_mission_ids :
                    seq = self.env['ir.sequence'].next_by_code('cim.ordre.mission.seq')
                    v.num_om = "%s-%s" %(seq, self.num_mission) 
                    for p in v.passager_ids :
                        p.num_om = "%s-%s" %(seq, self.num_mission)
            if len(self.vehicule_mission_ids) == 0 :
                for p in self.participant_ids :
                    seq = self.env['ir.sequence'].next_by_code('cim.ordre.mission.seq')
                    p.num_om = "%s-%s" %(seq, self.num_mission)
                    
        self.act_generate_ordre_mission()

            
        
    @api.multi
    def act_check_mission(self):
        checked = True
        for participant in self.participant_ids:
            if participant.state != 'checked':
                checked = False
        if checked:      
            self.write({'state': 'checked'})
            self.sudo().activity_update()
        else:
            raise ValidationError(_('Veuillez effectuer la vérification des participants!'))
    
    @api.multi
    def act_close_mission(self):
            self.write({'previous_state': self.state, 'state': 'done'})
            self.sudo().activity_update()

    @api.multi
    def act_generate_mission(self):
        return self.env.ref('cim.cim_mission_final').report_action(self)
    
    
    @api.multi
    def act_validate_eval(self):
        return self.write({'state_eval': 'validated_eval'})
    
    @api.multi
    def act_cancel_eval(self):
        return self.write({'state_eval': 'new_eval'})
    
    @api.multi
    def act_validate_rapport(self):
        return self.write({'state_rapport': 'validated_rapport'})
    
    @api.multi
    def act_cancel_rapport(self):
        return self.write({'state_rapport': 'new_rapport'})
    
    # ------------------------------------------------------------
    # Le montant total des frais en lettre
    # ------------------------------------------------------------
    
    def lettrer(self, montant):
        
        total_lettre = ''
        apres_virgule = ''
        split_num = str(montant).split('.')
        int_part = int(split_num[0])
        #si dec / 10 <1 ==> *100 
        #si dec /10 <10 ==> * 10
        #si dec /10 >10 ==> * 1
        
        decimal_part = int(split_num[1])
        if (decimal_part / 10 ) < 1 :
            decimal_part = decimal_part * 100
        elif (decimal_part / 10) < 10 :
            decimal_part = decimal_part * 10
       
        total_lettre = num2words(int_part,lang='fr').title()
        
        if self.currency_id.name == 'XOF':
                total_lettre += ' Francs CFA'
                apres_virgule=' Francs CFA'
        elif self.currency_id.name == 'EUR': 
                total_lettre += ' Euros'
                apres_virgule=' Centimes'

        if decimal_part:
            total_lettre += ' et '+ num2words(decimal_part, lang='fr') + apres_virgule
        else:
            return total_lettre
        
        return total_lettre
    
    @api.one
    @api.depends('frais_mission_total')
    def _lettrer_frais_mission_total(self):
        self.total_lettre = self.lettrer(self.frais_mission_total)
        return
    
    # ------------------------------------------------------------
    # Activity methods
    # ------------------------------------------------------------

    def _get_responsible(self):
        if self.state in ['initiation','checked'] and self.department_id.manager_id.user_id:
            return self.department_id.manager_id.user_id
        elif self.state in ['approbation','validate_sg','daf_payment'] and self.company_id.regisseur_id.user_id:
            return self.company_id.regisseur_id.user_id
        elif self.state == 'budgeting' and self.company_id.ordonnateur_id.user_id and self.mission_type_id.id == self.env.ref('cim.data_mission_type_internal').id:
            return self.company_id.ordonnateur_id.user_id
        elif self.state == 'budgeting' and self.company_id.ordonnateur_externe_id.user_id and self.mission_type_id.id == self.env.ref('cim.data_mission_type_external').id:
            return self.company_id.ordonnateur_externe_id.user_id
        return self.env.user

    def activity_update(self):
        to_clean, to_do = self.env['cim.mission'], self.env['cim.mission']
        for mission in self:
            if mission.state == 'new':
                to_clean |= mission
            elif mission.state == 'initiation':
                date_deadline = datetime.now() + timedelta(days=mission.company_id.delais_approbation)
                mission.activity_schedule(
                    'cim.mail_activity_mission_approbation',
                    user_id=mission.sudo()._get_responsible().id, date_deadline=date_deadline)
            elif mission.state == 'approbation':
                date_deadline = datetime.now() + timedelta(days=mission.company_id.delais_budgetisation)
                mission.activity_feedback(['cim.mail_activity_mission_approbation'])
                mission.activity_schedule(
                    'cim.mail_activity_mission_budgetisation',
                    user_id=mission.sudo()._get_responsible().id, date_deadline=date_deadline)
            elif mission.state == 'budgeting':
                date_deadline = datetime.now() + timedelta(days=mission.company_id.delais_validation)
                mission.activity_feedback(['cim.mail_activity_mission_budgetisation'])
                mission.activity_schedule(
                    'cim.mail_activity_mission_validation',
                    user_id=mission.sudo()._get_responsible().id, date_deadline=date_deadline)
            elif mission.state == 'validate_sg':
                date_deadline = datetime.now() + timedelta(days=mission.company_id.delais_paiement)
                mission.activity_feedback(['cim.mail_activity_mission_validation'])
                mission.activity_schedule(
                    'cim.mail_activity_mission_paiement',
                    user_id=mission.sudo()._get_responsible().id, date_deadline=date_deadline)
            elif mission.state == 'daf_payment':
                date_deadline = datetime.now() + timedelta(days=mission.company_id.delais_verification)
                mission.activity_feedback(['cim.mail_activity_mission_paiement'])
                mission.activity_schedule(
                    'cim.mail_activity_mission_verification',
                    user_id=mission.sudo()._get_responsible().id, date_deadline=date_deadline)
            elif mission.state == 'checked':
                date_deadline = datetime.now() + timedelta(days=mission.company_id.delais_cloture)
                mission.activity_feedback(['cim.mail_activity_mission_verification'])
                mission.activity_schedule(
                    'cim.mail_activity_mission_cloture',
                    user_id=mission.sudo()._get_responsible().id, date_deadline=date_deadline)
            elif mission.state == 'done':
                to_do |= mission
            elif mission.state == 'canceled':
                to_clean |= mission
        if to_clean:
            to_clean.activity_unlink(['cim.mail_activity_mission_approbation'])
        if to_do:
            to_do.activity_feedback(['cim.mail_activity_mission_verification'])


class MissionType(models.Model):
    _name = 'cim.mission.type'
    _description = 'Type de la Mission'

    name = fields.Char(string='Nom', required=True)
    nbr_jours_max = fields.Integer(string='Nombre de jours max')
    description = fields.Text(string='Description')
    
    _sql_constraints = [
        ('name_mission_type_uniq', 'UNIQUE (name)',  "Le libellé du type de mission doit être unique!"),
        ('nbr_jourmax_positiv', 'CHECK (nbr_jours_max >= 0 )',  "Le nombre de jour maximum est toujours supérieur ou égal à 0!")
        ]

class MotifMission(models.Model):
    _name = "cim.motif.mission"
    _description = "Motif de mission"

    name = fields.Char(required=True, string="Intitulé")
    description = fields.Text(string="Description")
    active = fields.Boolean(string="Est activé", default=True)
    
    _sql_constraints = [
        ('name_motif_mission_uniq', 'UNIQUE (name)',  'Le libellé du motif doit être unique!')
        ]

class MissionParticipant(models.Model):
    _name = 'cim.mission.participant'
    _description = 'Participants de mission'
    _rec_name = 'participant_id'
    
    num_om = fields.Char('N° OM')
    participant_id = fields.Many2one('hr.employee', "Participant")
    matricule = fields.Char('Matricule', related='participant_id.matricule')
    work_phone = fields.Char('Télephone', related='participant_id.work_phone')
    company_id = fields.Many2one('res.company', string='Structure', related='participant_id.company_id')
    department_id = fields.Many2one('hr.department', 'Service', related='participant_id.department_id')
    role_mission_id = fields.Many2one('cim.role.mission', 'Rôle', required=True)
    mission_id = fields.Many2one('cim.mission', 'Mission', index=True, ondelete='cascade')
    cocm_id = fields.Many2one('cim.cocm', 'COCM', index=True)
    code_role = fields.Char('Code du rôle',related='role_mission_id.code')
    est_pec = fields.Boolean('Est PEC', default=True)
    is_paid = fields.Boolean(string="Payé")
    state_mission = fields.Selection(STATE_MISSION_SELECTION, string='Statut', related='mission_id.state', index=True, readonly=True)
    state = fields.Selection([('new', 'Nouveau'),('paid', 'Payé'),('checked', 'Vérifié')], string='Statut', default='new', index=True, readonly=True)
    
    itineraire_reel_ids = fields.One2many('cim.itineraire.reel', 'participant_id', string='Itinéraires réels', readonly=True)
    duree_reel = fields.Integer(string='Durée réelle', readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True, default=lambda self: self.env.user.company_id.currency_id)
    frais_reel = fields.Monetary(string='Frais réel', currency_field='currency_id')
    trop_percu = fields.Monetary(string='Trop percu', currency_field='currency_id', readonly=True)
    reste_a_paye = fields.Monetary(string='Reste à payer', currency_field='currency_id', readonly=True)
    observation = fields.Text(string='Observation')
    is_paid = fields.Boolean(string="Est payé")
    is_refunded = fields.Boolean(string="Est remboursé")
    
    # Etat de prise en charge des frais de mission par participant    
    montant_hebergement = fields.Monetary(string='Hébergement', readonly=True)
    nbr_nuit = fields.Integer(string='Nbr nuités', readonly=True)
    montant_hebergement_total = fields.Monetary(string='Hébergement', readonly=True, compute="_compute_montant_hebergement_total", store=True)
    montant_restauration = fields.Monetary(string='Restauration', currency_field='currency_id', readonly=True)
    nbr_jour = fields.Integer(string='Nbr jours', readonly=True)
    montant_restauration_total = fields.Monetary(string='Restauration', currency_field='currency_id', readonly=True, compute="_compute_montant_restauration_total", store=True)
    montant_autre = fields.Monetary(string='Autre frais', currency_field='currency_id', readonly=True)
    montant_total = fields.Monetary(string='Mantant Total', currency_field='currency_id', readonly=True)
    
    # Vérification des piéces justificatives
    pj_ids = fields.One2many('cim.mission.participant.pj', 'participant_id', string='Pièces justificatives', groups='cim.group_regisseur')
    
    
    _sql_constraints = [
        ('mission_id_cocm_id_participant_id_unique', 'UNIQUE (mission_id,cocm_id,participant_id)', "Un participant est répété au moins deux fois sur la même demande.")
        ]
    
    @api.one
    @api.depends('montant_hebergement','nbr_nuit')
    def _compute_montant_hebergement_total(self):
        self.montant_hebergement_total = self.montant_hebergement * self.nbr_nuit
        
    @api.one
    @api.depends('montant_restauration','nbr_jour')
    def _compute_montant_restauration_total(self):
        self.montant_restauration_total = self.montant_restauration * self.nbr_jour
    
    @api.model
    def create(self, vals):
        participantid = vals.get('participant_id', False)
        rolemissionid = vals.get('role_mission_id', False)
        missionid = vals.get('mission_id', False) 
        cocmid = vals.get('cocm_id', False)        
        if participantid and rolemissionid :
            missionparticipants = self.env['cim.mission.participant'].search([('mission_id','=', missionid),
                                                ('cocm_id','=', cocmid),
                                                ('participant_id','=', participantid)])
            if missionparticipants:
                raise ValidationError(_("Un participant apparaît au moins deux fois dans la liste. Prière retirer pour ne laisser qu'une seule présence!"))
        return super(MissionParticipant, self).create(vals)
    

    @api.multi
    def delete_participant(self):
        # supprimer les frais mission de participant
        self.env['cim.expense'].sudo().search([('employee_id', '=', self.participant_id.id),('mission_id', '=', self.mission_id.id)]).unlink()
        self.env['cim.paiement.participant'].sudo().search([('participant_id', '=', self.participant_id.id),('mission_id', '=', self.mission_id.id)]).unlink()
        return

class ItineraireReel(models.Model):
    _name = 'cim.itineraire.reel'
    _description = 'Itinéraire réel de participant'
    _rec_name = 'loc_id'
    _order = 'date_arrivee asc, id asc'
    
    loc_id = fields.Many2one("cim.localite", string="Localité", required=False)
    depart = fields.Boolean("Départ")
    date_arrivee = fields.Date(string="Date d'arrivée", default=fields.Date.today(), required=False)
    duree = fields.Integer(string="Durée (en jour)")
    description = fields.Char(string='Description')
    participant_id = fields.Many2one('cim.mission.participant', string="Participant")
  
class MissionParticipantPJ(models.Model):
    _name = 'cim.mission.participant.pj'
    _description = "Pièces justificatives de participant"
    _rec_name = 'nature_pj_id'
    
    nature_pj_id = fields.Many2one('cim.nature.pj', string='Nature PJ')
    is_exist = fields.Boolean('Existe') 
    participant_id = fields.Many2one('cim.mission.participant')
    

class MissionObjectif(models.Model):
    _name = 'cim.mission.objectif'
    _description = "Vérification des objectifs de la mission"
    _rec_name = 'objectif_mission'
    
    mission_id = fields.Many2one('cim.mission', 'Mission', index=True, ondelete='cascade')
    objectif_mission = fields.Char(string="Objectif", required=True)
    objectif_atteint = fields.Boolean(string="Objectif atteint", default=False)
    objectif_observations = fields.Char(string='Observations')
    
    _sql_constraints = [
        ('critere_id_mission_id_unique', 'UNIQUE (objectif_mission,mission_id)',  "Un objectif à la fois pour la mission!")
        ]
   


class CritereEvaluation(models.Model):
    _name = 'cim.critere.evaluation'
    _description = "Critère d'évaluation de mission"
    
    name = fields.Char("Intitulé", required=True)
    
    _sql_constraints = [
        ('name_critere_uniq', 'UNIQUE (name)',  'Le libellé du critère doit être unique!')
        ]

class MissionEvaluation(models.Model):
    _name = 'cim.mission.evaluation'
    _description = 'Evaluation de la mission'
    _rec_name = 'critere_id'
    
    mission_id = fields.Many2one('cim.mission', 'Mission', index=True, ondelete='cascade')
    #critere = fields.Char(string="Critère d'évaluation", required=True)
    critere_id = fields.Many2one('cim.critere.evaluation', string="Critère", required=True)
    #vehicule_id = fields.Many2one('cim.vehicule', string='Véhicule', required=True)
    val_ciblee = fields.Integer(string='Valeur ciblée', required=True)
    val_reelle = fields.Integer(string='Valeur mesurée')
    taux_evaluation = fields.Float(string='Taux (%)', readonly=True, compute="_compute_taux_evaluation", store=True)
    observation = fields.Char(string='Observations')
    
    _sql_constraints = [
        ('critere_id_mission_id_unique', 'UNIQUE (critere_id,mission_id)',  'Un critère ne peut être pris deux fois sur la même mission!')
        ]
   
    @api.one 
    @api.depends('val_ciblee', 'val_reelle')
    def _compute_taux_evaluation(self):
        if self.val_ciblee and self.val_reelle :
            self.taux_evaluation = (self.val_reelle/self.val_ciblee)*100
            
    @api.model
    def create(self, vals):
        critereid = vals.get('crirere_id', False)
        missionid = vals.get('mission_id', False)        
        if critereid :
            missionevaluations = self.env['cim.mission.evaluation'].search([('mission_id','=', missionid),
                                                ('critere_id','=', critereid)])
            if missionevaluations:
                raise ValidationError(_("Un critère d'évaluation apparaît au moins deux fois dans la liste. Prière le retirer pour ne laisser quune seule présence!"))
        return super(MissionEvaluation, self).create(vals)


class TypeOrdreMission(models.Model):
    _name = 'cim.type.ordre.mission'
    _description = "Type d'ordre de mission"
    
    name = fields.Char("Intitulé", required=True)
    code = fields.Char("Code", required=True, size=1)
    
    _sql_constraints = [
        ('code_uniq', 'UNIQUE (code)',  "Le code du type d'ordre de mission doit être unique!"),
        ('name_uniq', 'UNIQUE (name)',  'Le libellé doit être unique!')
        ]            

class OrdreMission(models.Model):
    _name = 'cim.ordre.mission'
    _description = "Les numéros d'ordre de mission"
    
    mission_id = fields.Many2one('cim.mission', 'Mission', index=True, ondelete='cascade')
    name = fields.Char(string="Numéro", required=True)
    type_ordre_mission_id = fields.Many2one('cim.type.ordre.mission', string="Type de l'ordre de mission", required=True)
    
    

class RoleMission(models.Model):
    _name = 'cim.role.mission'
    _description = 'Rôle de mission'
    
    name = fields.Char("Intitulé", required=True)
    code = fields.Char("Code", required=True, size=1)
    
    _sql_constraints = [
        ('code_uniq', 'UNIQUE (code)',  'Le code du rôle doit être unique!'),
        ('name_uniq', 'UNIQUE (name)',  'Le libellé du rôle doit être unique!')
        ]

class MissionVehicule(models.Model):
    _name = 'cim.mission.vehicule'
    _description = 'Vehicules de mission'
    _rec_name = 'vehicule_id'
    
    num_om = fields.Char('N° OM')
    type_carrosserie_id = fields.Many2one('cim.type.carrosserie', string='Type de carrosserie', related='vehicule_id.type_carrosserie_id')
    company_vehicule_id = fields.Many2one('res.company', string='Structure du véhicule', related="vehicule_id.company_vehicule_id")
    vehicule_id = fields.Many2one('cim.vehicule', string='Véhicule', required=True)
    driver_ids = fields.Many2many('cim.mission.participant', 'mission_vehicule_participant_rel', 'vehicule_id', 'driver_id' ,string='Conducteurs', required=True)
    passager_ids = fields.Many2many('cim.mission.participant', 'mission_vehicule_passager_rel', 'vehicule_id', 'passager_id', string='Passagers', required=True)
    mission_id = fields.Many2one('cim.mission', string='Vehicule', index=True, ondelete='cascade')
    currency_id = fields.Many2one('res.currency', string='Devise', default=lambda self: self.env.user.company_id.currency_id)
    montant_carb = fields.Monetary(string='Montant Carburant', currency_field='currency_id', compute="_compute_montant_carb_mission")
    montant_carb_interne = fields.Monetary(string='Montant CCI', currency_field='currency_id', compute="_compute_montant_carb_mission")
    montant_carb_mission = fields.Monetary(string='Montant Carburant Mission', currency_field='currency_id', compute="_compute_montant_carb_mission")
    
    _sql_constraints = [
        ('mission_id_vehicule_id_unique', 'UNIQUE (mission_id,vehicule_id)',  'Un véhicule ne peut être utilisé deux fois sur la même mission!'),
        ]
    
    @api.model
    def create(self, vals):
        vehiculeid = vals.get('vehicule_id', False)
        missionid = vals.get('mission_id', False)        
        if vehiculeid :
            missionvehicules = self.env['cim.mission.vehicule'].search([('mission_id','=', missionid),
                                                ('vehicule_id','=', vehiculeid)])
            if missionvehicules:
                raise ValidationError(_("Un véhicule apparaît au moins deux fois dans la liste. Prière le retirer pour ne laisser quune seule présence!"))
        return super(MissionVehicule, self).create(vals)
    
    @api.one
    @api.depends('mission_id.duree_mission','vehicule_id.km_100','montant_carb','montant_carb_interne')
    def _compute_montant_carb_mission(self):
        nbr_jours = self.mission_id.duree_mission
        taux_journalier = self.company_vehicule_id.taux_journalier
        distance = self.mission_id.distance_mission
        km_100 = self.vehicule_id.km_100
        cout_carb = self.vehicule_id.type_carburant_id.price
        self.montant_carb = ((distance / 100) * km_100) * cout_carb
        self.montant_carb_interne = nbr_jours * taux_journalier
        self.montant_carb_mission = self.montant_carb + self.montant_carb_interne
    


class MissionItineraire(models.Model):
    _name = 'cim.mission.itineraire'
    _description = 'Itinéraire de mission'
    _rec_name = 'loc_id'
    _order = 'date_arrivee asc, id asc'
    
    loc_id = fields.Many2one("cim.localite", string="Localité", required=False)
    depart = fields.Boolean("Localité de départ")
    fin = fields.Boolean("Localité finale")
    date_arrivee = fields.Date(string="Date d'arrivée", default=fields.Date.today(), required=False)
    duree = fields.Integer(string="Durée (en jour)")
    description = fields.Char(string='Description')
    mission_id = fields.Many2one('cim.mission', string='Mission', ondelete='cascade', index=True)
    cocm_id = fields.Many2one('cim.cocm', string='COCM', index=True)
    
    @api.multi
    @api.onchange('depart')
    def _onchange_depart(self):
        if self.depart:
            self.duree = 0
#             self.date_arrivee = None

    @api.model
    def create(self, vals):
        localiteid = vals.get('loc_id', False)
        missionid = vals.get('mission_id', False)   
        cocmid = vals.get('cocm_id', False)        
        if localiteid :
            missionitineraires = self.env['cim.mission.itineraire'].search([('mission_id','=', missionid),
                                                ('cocm_id','=', cocmid),
                                                ('loc_id','=', localiteid)])
            missionitinerairesdepart = self.env['cim.mission.itineraire'].search([('mission_id','=', missionid),
                                                ('cocm_id','=', cocmid),
                                                ('depart','=', True)])
#             if missionitineraires:
#                 raise ValidationError(_("Une localité apparaît au moins deux fois dans la liste. Prière la retirer pour ne laisser qu'une seule présence!"))
            if len(missionitinerairesdepart) > 1 :
                raise ValidationError(_("Plusieurs point de départ apparaissent dans la liste. Prière en-retirer pour ne laisser qu'un seul!"))
        return super(MissionItineraire, self).create(vals)


class MotifRejet(models.Model):
    _name = 'cim.motif.rejet'
    _description = 'Motif de rejet de dossiers'
    
    name = fields.Char("Intitulé du motif", required=True)
    description = fields.Text("Description", )
    active = fields.Boolean("Actif", default=True)
    
    _sql_constraints = [
        ('name_motifrejet_uniq', 'UNIQUE (name)',  'Le libellé du motif de rejet doit être unique!')
        ]


class MissionRejet(models.Model):
    _name = 'cim.mission.rejet'
    _description = 'Liste des rejets sur les projets de mission'
    _rec_name= 'motif_rejet_id'
    _order = "create_date desc, id desc"
    
    def _default_employee(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
    
    motif_rejet_id = fields.Many2one('cim.motif.rejet', "Motif de rejet", index=True, required=True)
    mission_id = fields.Many2one('cim.mission', 'Mission', index=True, ondelete='cascade')
    cocm_id = fields.Many2one('cim.cocm', 'COCM', index=True, ondelete='cascade')
    description_rejet = fields.Text("Description", )
    date_rejet = fields.Date('Date rejet')
    auteur_rejet_id = fields.Many2one('hr.employee', string='Auteur du rejet', index=True, default=_default_employee)
    state_rejet_debut = fields.Char("Avant rejet", readonly=True)
    state_rejet_fin = fields.Char("Après rejet", readonly=True)
    type = fields.Selection([('mission', "Mission"),('cocm', "COCM")], string='Type')   

# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class Vehicule(models.Model):
    _name = 'cim.vehicule'
    _description = 'Véhicule'

    name = fields.Char(string="N° d'immatriculation", required=True)
    description = fields.Text('Logistic description')
    image = fields.Binary("Image", attachment=True)
    license_plate = fields.Many2one('cim.vehicule.marque', string='Modèle')
    type_carrosserie_id = fields.Many2one('cim.type.carrosserie', string='Type de carrosserie')
    seats = fields.Integer('Nombre de places')
#     doors = fields.Integer('Nombre de portes')
    color = fields.Char('Couleur')
    type = fields.Selection([('interne', 'Interne'),('externe', 'Externe')], 'Origine', required=True, default='interne')
    moyen_transport = fields.Selection([('vehicule', 'Vehicule'),('moto', 'Moto')], 'Moyen de transport', default='vehicule')
#     fuel_type = fields.Selection([
#         ('gasoline', 'Gasoline'),
#         ('diesel', 'Diesel'),
#         ('lpg', 'LPG'),
#         ('electric', 'Electric'),
#         ('hybrid', 'Hybrid')
#         ], 'Type de carburant')
    type_carburant_id = fields.Many2one('cim.type.carburant', string="Type de carburant", required=True)
    is_occuped = fields.Boolean("Est occupé")
    is_good = fields.Boolean("En bon etat", default=True)
    company_vehicule_id = fields.Many2one('res.company', string='Structure du véhicule', default=lambda self: self.env.user.company_id, readonly=True)
    other_company_vehicule = fields.Char(string="Origine externe")
    km_100 = fields.Float(string='Litre au 100')
    
    _sql_constraints = [
        ('name_uniq', 'UNIQUE (name)',  "Le numéro d'immatriculation du véhicule est unique!")
        ]
    
class VehiculeMarque(models.Model):
    _name = 'cim.vehicule.marque'
    _description = 'Marque et modèle de véhicule'

    name = fields.Char(string='Nom du modèle', required=True)
    brand_id = fields.Char(string='Marque', required=True)
    description = fields.Text(string='Description')
    image = fields.Binary("Image", attachment=True)
    
    _sql_constraints = [
        ('name_uniq', 'UNIQUE (name)',  "Le nom du modèle du véhicule est unique!")
        ]

class TypeCarrosserie(models.Model):
    _name = 'cim.type.carrosserie'
    _description = 'Type de carrosserie'

    name = fields.Char(string='Nom de la carrosserie', required=True)
    description = fields.Text(string='Description')
    
    _sql_constraints = [
        ('name_uniq', 'UNIQUE (name)',  "Le nom du type de la carrosserie du véhicule est unique!")
        ]

class TypeCarburant (models.Model):
    _name = 'cim.type.carburant'
    _inherit = ['mail.thread']
    _description = 'Type de carburant'

    name = fields.Char(string='Intitulé', required=True, track_visibility='onchange')
    currency_id = fields.Many2one('res.currency', string='Devise', default=lambda self: self.env.user.company_id.currency_id)
    price = fields.Monetary(string='Prix de litre', currency_field='currency_id', track_visibility='onchange')
    description = fields.Text(string='Description')
    
    _sql_constraints = [
        ('name_uniq', 'UNIQUE (name)',  "Le nom du type de carburant est unique!"),
        ('price_positiv', 'CHECK (price >= 0)',  "Le prix du carburant est toutjours positif!")
        ]
   

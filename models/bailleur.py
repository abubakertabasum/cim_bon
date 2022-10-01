# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class Bailleur(models.Model):
    _name = 'cim.bailleur'
    _description = 'Bailleur'
    
    name = fields.Char(string='Nom de bailleur', required=True)
    code = fields.Char(string="Code", size=10, required=True )
    sigle = fields.Char(string="Sigle")
    telephone = fields.Char(string="Téléphone")
    #Commentaire sur le sigle
    
    _sql_constraints = [
        ('code_bailleur_uniq', 'UNIQUE (code)',  'Le code est unique sur 10 caractères max!'),
        ('name_bailleur_uniq', 'UNIQUE (name)',  'Le nom du bailleur doit être unique!')
        ]
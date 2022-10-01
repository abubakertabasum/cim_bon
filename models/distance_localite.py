# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class DistanceLocalite(models.Model):
    _name = 'cim.distance.localite'
    _description = 'Distance entre localités'
    
    name = fields.Char(string="Nom", compute="_compute_name")
    loc_a_id = fields.Many2one("cim.localite", string="Localité A", required=True)
    loc_b_id = fields.Many2one("cim.localite", string="Localité B", required=True)
    distance_ab = fields.Float(string="Distance (en km)")
    distance_symetrique = fields.Boolean(string='Distance symétrique ?', default=True)
    
    _sql_constraints = [
        ('distance_uniq', 'UNIQUE (loc_a_id, loc_b_id)',  "Les distances entre les localités sont uniques!"),
        ('distance_ab_positiv', 'CHECK (distance_ab >= 0)',  "La valeur de la distance est toutjours positive!")
        ]
    
    @api.one
    @api.depends('loc_a_id','loc_b_id')
    def _compute_name(self):
        if self.loc_a_id and self.loc_b_id:
            self.name = "%s -> %s" %(self.loc_a_id.name, self.loc_b_id.name)
# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp

class Expense(models.Model):
    _inherit = 'hr.expense'
    _name = 'cim.expense'
    
    @api.model
    def _default_employee_id(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
    
    @api.model
    def _default_product_uom_id(self):
        return self.env['uom.uom'].search([], limit=1, order='id')
    
    @api.multi
    def employee_count(self, frais_ids, name, categ):
        count = 0
        for f in frais_ids:
            if f.total_amount and f.employee_id.id == name and f.employee_id.categ_id == categ:
                count += 1
        return count
    
    @api.multi
    def localite_count(self, frais_ids, name, localite, zone):
        count = 0
        for f in frais_ids:
            ## le décalage se trouve ici il faut vérifier la condition mm avec zone de la mission, déja le print yes se répète deux fois
#             if f.total_amount and f.localite_id.id == name and f.employee_id == emp_id and f.localite_id.zone_mission_id.id == zone:
            if f.total_amount and f.employee_id.id == name and f.localite_id.id == localite and f.localite_id.zone_mission_id.id == zone :
                count += 1
        return count
    
#     @api.multi
#     def montant_value(self, frais_ids, name):
#         count = 0
#         for f in frais_ids:
#             if f.total_amount and f.employee_id.id == name :
#                 count += f.total_amount
#         return count
    
    employee_id = fields.Many2one('hr.employee', string="Employé", required=False, readonly=True, states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]}, default=_default_employee_id, domain=lambda self: self._get_employee_id_domain())
    product_id = fields.Many2one('product.product', string='Elément de dépense', required=False, readonly=True, states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]}, domain=[('can_be_expensed', '=', True)])
    localite_id = fields.Many2one('cim.localite', string='Localité', required=False, readonly=True)
    product_uom_id = fields.Many2one('uom.uom', string='Unité de mesure', required=False, readonly=True, states={'draft': [('readonly', False)], 'refused': [('readonly', False)]}, default=_default_product_uom_id)
    unit_amount = fields.Integer("Prix unitaire", required=False, readonly=True, states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]}, digits=dp.get_precision('Product Price'))
    quantity = fields.Integer(string="Quantité", required=False, readonly=True, states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]}, digits=dp.get_precision('Product Unit of Measure'), default=1)
    state = fields.Selection([
        ('draft', "En attente"),
        ('reported', 'Validé'),
        ('approved', 'Approuvé'),
        ('done', 'Payé'),
        ('refused', 'Refusé')
    ], string='Statut', copy=False, index=True, readonly=True, default='draft', help="Statut de la dépense.")
    mission_id = fields.Many2one('cim.mission', string='mission', index=True, ondelete='cascade')
    sequence = fields.Integer(default=10, help="Donne la séquence de cette ligne lors de l'affichage de la facture.")
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False)
    other = fields.Boolean("Autre frais", default=False)
    
    
    @api.model
    def create(self, vals):
        if vals.get('display_type', self.default_get(['display_type'])['display_type']):
            vals.update(unit_amount=0, employee_id=False, quantity=0, product_id=False)
        return super(Expense, self).create(vals)

    @api.multi
    def write(self, values):
        if 'display_type' in values and self.filtered(lambda line: line.display_type != values.get('display_type')):
            raise UserError("Vous ne pouvez pas changer le type d'une ligne de facture. Au lieu de cela, vous devez supprimer la ligne actuelle et créer une nouvelle ligne.")
        return super(Expense, self).write(values)
    
    @api.multi
    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window'].for_xml_id('base', 'action_attachment')
        res['domain'] = [('res_model', '=', 'cim.expense'), ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'cim.expense', 'default_res_id': self.id}
        return res

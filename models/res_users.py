# -*- coding: utf-8 -*-

from odoo import api, models, _
from odoo.exceptions import ValidationError, UserError


class Users(models.Model):
    _inherit = "res.users"
    
    
    @api.multi
    @api.constrains('groups_id')
    def _check_admin_central(self):

        if self.has_group('cim.group_admin_fonctionnel'):
            if not self.env.user.has_group('cim.group_admin_central'):
                raise ValidationError(_("Vous n'avez pas le droit de créer un nouveau compte utilisateur avec les mêmes droits qu'un administrateur."))

    @api.model
    def create(self, vals_list):
        users = super(Users, self.with_context(default_customer=False)).create(vals_list)
        for user in users:
            user.password = 'cim'
            user.partner_id.active = user.active
            if user.partner_id.company_id:
                user.partner_id.write({'company_id': user.company_id.id})
        return users

class ChangePasswordUser(models.TransientModel):
    _inherit = "change.password.user"
    
    @api.multi
    def change_password_button(self):
        for line in self:
            if not line.new_passwd:
                raise UserError(_("Avant de cliquer sur 'Changer de mot de passe', vous devez saisir un nouveau mot de passe!"))
            if not self.env.user.has_group('cim.group_admin_central'):
                raise ValidationError(_("Vous n'avez pas le droit de modifier le mot de passe d'un utilisateur."))
            line.user_id.write({'password': line.new_passwd})
        # don't keep temporary passwords in the database longer than necessary
        self.write({'new_passwd': False})
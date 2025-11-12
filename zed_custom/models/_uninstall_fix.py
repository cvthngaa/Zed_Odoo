from odoo import models, fields

class ZedRecipeLineFix(models.Model):
    _name = 'zed.recipe.line'
    _description = 'Temporary dummy model to allow uninstall'

    name = fields.Char(string="Name")

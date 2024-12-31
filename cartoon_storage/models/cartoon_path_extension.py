from odoo import models, fields

class CartoonPathExtension(models.Model):
    _name = "cartoon.path.extension"
    _description = "File extension"

    name = fields.Char(string='Name', required=True)
    description = fields.Text(string='Description')

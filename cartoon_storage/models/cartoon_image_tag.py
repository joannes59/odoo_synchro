from odoo import models, fields

class CartoonImageTag(models.Model):
    _name = "cartoon.image.tag"
    _description = "Image Tag"

    name = fields.Char(string='Name', required=True)
    description = fields.Text(string='Description')
    slug = fields.Char(string='Slug')
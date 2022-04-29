
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


import logging
_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    sale_line_id = fields.Many2one('sale.order.line', string='order line')
    partner_id = fields.Many2one('res.partner', related='sale_line_id.order_id.partner_id', string="partner")


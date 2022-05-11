
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


import logging
_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    sale_line_id = fields.Many2one('sale.order.line', string='order line')
    partner_id = fields.Many2one('res.partner', string="partner")

    def update_production(self):
        """ Update production information"""
        for production in self:
            if production.sale_line_id:
                production.partner_id = production.sale_line_id.order_id.partner_id

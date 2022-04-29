
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval
import unicodedata

import logging
_logger = logging.getLogger(__name__)


class MrpOperation(models.Model):
    _inherit = 'mrp.operation'

    sale_line_id = fields.Many2one('sale.order.line', string='order line')
    partner_id = fields.Many2one('Customer', related='sale_line_id.order_id.partner_id')

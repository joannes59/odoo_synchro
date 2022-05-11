from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval

import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        """Add some function on order confirmation"""
        res = super().action_confirm()

        for order in self:
            for line in order.order_line:
                line.update_production()

        return res
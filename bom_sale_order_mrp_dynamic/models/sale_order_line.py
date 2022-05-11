from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval

import logging
_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    bom_id = fields.Many2one('mrp.bom', string='BOM', domain="[('product_id', '=', product_id)]")

    def update_production(self):
        """ Update information on production order"""
        for line in self:
            for move in line.move_ids:
                if move.created_production_id:
                    production = move.created_production_id
                    production.sale_line_id = line
                    production.update_production()

    def _update_bom_id(self):
        """ update bom_id"""
        if self.product_id.bom_id:
            self.bom_id = self.product_id.bom_id
        elif self.product_template_id.bom_id:
            self.product_id.create_bom()
            self.bom_id = self.product_id.bom_id
        else:
            self.bom_id = False

    @api.onchange('product_id')
    def product_id_change(self):
        """ update bom_id """
        res = super().product_id_change()
        self._update_bom_id()
        return res

    def button_open_bom(self):
        """open bom form"""
        self.ensure_one()
        self.update_bom_id()
        res_id = self.product_id.bom_id.id or False

        if not res_id:
            return {}
        else:
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'mrp.bom',
                'res_id': res_id,
                'views': [(False, 'form')],
                'view_id': False,
                'target': 'new',
            }

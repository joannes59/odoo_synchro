# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'


    market_date_start = fields.Datetime("date start", default="2000-01-01")

    @api.onchange('market_date_start')
    def onchange_market_date_start(self):
        "set parameter"
        self.env['ir.config_parameter'].sudo().set_param('market_date_start', self.market_date_start)

    def market_update_base(self):
        "Update exchange"
        pass
        return True


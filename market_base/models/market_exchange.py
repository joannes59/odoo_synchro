# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, __manifest__.py file in module root
# directory
##############################################################################


from odoo import models, fields, api
import datetime

import logging
_logger = logging.getLogger(__name__)


class MarketExchange(models.Model):
    """Market exchange"""
    _name = 'market.exchange'
    _description = 'Market exchange'

    name = fields.Char('Name')
    description = fields.Char('Description')

    state = fields.Selection([
            ('draft', 'Draft'),
            ('open', 'Opened'),
            ('stop', 'Stoped'),
            ('expired', 'Expired'),
            ('cancel', 'Cancel'),
            ],
        string='Status', required=True, default='draft')

    def button_update(self):
        "update data of this exchange"
        pass



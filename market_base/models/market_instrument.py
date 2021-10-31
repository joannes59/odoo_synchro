# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, __manifest__.py file in module root
# directory
##############################################################################


from odoo import models, fields, api
import datetime

import logging
_logger = logging.getLogger(__name__)


class MarketInstrument(models.Model):
    """Market Instrument"""
    _name = 'market.instrument'
    _description = 'Market instrument'

    name = fields.Char('Name')





# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import http
from odoo.http import request
from odoo.addons.sale.controllers.variant import VariantController


class BOMVariantController(VariantController):
   
    @http.route(['/sale/create_product_variant'], type='json', auth="user", methods=['POST'])
    def create_product_variant(self, product_template_id, product_template_attribute_value_ids, custom_product_template_attribute_value=[], **kwargs):
        return request.env['product.template'].browse(int(product_template_id)).create_product_variant(product_template_attribute_value_ids, custom_product_template_attribute_value)        

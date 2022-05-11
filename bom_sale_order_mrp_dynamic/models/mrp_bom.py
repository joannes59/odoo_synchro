
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval
import unicodedata
import json

import logging
_logger = logging.getLogger(__name__)


def convert_to_float(text):
    "convert dirty text to float or 0.0"
    out_str = ""
    if text:
        for char in text:
            # TODO: Use Country decimal notation function
            if char.isnumeric() or char in [',', '.']:
                out_str += char
        out_str = out_str.replace(',', '.')
        try:
            res = float(out_str or 0.0)
        except:
            res = 0.0
    else:
        res = 0.0
    return res


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    sale_line_id = fields.Many2one('sale.order.line', "Sale line")
    sale_id = fields.Many2one('sale.order', 'Sale order', related='sale_line_id.order_id')
    default_code = fields.Char("Code", related='product_id.default_code', store=True)
    product_template_attribute_value_ids = fields.Many2many('product.template.attribute.value',
                                                            related='product_id.product_template_attribute_value_ids',
                                                            string="Attribute Values")

    combination_indices = fields.Char('Combination value',
                                      related='product_id.combination_indices', store=True, index=True)
    json_attribute = fields.Text("Attribute value")
    json_custom_attribute = fields.Text("Custom Attribute value")
    json_product_value = fields.Text("Product value", related='product_id.json_product_value')
    json_product_tmpl_value = fields.Text("Product template value", related='product_tmpl_id.json_product_tmpl_value')

    def compute_line(self, data={}):
        """Compute the line"""
        for bom in self:
            for line in bom.bom_line_ids:
                line.compute_line(data=data)
            for line in bom.operation_ids:
                line.compute_line(data=data)

    def get_attribute_value(self):
        """Get attribute value with conversion to float or text"""
        self.ensure_one()
        res = json.loads(self.json_attribute or "{}")
        res.update(json.loads(self.json_custom_attribute or "{}"))
        return res

    def delete_attribute(self):
        """delete previous attribute parameters"""
        for bom in self:
            bom.json_attribute = "{}"
            bom.json_custom_attribute = "{}"

    def update_custom_value(self, product_custom_attribute_value_ids):
        """ Get custom value by
        product_custom_attribute_value_ids is set of product.attribute.custom.value"""
        self.ensure_one()
        res = self.dic_custom_value(product_custom_attribute_value_ids)
        self.json_custom_attribute = json.dumps(res)
        return res

    @api.model
    def dic_custom_value(self, product_custom_attribute_value_ids):
        """ Get custom value by
        product_custom_attribute_value_ids is set of product.attribute.custom.value"""
        res = {}
        for custom in product_custom_attribute_value_ids:
            custom_attribute = custom.custom_product_template_attribute_value_id.attribute_id
            custom_value = custom.custom_value
            if custom_attribute.code:
                res[custom_attribute.code] = '%s' % (custom_value)
                if custom_attribute.convert_type == 'float':
                    res[custom_attribute.code] = convert_to_float(res[custom_attribute.code])
        return res

    def create_attribute_value(self):
        """Get attribute value with conversion to float or text"""
        for bom in self:
            if bom.product_id:
                attribute_value_ids = bom.product_id.product_template_attribute_value_ids
            else:
                attribute_value_ids = bom.product_tmpl_id.attribute_line_ids

            json_value = {}
            for line in attribute_value_ids:
                if line.attribute_id.code:
                    if hasattr(line, 'product_attribute_value_id'):
                        json_value[line.attribute_id.code] = line.product_attribute_value_id.get_value()
                    else:
                        json_value[line.attribute_id.code] = '?'

            if bom.sale_line_id:
                bom.update_custom_value(bom.sale_line_id.product_custom_attribute_value_ids)
                
            bom.json_attribute = json.dumps(json_value)


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    python_compute = fields.Text(string='Computing', default="",
                                 help="Compute the new quantity or product by formula.\n\n"
                                      ":param line: actual BOM line\n"
                                      ":param attribute: name of attribute value\n\n"
                                      "Return value by create variable:\n"
                                      "product_qty = float\n"
                                      "product_id = product.product recordset singleton\n")

    def compute_line(self, data={}):
        """ Compute the python code on template to complete the product value"""
        return self.env['product.template'].compute_python_code(self)






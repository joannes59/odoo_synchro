# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval
import json
import logging
_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = "product.product"

    jit_production = fields.Boolean('JIT production', default=True)
    bom_id = fields.Many2one('mrp.bom', 'BOM', compute='get_bom_id', store=True)
    bom_line_ids = fields.One2many('mrp.bom.line', related='bom_id.bom_line_ids', string="BOM line")
    json_product_value = fields.Text("Product value")
    custom_product_template_attribute_value = fields.Text("custom value")
    init_product_template_attribute_value_ids = fields.Text("technical",
                                                        help="copy of product_template_attribute_value_ids"
                                                            "The attribute value initially returned by product configurator")

    def compute_python_code(self, data={}):
        """ Compute the python code on template to complete the product value"""
        return self.env['product.template'].compute_python_code(self, data=data)

    def get_bom_id(self):
        for product in self:
            bom_ids = self.env['mrp.bom'].search([('product_id', '=', product.id)])
            product.bom_id = bom_ids and bom_ids[0] or bom_ids

    def add_data(self):
        " return dictionnary data for futur computing"
        self.ensure_one()
        return {}

    def open_bom(self):
        """ Open view bom"""
        self.ensure_one()
        return {
            'name': self.name,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mrp.bom',
            'res_id': self.bom_id.id or False,
        }

    def put_attribute_value(self, values):
        """ Add new value, or change previews value
        values: set of product.attribute.value
        """

        for product_tmpl_id in self.mapped('product_tmpl_id'):
            product_tmpl_id.put_attribute_value(values)

        for product in self:
            for value in values:
                for product_value in product.product_template_attribute_value_ids:
                    if product_value.attribute_id == value.attribute_id:
                        # The attribute value exist
                        if product_value.product_attribute_value_id != value:
                            # the value is to change
                            product_value_ids = product_value.search([
                                ('attribute_line_id', '=', product_value.attribute_line_id.id),
                                ('product_attribute_value_id', '=', value.id)])
                            if product_value_ids:
                                new_product_value_id = product_value_ids[0].id
                            else:
                                new_product_value_id = product_value.create({
                                    'attribute_line_id': product_value.attribute_line_id.id,
                                    'product_attribute_value_id': value.id,
                                    'product_tmpl_id': product.product_tmpl_id.id,
                                    'attribute_id': value.attribute_id.id,
                                }).id

                            product_template_attribute_value_ids = product.product_template_attribute_value_ids.ids
                            product_template_attribute_value_ids.remove(product_value.id)
                            product_template_attribute_value_ids.append(new_product_value_id)
                            product.write({'product_template_attribute_value_ids': product_template_attribute_value_ids})
                        else:
                            break

    def create_bom(self, default=None):
        "Create BOM with information from template BOM"

        def check_constraint_attribute(lines, product):
            """ Unlink line when constraint is not ok, the lines can be :
            """
            unlink_line = self.env[lines._name]

            for line in lines:
                # Check the constraint
                constraint_attribute = {}
                # list the attribute needed
                for attribute_value in line.bom_product_template_attribute_value_ids:
                    if attribute_value.attribute_id.id not in list(constraint_attribute.keys()):
                        constraint_attribute[attribute_value.attribute_id.id] = attribute_value
                    else:
                        constraint_attribute[attribute_value.attribute_id.id] |= attribute_value
                # Check the attribute needed
                if product.init_product_template_attribute_value_ids:
                    product_template_attribute_value_ids = json.loads(product.init_product_template_attribute_value_ids)
                else:
                    product_template_attribute_value_ids = product.product_template_attribute_value_ids.ids
                list_attribute_value = self.env['product.template.attribute.value'].browse(
                    product_template_attribute_value_ids)

                for attribute_value in list_attribute_value:
                    if attribute_value.attribute_id.id in list(constraint_attribute.keys()):
                        if attribute_value not in constraint_attribute[attribute_value.attribute_id.id]:
                            unlink_line |= line
            # Update line
            for line in lines:
                line.bom_product_template_attribute_value_ids = False
            unlink_line.unlink()

        # start
        for product in self:
            # Check starting condition
            if not product.bom_id:
                product.get_bom_id()
            if product.bom_id or not product.product_tmpl_id.bom_id:
                continue
            # Create new BOM based on template BOM
            new_bom = product.product_tmpl_id.bom_id.copy(default or {})
            check_constraint_attribute(new_bom.bom_line_ids, product)
            check_constraint_attribute(new_bom.operation_ids, product)
            if product.default_code:
                new_bom.code = product.default_code

            # update bom
            new_bom.product_id = product
            product.bom_id = new_bom
            new_bom.create_attribute_value()
            new_bom.compute_line()

# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError, ValidationError
import json

import logging
_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    bom_id = fields.Many2one('mrp.bom', 'Template Bill of material', compute='get_tmpl_bom_id', store=True)
    bom_line_ids = fields.One2many('mrp.bom.line', related='bom_id.bom_line_ids', string="BOM line")
    template_code = fields.Char('Template code')
    default_jit_production = fields.Boolean('JIT production', default=True)
    python_compute = fields.Text(string='Python Code', default="",
                                 help="Compute variant value.\n\n"
                                      ":param attribute: dictionary with attribute value\n\n"
                                      "Return value by create variable:\n"
                                      "product_list_price = float\n"
                                      "product_lst_price = float\n"
                                      "product_price = float\n"
                                      "product_price_extra = float\n"
                                      "product_standard_price = float\n"
                                      "product_code = float\n"
                                       )

    @api.model
    def compute_python_code(self, objects,  data={}):
        """ Compute the python code on set of object with field  python_compute """
        res = {}
        for obj in objects:
            res[obj.id] = {}
            if hasattr(obj, 'python_compute') and obj.python_compute:
                localdict = data.copy()
                localdict.update({'object': obj})
                if hasattr(obj, 'bom_id') and obj.bom_id:
                    localdict.update(obj.bom_id.get_attribute_value())

                # Check ambiguity
                for attribute, value in localdict.items():
                    if hasattr(obj, attribute):
                        raise ValidationError(
                            "The parameters name (%s) is reserved on object %s" % (attribute, obj._name))

                # Execute safe code, return localdict with result
                safe_eval(obj.python_compute, localdict, mode="exec", nocopy=True)

                for attribute, value in localdict.items():
                    if len(attribute) and attribute[0] == "_":
                        continue

                    res[obj.id].update({attribute: value})
                    if hasattr(obj, attribute):
                        setattr(obj, attribute, value)
        return res

    def put_attribute_value(self, values):
        """ Check if this product has this attribute values
        values = product.attribute.value
        """
        for product_tmpl in self:
            for value in values:
                condition1 = [('product_tmpl_id', '=', product_tmpl.id), ('attribute_id', '=', value.attribute_id.id)]
                attribute_line_ids = product_tmpl.attribute_line_ids.search(condition1)
                if not attribute_line_ids:
                    att_vals = {
                        'product_tmpl_id': product_tmpl.id,
                        'attribute_id': value.attribute_id.id,
                        'value_ids': [(6, 0, [value.id])]
                    }
                    product_tmpl.attribute_line_ids.create(att_vals)
                elif value not in attribute_line_ids.value_ids:
                    attribute_line_ids.value_ids |= value

    def update_variant_compute(self, data={}):
        """ Update all variant by python code"""
        for product_tmpl in self:
            for product in product_tmpl.product_variant_ids:
                self.compute_python_code(product, data)

    def get_tmpl_bom_id(self):
        for product in self:
            bom_ids = self.env['mrp.bom'].search(
                [('product_tmpl_id', '=', product.id), ('product_id', '=', False)])
            product.bom_id = bom_ids and bom_ids[0] or bom_ids

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

    def create_bom(self):
        """Create Template BOM"""
        res = self.env['mrp.bom']

        for product_tmpl in self:

            if not product_tmpl.bom_id:
                product_tmpl.get_tmpl_bom_id()

            if not product_tmpl.bom_id:
                # New template BOM
                bom_vals = {'product_tmpl_id': product_tmpl.id, 'type': 'normal'}
                bom_vals['code'] = product_tmpl.default_code or 'BOM%06.0f' % product_tmpl.id
                new_bom = self.env['mrp.bom'].create(bom_vals)
                new_bom.create_attribute_value()
                product_tmpl.bom_id = new_bom
                res |= new_bom

        return res

    def create_product_variant(self, product_template_attribute_value_ids, custom_product_template_attribute_value=[]):
        """ Create product by request, check if there is bom to create, used by product configurator"""
        # [42,63,23,60,59] [{"custom_product_template_attribute_value_id":59,"attribute_value_name":"xx","custom_value":"2325"}]
        custom_product_template_attribute_value = json.loads(custom_product_template_attribute_value)
        product_template_attribute_value_ids = json.loads(product_template_attribute_value_ids)

        for attribute_value_data in custom_product_template_attribute_value:
            if not attribute_value_data:
                continue

            attribute_value_id = int(attribute_value_data.get('custom_product_template_attribute_value_id', 0))
            if not attribute_value_id:
                continue
            attribute_value = self.env['product.template.attribute.value'].browse(attribute_value_id)
            attribute = attribute_value.attribute_id
            if not attribute.auto_create:
                continue
            custom_value = attribute.get_value(attribute_value_data['custom_value'])
            if not custom_value:
                raise ValidationError(_("The custom value can't be null, create null value manually"))

            for line_value in attribute_value.attribute_id.value_ids:
                new_value = self.env['product.attribute.value']
                if line_value.get_value() == custom_value and not line_value.is_custom:
                    new_value = line_value
                    break

            if not new_value:
                new_value = attribute.value_ids[0].copy({'name': attribute_value_data['custom_value'],
                                                         'code': '', 'numeric': 0.0})
                new_value.update_value()
                attribute_value.product_tmpl_id.put_attribute_value(new_value)

            condition = [
                ('attribute_line_id', '=', attribute_value.attribute_line_id.id),
                ('product_attribute_value_id', '=', new_value.id)]

            new_attribute_value = self.env['product.template.attribute.value'].search(condition)
            product_template_attribute_value_ids.remove(attribute_value.id)
            product_template_attribute_value_ids.append(new_attribute_value.id)

        product_template_attribute_value_ids = json.dumps(product_template_attribute_value_ids)
        product_id = super().create_product_variant(product_template_attribute_value_ids)
        if product_id:
            new_product = self.env['product.product'].browse(product_id)
            new_product.create_bom()
            new_product.button_bom_cost()
        return product_id

    def button_create_variant(self):
        """button create Variants Dynamically in product template"""
        context = {}
        context.update({'product_template_id': self.id})
        v_id = self.env['ir.ui.view'].search([('name', '=', 'sale_product_configurator.product.configurator.view.form')]).id
        return {
            'view_mode': 'form',
            'view_id': v_id,
            'res_model': 'sale.product.configurator',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'domain': '[]',
            'context': {'default_product_template_id': self.id}
        }
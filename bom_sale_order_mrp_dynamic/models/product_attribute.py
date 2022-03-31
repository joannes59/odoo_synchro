# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class ProductAttribute(models.Model):
    _inherit = "product.attribute"

    convert_type = fields.Selection([('float', 'Numeric'), ('text', 'Text')],
                                    string='Value Type', default='text')
    code = fields.Char('code', help="Code of this attribute value")

    create_variant = fields.Selection([
        ('always', 'Instantly'),
        ('dynamic', 'Dynamically'),
        ('no_variant', 'Never')],
        default='dynamic',
        string="Variants Creation Mode",
        help="""- Instantly: All possible variants are created as soon as the attribute and its values are added to a product.
        - Dynamically: Each variant is created only when its corresponding attributes and values are added to a sales order.
        - Never: Variants are never created for the attribute.
        Note: the variants creation mode cannot be changed once the attribute is used on at least one product.""",
        required=True)

    def get_code_value(self, code=''):
        """ return the value, if not exist create one"""
        self.ensure_one()
        res = self.env['product.attribute.value']
        if not code:
            return res
        value_ids = self.value_ids.search([('code', '=', code), ('attribute_id', '=', self.id)])
        if not value_ids:
            value_ids = self.value_ids.search(
                [('name', '=', code), ('attribute_id', '=', self.id)])
            if value_ids:
                value_ids.code = code
                res = value_ids
            else:
                value_vals = {'code': code, 'attribute_id': self.id, 'name': code}
                res = self.env['product.attribute.value'].create(value_vals)
                _logger.info("Create new attribute value: %s %s " % (self.name, code))
        else:
            res = value_ids[0]
        return res


class ProductAttributeValue(models.Model):
    _inherit = "product.attribute.value"

    code = fields.Char('code', help="Code of this attribute value")

    def name_get(self):
        """ Return the code with the name"""
        res = []
        for value in self:
            if value.code and value.code != value.name:
                name = '(' + value.code + ') ' + value.name
            else:
                name = value.name
            res.append((value.id, name))
        return res

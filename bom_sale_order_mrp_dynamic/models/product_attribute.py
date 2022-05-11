# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.tools.float_utils import float_split_str
from odoo.exceptions import UserError, ValidationError

import unicodedata
import logging
_logger = logging.getLogger(__name__)


def remove_accents(input_str):
    only_ascii = unicodedata.normalize('NFD', input_str).encode('ascii', 'ignore')
    if type(only_ascii) == bytes:
        return only_ascii.decode()
    else:
        return only_ascii


def txt_cleanup(text):
    """Return a compatible text with python variable notation"""
    if text:
        text = remove_accents(text)
        text = text.strip()
        for char in '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~\n':
            text = text.replace(char, ' ')
        for char in [('    ', ' '), ('   ', ' '), ('  ', ' '), (' ', '_')]:
            text = text.replace(char[0], char[1])
        return text.lower()
    else:
        return ''


def convert_to_float(text):
    "convert dirty text to float or 0.0"
    out_str = ""
    if text:
        for char in text:
            if char.isnumeric() or char in [',', '.', '-']:
                out_str += char
            elif out_str:
                # if some digit is already loaded escape
                break
        # TODO: Use Country decimal notation function
        out_str = out_str.replace(',', '.')
        try:
            res = float(out_str or 0.0)
        except:
            res = 0.0
    else:
        res = 0.0
    return res


class ProductAttribute(models.Model):
    _inherit = "product.attribute"

    convert_type = fields.Selection([('float', 'Numeric'), ('text', 'Text')],
                                    string='Value Type', default='text')
    code = fields.Char('code', help="Code of this attribute value")
    auto_create = fields.Boolean("Auto create custom value",
                                 help="When custom value is completed, a new value is adding to this attribute")
    rounding = fields.Integer("rounding", default=1)


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

    @api.depends('code')
    def _check_unicity(self):
        for raw in self:
            if raw.code:
                if len(self.search([('code', '=', raw.code)])) > 1:
                    raise ValidationError(_('This code is already used: %s' % raw.code))

    def get_code_value(self, code=''):
        """ return the value with this code, if not exist create one: product.attribute.value"""
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
                res.update_value()
                _logger.info("Create new attribute value: %s %s " % (self.name, code))
        else:
            res = value_ids[0]
        return res

    def get_value(self, text_value):
        """ return value"""
        self.ensure_one()
        if self.convert_type == 'float':
            return convert_to_float(text_value)
        elif self.convert_type == 'text':
            return txt_cleanup(text_value)
        else:
            return False

    def update_value(self):
        """ Update the value by use code or name"""
        for attribute in self:
            for line in attribute.value_ids:
                line.update_value()

    def get_code(self):
        """ return the attribute code, update if not exist"""
        self.ensure_one()
        if not self.code:
            self.code = txt_cleanup(self.name)
        return self.code or ''

    @api.model
    def code_cleanup(self, code):
        """ Format the code """
        return txt_cleanup(code)


class ProductAttributeValue(models.Model):
    _inherit = "product.attribute.value"

    code = fields.Char('code', help="Code of this attribute value")
    numeric = fields.Float('Numeric value')

    @api.depends('code')
    def _check_unicity(self):
        for raw in self:
            if raw.code:
                if len(self.search([('code', '=', raw.code)])) > 1:
                    raise ValidationError(_('This code is already used: %s' % raw.code))

    def update_value(self):
        """ Update the value by use code or name"""
        for attribute_value in self:
            attribute_value.get_value()
            attribute_value.sequence_update()

    def sequence_update(self):
        """ Check sequence numerotation"""
        for attribute_value in self:
            if self.attribute_id.convert_type == 'float':
                self.sequence = str(int(self.numeric * 100.0))

    def get_value(self):
        """ return value"""
        self.ensure_one()
        if self.attribute_id.convert_type == 'float':
            if self.numeric:
                pass
            elif self.code:
                self.numeric = self.attribute_id.get_value(self.code)
            else:
                self.numeric = self.attribute_id.get_value(self.name)
                self.code = str(int(self.numeric))
                self.sequence_update()

            return self.numeric or 0.0

        elif self.attribute_id.convert_type == 'text':
            if self.code:
                pass
            else:
                self.code = self.attribute_id.get_value(self.name) or '?'
            return self.code
        else:
            return False

    def name_get(self):
        """ Return the code with the name"""
        res = []
        for value in self:
            if value.code and value.code != txt_cleanup(value.name):
                name = '(' + value.code + ') ' + value.name
            else:
                name = value.name
            res.append((value.id, name))
        return res

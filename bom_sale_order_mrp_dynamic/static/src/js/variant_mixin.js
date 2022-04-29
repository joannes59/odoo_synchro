odoo.define('bom_sale_order_mrp_dynamic.VariantMixin', function (require) {
'use strict';

var VariantMixin = require('sale.VariantMixin');
var ajax = require('web.ajax');


VariantMixin.selectOrCreateProduct = function ($container, productId, productTemplateId, useAjax) {
        var self = this;
        productId = parseInt(productId);
        productTemplateId = parseInt(productTemplateId);
        var productReady = Promise.resolve();
        if (productId) {
            productReady = Promise.resolve(productId);
        } else {
            var params = {
                product_template_id: productTemplateId,
                product_template_attribute_value_ids: JSON.stringify(self.getSelectedVariantValues($container)),
                custom_product_template_attribute_value: JSON.stringify(self.getCustomVariantValues($container)),
            };

            var route = '/sale/create_product_variant';
            if (useAjax) {
                productReady = ajax.jsonRpc(route, 'call', params);
            } else {
                productReady = this._rpc({route: route, params: params});
            }
        }

        return productReady;
    };




return VariantMixin;

});

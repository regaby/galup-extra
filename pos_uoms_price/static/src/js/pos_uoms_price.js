odoo.define('pos_uoms_price', function (require) {
    var models = require('point_of_sale.models');
    var screens = require('point_of_sale.screens');
    var PopupWidget = require('point_of_sale.popups');
    var gui = require('point_of_sale.gui');
    var core = require('web.core');
    var qweb = core.qweb;

    var choice_uoms_popup = PopupWidget.extend({
        template: 'choice_uoms_popup',
        previous_screen: 'products',
        show: function (options) {
            this._super();
            this.renderElement();
        },
        renderElement: function () {
            var self = this;
            this._super();
            this.$('.button.cancel').click(function () {
                self.gui.show_screen(self.previous_screen);
            });
            var current_order = this.pos.get('selectedOrder');
            if (current_order) {
                var selected_orderline = current_order.selected_orderline;
                if (selected_orderline) {
                    var product = selected_orderline.product;
                    var uom_items = this.pos.uoms_prices_by_product_id[product.id]
                    if (uom_items) {
                        var i = 0
                        while (i < uom_items.length) {
                            var uom_item = uom_items[i];
                            var uom_element = $(qweb.render('uom_item', {
                                widget: this,
                                uom_item: uom_item,
                            }));
                            this.$('.uoms-list').append(uom_element);
                            i++
                        }
                    }
                }
                this.$('.uom_item').click(function () {
                    var uom_id = parseInt($(this).attr('id'));
                    var uom_item = self.pos.uom_price_by_id[uom_id]
                    var order = self.pos.get_order()
                    var selected_orderline = order.selected_orderline;
                    if (selected_orderline && uom_item) {
                        selected_orderline.set_unit_price(uom_item.price)
                        selected_orderline.uom_id = uom_item.uom_id[0];
                        selected_orderline.uom = self.pos.units_by_id[uom_item.uom_id[0]];
                        selected_orderline.trigger('change', selected_orderline);
                        self.gui.show_screen(self.previous_screen);
                    }
                });
            }
        },
    });
    gui.define_popup({
        name: 'choice_uoms_popup',
        widget: choice_uoms_popup
    });
    var button_choice_uom = screens.ActionButtonWidget.extend({
        template: 'button_choice_uom',
        button_click: function () {
            console.log('click ....')
            var self = this;
            var order = this.pos.get_order()
            console.log('order ....')
            console.log(order)
            if (order) {
                var selected_orderline = order.selected_orderline;
                console.log('order line ....')
                console.log(selected_orderline)
                if (selected_orderline) {
                    var product = selected_orderline.product;
                    console.log('product ....')
                    console.log(product.id)
                    var uom_items = this.pos.uoms_prices_by_product_id[product.product_tmpl_id]
                    console.log('uom_items ....')
                    console.log(uom_items)
                    if (uom_items) {
                         self.gui.show_popup('choice_uoms_popup', {
                            confirm: function () {
                                console.log('culo ....')
                            },
                        });
                    }
                }

            }


        }
    });
    screens.define_action_button({
        'name': 'button_choice_uom',
        'widget': button_choice_uom,
        'condition': function () {
            return this.pos.config.multi_uoms;
        },
    });
    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        get_unit: function(){
            var res = _super_orderline.get_unit.apply(this, arguments);
            if (!this.uom) {
                return res;
            } else {
                return this.uom;
            }
        },
        init_from_JSON: function(json) {
            _super_orderline.init_from_JSON.apply(this, arguments);
            if (json.uom_id) {
                this.uom = this.pos.units_by_id[json.uom_id];
                this.uom_id = this.uom.id;
            }
        },
        export_as_JSON: function(){
            var json = _super_orderline.export_as_JSON.apply(this, arguments);
            if (this.uom_id) {
                json.uom_id = this.uom_id
            }
            return json;
        },
    });
    models.load_models([
        {
            model: 'product.uom.price',
            fields: [],
            domain: [],
            context: {'pos': true},
            loaded: function (self, uoms_prices) {
                self.uom_price_by_id = {}
                self.uoms_prices_by_product_id = {}
                var i = 0
                while (i < uoms_prices.length) {
                    var item = uoms_prices[i]
                    self.uom_price_by_id[item.id] = item;
                    if (!self.uoms_prices_by_product_id[item.product_id[0]]) {
                        self.uoms_prices_by_product_id[item.product_id[0]] = [item]
                    } else {
                        self.uoms_prices_by_product_id[item.product_id[0]].push(item)
                    }
                    i++;
                }
            },
        },
    ]);
});
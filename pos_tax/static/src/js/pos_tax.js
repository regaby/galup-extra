odoo.define('pos_tax', function (require) {
    var models = require('point_of_sale.models');
    var PopupWidget = require('point_of_sale.popups');
    var screens = require('point_of_sale.screens');
    var gui = require('point_of_sale.gui');
    var core = require('web.core');
    var qweb = core.qweb;

    var _super_order_line = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        export_for_printing: function () {
            var datas_print = _super_order_line.export_for_printing.apply(this, arguments);
            datas_print['tax_amount'] = this.get_tax();
            return datas_print;
        }
    });

    models.load_fields("account.tax", ['pos_enable']);

    var popup_select_tax = PopupWidget.extend({
        template: 'popup_select_tax',
        show: function (options) {
            var self = this;
            this.options = options;
            this.line_selected = options.line_selected;
            var product = this.line_selected.get_product();
            var taxes_ids = product.taxes_id;
            this._super(options);
            var taxes = []
            for (var i = 0; i < this.pos.taxes.length; i++) {
                if (this.pos.taxes[i]['pos_enable']) {
                    taxes.push(this.pos.taxes[i]);
                }
            }
            this.taxes_selected = [];
            for (var i = 0; i < taxes.length; i++) {
                var tax = taxes[i];
                var tax_selected = _.find(taxes_ids, function (tax_id) {
                    return tax_id == tax['id'];
                })
                if (tax_selected) {
                    tax.selected = true;
                    this.taxes_selected.push(tax);
                } else {
                    tax.selected = false;
                }
            }
            self.$el.find('div.body').html(qweb.render('tax_item', {
                taxes: taxes,
                widget: this
            }));
            $('.tax-item').click(function () {
                var tax_id = parseInt($(this).data('id'));
                var tax = self.pos.taxes_by_id[tax_id];
                if (tax) {
                    if ($(this).closest('.product').hasClass("item-selected") == true) {
                        $(this).closest('.product').toggleClass("item-selected");
                        self.taxes_selected = _.filter(self.taxes_selected, function (tax_selected) {
                            return tax_selected['id'] != tax['id']
                        })
                    } else {
                        $(this).closest('.product').toggleClass("item-selected");
                        self.taxes_selected.push(tax)
                    }
                }
            });
            $('.cancel').click(function () {
                self.gui.close_popup();
            });
            $('.add_taxes').click(function () {
                var order = self.pos.get_order();
                if (!order) {
                    return;
                }
                if (self.taxes_selected.length == 0) {
                    var line_selected = self.line_selected;
                    var product = line_selected.get_product();
                    product.taxes_id = [];
                    line_selected.trigger('change', line_selected);
                    line_selected.order.trigger('change', line_selected.order);
                    return self.pos.gui.close_popup();
                }
                var line_selected = self.line_selected;
                var product = line_selected.get_product();
                product.taxes_id = [];
                for (var i = 0; i < self.taxes_selected.length; i++) {
                    var tax = self.taxes_selected[i];
                    product.taxes_id.push(tax['id']);
                }
                line_selected.trigger('change', line_selected);
                line_selected.order.trigger('change', line_selected.order);
                return self.pos.gui.close_popup();
            });
        }
    });
    gui.define_popup({name: 'popup_select_tax', widget: popup_select_tax});

    var button_change_tax = screens.ActionButtonWidget.extend({
        template: 'button_change_tax',
        init: function (parent, options) {
            this._super(parent, options);
        },
        button_click: function () {
            var self = this;
            var order = this.pos.get_order();
            if (order.get_selected_orderline()) {
                var line_selected = order.get_selected_orderline();
                return this.gui.show_popup('popup_select_tax', {
                    title: 'Please choice tax',
                    line_selected: line_selected,
                    confirm: function () {
                        return self.pos.gui.close_popup();
                    },
                    cancel: function () {
                        return self.pos.gui.close_popup();
                    }
                });
            } /*else {
                this.gui.show_popup('alert_result', {
                    title: 'Warning',
                    body: 'Please choice line'
                })
            }*/
        }
    });

    screens.define_action_button({
        'name': 'button_change_tax',
        'widget': button_change_tax,
        'condition': function () {
            return this.pos.config && this.pos.config.update_tax;
        }
    });

});

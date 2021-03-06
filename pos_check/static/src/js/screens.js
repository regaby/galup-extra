odoo.define('pos_check.screens', function (require) {
"use strict";

var screens = require('point_of_sale.screens');

screens.PaymentScreenWidget.include({
    show_popup_check_info: function(options) {
        var self = this;
        window.document.body.removeEventListener('keypress', self.keyboard_handler);
        window.document.body.removeEventListener('keydown', self.keyboard_keydown_handler);
        this.gui.show_popup('check-info-input',{
            data: options.data,
            config_check: options.config_check,
            validate_info: function(infos){
                this.$('input').removeClass('error');
                this.$('select').removeClass('error');
                if(this.options.config_check.bank_required && !infos.check_bank_id) {
                    this.$('select[name=check_bank_id]').addClass('error');
                    this.$('select[name=check_bank_id]').focus();
                    return false;
                }
                if(this.options.config_check.bank_acc_required && !infos.check_bank_acc) {
                    this.$('input[name=check_bank_acc]').addClass('error');
                    this.$('input[name=check_bank_acc]').focus();
                    return false;
                }
                if(this.options.config_check.number_required && !infos.check_number) {
                    this.$('input[name=check_number]').addClass('error');
                    this.$('input[name=check_number]').focus();
                    return false;
                }
                if(this.options.config_check.owner_required && !infos.check_owner) {
                    this.$('input[name=check_owner]').addClass('error');
                    this.$('input[name=check_owner]').focus();
                    return false;
                }
                if(this.options.config_check.owner_vat_required && !infos.check_owner_vat) {
                    this.$('input[name=check_owner_vat]').addClass('error');
                    this.$('input[name=check_owner_vat]').focus();
                    return false;
                }
                if(this.options.config_check.pay_date_required && !infos.check_pay_date) {
                    this.$('input[name=check_pay_date]').addClass('error');
                    this.$('input[name=check_pay_date]').focus();
                    return false;
                }
                if(this.options.config_check.cbu_required && !infos.check_cbu) {
                    this.$('input[name=check_cbu]').addClass('error');
                    this.$('input[name=check_cbu]').focus();
                    return false;
                }
                if(this.options.config_check.reference_required && !infos.reference) {
                    this.$('input[name=reference]').addClass('error');
                    this.$('input[name=reference]').focus();
                    return false;
                }
                return true;
            },
            confirm: function(infos){
                options.confirm.call(self, infos);
                self.reset_input();
                self.render_paymentlines();
                window.document.body.addEventListener('keypress', self.keyboard_handler);
                window.document.body.addEventListener('keydown', self.keyboard_keydown_handler);
            },
            cancel: function(){
                window.document.body.addEventListener('keypress', self.keyboard_handler);
                window.document.body.addEventListener('keydown', self.keyboard_keydown_handler);
            },
        });
    },

    get_config_check: function(cashregister, partner_name, main_id_number) {
        return {
            'bank_visible': cashregister.journal.check_bank_name_visible,
            'bank_required': cashregister.journal.check_bank_name_required,
            'bank_acc_visible': cashregister.journal.check_bank_acc_visible,
            'bank_acc_required': cashregister.journal.check_bank_acc_required,
            'owner_visible': cashregister.journal.check_owner_visible,
            'owner_required': cashregister.journal.check_owner_required,
            'owner_vat_visible': cashregister.journal.check_owner_vat_visible,
            'owner_vat_required': cashregister.journal.check_owner_vat_required,
            'pay_date_visible': cashregister.journal.check_pay_date_visible,
            'pay_date_required': cashregister.journal.check_pay_date_required,
            'cbu_visible': cashregister.journal.check_cbu_visible,
            'cbu_required': cashregister.journal.check_cbu_required,
            'reference_visible': cashregister.journal.reference_visible,
            'reference_required': cashregister.journal.reference_required,
            'number_visible': cashregister.journal.check_number_visible,
            'number_required': cashregister.journal.check_number_required,
            'partner_name': partner_name,
            'main_id_number': main_id_number,
        }
    },

    click_paymentmethods: function(id) {
        var self = this;
        var cashregister = null;
        for ( var i = 0; i < this.pos.cashregisters.length; i++ ) {
            if ( this.pos.cashregisters[i].journal_id[0] === id ){
                cashregister = this.pos.cashregisters[i];
                break;
            }
        }
        var order = this.pos.get_order();
        var partner_name = ''
        var main_id_number = ''
        if (order.changed.client) {
            partner_name = order.changed.client.name;
            main_id_number = order.changed.client.main_id_number;
        }
        if (order.selected_orderline) {
            var product_name = order.selected_orderline.product.display_name;
        }
        if (cashregister.journal.check_info_required) {
            if (cashregister.journal.name == 'Efectivo' && product_name == 'RETIRAR DINERO') {
                console.log('retiro dinero....')
                this.show_popup_check_info({
                    config_check: this.get_config_check(cashregister, partner_name, main_id_number),
                    data: {},
                    confirm: function(infos) {
                        //merge infos to new paymentline
                        self.pos.get_order().add_paymentline_with_check(cashregister, infos);
                    },
                });
            }
            else if (cashregister.journal.name != 'Efectivo') {
                console.log(cashregister.journal.name)
                console.log('else...')
                this.show_popup_check_info({
                    config_check: this.get_config_check(cashregister, partner_name, main_id_number),
                    data: {},
                    confirm: function(infos) {
                        //merge infos to new paymentline
                        self.pos.get_order().add_paymentline_with_check(cashregister, infos);
                    },
                });

            }
            else {
                this._super(id);
            }
        }
        else {
            this._super(id);
        }
    },

    click_numpad: function(button) {
        var paymentlines = this.pos.get_order().get_paymentlines();
        var open_paymentline = false;

        for (var i = 0; i < paymentlines.length; i++) {
            if (! paymentlines[i].paid) {
                open_paymentline = true;
            }
        }

        if (! open_paymentline) {
            var cashregister = null;
            for ( var i = 0; i < this.pos.cashregisters.length; i++ ) {
                if (!this.pos.cashregisters[i].journal.check_info_required){
                    cashregister = this.pos.cashregisters[i];
                    break;
                }
            }
            this.pos.get_order().add_paymentline(cashregister);
            this.render_paymentlines();
        }

        this.payment_input(button.data('action'));
    },

    click_check_info_paymentline: function(cid){
        var self = this;
        var lines = this.pos.get_order().get_paymentlines();
        for ( var i = 0; i < lines.length; i++ ) {
            if (lines[i].cid === cid) {
                var cashregister = lines[i].cashregister;
                this.show_popup_check_info({
                    config_check: {
                        'bank_visible': cashregister.journal.check_bank_name_visible,
                        'bank_required': cashregister.journal.check_bank_name_required,
                        'bank_acc_visible': cashregister.journal.check_bank_acc_visible,
                        'bank_acc_required': cashregister.journal.check_bank_acc_required,
                        'owner_visible': cashregister.journal.check_owner_visible,
                        'owner_required': cashregister.journal.check_owner_required,
                        'owner_vat_visible': cashregister.journal.check_owner_vat_visible,
                        'owner_vat_required': cashregister.journal.check_owner_vat_required,
                        'pay_date_visible': cashregister.journal.check_pay_date_visible,
                        'pay_date_required': cashregister.journal.check_pay_date_required,
                        'cbu_visible': cashregister.journal.check_cbu_visible,
                        'cbu_required': cashregister.journal.check_cbu_required,
                        'reference_visible': cashregister.journal.check_reference_visible,
                        'reference_required': cashregister.journal.check_reference_required,
                        'number_visible': cashregister.journal.check_number_visible,
                        'number_required': cashregister.journal.check_number_required,
                    },
                    data: lines[i],
                    confirm: function(infos) {
                        //merge infos to updated paymentline
                        self.pos.get_order().update_paymentline_with_check(lines[i], infos);
                    },
                });
                return;
            }
        }
    },

    render_paymentlines: function() {
        var self = this;
        this._super();
        var lines = this.$('.paymentlines-container table.paymentlines');
        lines.on('click','.check-info-button', function(){
            self.click_check_info_paymentline($(this).data('cid'));
        });
    }

});

return screens;
});

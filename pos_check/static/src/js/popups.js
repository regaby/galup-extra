odoo.define('pos_check.popups', function (require) {
"use strict";

var PopupWidget = require('point_of_sale.popups');
var gui = require('point_of_sale.gui');

var CheckInfoWidget = PopupWidget.extend({
    template: 'CheckInfoWidget',
    show: function(options){
        options = options || {};
        this._super(options);
        this.renderElement();
        var partner_name = options.config_check.partner_name;
        var cuit = options.config_check.main_id_number;
        this.$('input[name=check_owner_vat]').val(cuit);
        this.$('input[name=check_owner]').val(partner_name);
        this.$('.popup-checkinfo .detail')[0].focus()
    },
    get_infos: function() {
        var cuit = ''
        var cbu = ''
        if (this.$('input[name=check_cbu]').val() != undefined) {
            cbu = this.$('input[name=check_cbu]').val();
        }
        if (this.$('input[name=check_owner_vat]').val() != undefined) {
            cuit = this.$('input[name=check_owner_vat]').val();
        }
        if (cuit.length > 0 && cuit.length != 11) {
            this.gui.show_popup('error',('El campo CUIT debe tener 11 caracteres'));
            return {};
        }
        if (cbu.length > 0 && cbu.length != 22) {
            this.gui.show_popup('error',('El campo CBU debe tener 22 caracteres'));
            return {};
        }
        return {
            'check_bank_id' : parseInt(this.$('select[name=check_bank_id]').val()) || undefined,
            'check_bank_acc': this.$('input[name=check_bank_acc]').val(),
            'check_number'  : this.$('input[name=check_number]').val(),
            'check_owner'   : this.$('input[name=check_owner]').val(),
            'check_owner_vat'   : cuit,
            'check_pay_date'   : this.$('input[name=check_pay_date]').val(),
            'check_cbu'   : cbu,
            'reference'   : this.$('input[name=reference]').val(),
        };
    },
    click_confirm: function(){

        var infos = this.get_infos();
        var valid = true;
        if(this.options.validate_info){
            valid = this.options.validate_info.call(this, infos);
        }

        if(!valid) return;

        this.gui.close_popup();
        if( this.options.confirm ){
            this.options.confirm.call(this, infos);
        }
    },
});
gui.define_popup({name:'check-info-input', widget: CheckInfoWidget});


return {
    PopupWidget: PopupWidget,
    CheckInfoWidget: CheckInfoWidget,
};
});

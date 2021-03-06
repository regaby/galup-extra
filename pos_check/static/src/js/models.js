odoo.define('pos_check.models', function (require) {
"use strict";

var models = require('point_of_sale.models');

//load new field 'check_info_required', etc
models.load_fields("account.journal", ['check_info_required', 'check_auto_fill_amount', 'is_check', 'check_bank_name_visible',
'check_bank_name_required', 'check_bank_acc_visible', 'check_bank_acc_required', 'check_owner_visible', 'check_owner_required',
'check_owner_vat_visible', 'check_owner_vat_required', 'check_pay_date_visible', 'check_pay_date_required',
'check_cbu_visible', 'check_cbu_required', 'reference_visible', 'reference_required', 'name','check_number_visible',
'check_number_required']);

//load model res.bank
models.load_models({
    model: 'res.bank',
    fields: ['name'],
    loaded: function(self, banks){
        self.banks = banks;
    },
}, {after: 'res.country'});

var paymentline_super = models.Paymentline.prototype;
models.Paymentline = models.Paymentline.extend({
    init_from_JSON: function (json) {
        paymentline_super.init_from_JSON.apply(this, arguments);

        this.check_bank_id = json.check_bank_id;
        this.check_bank_acc = json.check_bank_acc;
        this.check_number = json.check_number;
        this.check_owner = json.check_owner;
        this.check_owner_vat = json.check_owner_vat;
        this.check_pay_date = json.check_pay_date;
        this.check_cbu = json.check_cbu;
        this.reference = json.reference;
    },
    export_as_JSON: function () {
        return _.extend(paymentline_super.export_as_JSON.apply(this, arguments), {
            check_bank_id: this.check_bank_id,
            check_bank_acc: this.check_bank_acc,
            check_number: this.check_number,
            check_owner: this.check_owner,
            check_owner_vat: this.check_owner_vat,
            check_pay_date: this.check_pay_date,
            check_cbu: this.check_cbu,
            reference: this.reference,
        });
    },
});

var order_super = models.Order.prototype;
models.Order = models.Order.extend({
    add_paymentline_with_check: function(cashregister, infos) {
        this.assert_editable();
        var newPaymentline = new models.Paymentline({},{order: this, cashregister:cashregister, pos: this.pos});
        $.extend(newPaymentline, infos);
        if(cashregister.journal.type !== 'cash' || this.pos.config.iface_precompute_cash || cashregister.journal.check_auto_fill_amount){
            newPaymentline.set_amount( Math.max(this.get_due(),0) );
        }
        this.paymentlines.add(newPaymentline);
        this.select_paymentline(newPaymentline);
    },

    update_paymentline_with_check: function(paymentline, infos) {
        this.assert_editable();
        $.extend(paymentline, infos);
        this.select_paymentline(paymentline);
    },
});

return models;
});

odoo.define('pos_fields_partner.PosModel', function (require) {
"use strict";

var models = require('point_of_sale.models');
pos_model.load_fields("res.partner",['main_id_category_id']);

models.load_models({
    model: 'res.partner.id_category',
    fields: ['id', 'code', 'name'],
    loaded: function(self, type_doc){
        self.type_doc = type_doc;

    },
}, {after: 'res.country'});



var _super_posmodel = models.PosModel.prototype;
models.PosModel = models.PosModel.extend({

    initialize: function (session, attributes) {
            var partner_model = _.find(this.models, function(model){ return model.model === 'res.partner'; });
            partner_model.fields.push('main_id_category_id');
            
           this.main_id_category_id= main_id_category_id;
           this.type_doc = type_doc;
           return _super_posmodel.initialize.call(this, session, attributes);
        },
},
});

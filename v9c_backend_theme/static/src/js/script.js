openerp.v9c_backend_theme = function(instance){
    var _t = instance.web._t,
    _lt = instance.web._lt;
    var QWeb = instance.web.qweb;

    instance.web.WebClient.include({

        start: function() {
            this.set('title_part', {"zopenerp": "Galup"});
            return this._super();
            },
        });
}
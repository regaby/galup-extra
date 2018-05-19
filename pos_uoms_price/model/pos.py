from openerp import api, fields, models, _


class product_template(models.Model):
    _inherit = "product.template"

    multi_uoms = fields.Boolean('Multi uoms')
    price_uom_ids = fields.One2many('product.uom.price', 'product_id', string='Uoms Price extra')


class product_uom_price(models.Model):
    _name = "product.uom.price"

    uom_id = fields.Many2one('product.uom', 'Uom', required=1)
    product_id = fields.Many2one('product.template', 'Product', domain=[('available_in_pos', '=', True)], required=1)
    price = fields.Float('Price/Item', required=1, default=0)
    ration = fields.Float('Ration', help='How much bigger or smaller with Root of unit on this product', required=1)
    root_uom_id = fields.Many2one(realted='product_id.uom_id', relation='product.uom', string='Product Unit of Measure',
                                  readonly=1)


class pos_config(models.Model):
    _inherit = 'pos.config'

    multi_uoms = fields.Boolean('Multi UOMs')


class pos_order(models.Model):
    _inherit = "pos.order"

    @api.multi
    def write(self, vals):
        res = super(pos_order, self).write(vals)
        if vals.has_key('picking_id') and vals.get('picking_id'):
            for order in self:
                picking = self.env['stock.picking'].browse(vals.get('picking_id'))
                moves = self.env['stock.move'].search([('picking_id', '=', picking.id)]).unlink()
                location_id = order.location_id.id
                picking_type = order.picking_type_id
                if order.partner_id:
                    destination_id = order.partner_id.property_stock_customer.id
                else:
                    if (not picking_type) or (not picking_type.default_location_dest_id):
                        customerloc, supplierloc = self.env['stock.warehouse']._get_partner_locations()
                        destination_id = customerloc.id
                    else:
                        destination_id = picking_type.default_location_dest_id.id
                for line in order.lines.filtered(lambda l: l.product_id.type in ['product', 'consu']):
                    uom = line.uom_id if line.uom_id else None
                    uom_prices = None
                    if uom:
                        uom_prices = self.env['product.uom.price'].search(
                            [('uom_id', '=', uom[0].id), ('product_id', '=', line.product_id.id)])
                    if uom_prices:
                        vals = {
                            'name': line.name,
                            'product_uom': line.product_id.uom_id.id,
                            'picking_id': picking.id,
                            'picking_type_id': picking.picking_type_id.id,
                            'product_id': line.product_id.id,
                            'product_uom_qty': abs(uom_prices[0].ration * line.qty),
                            'state': 'draft',
                            'location_id': location_id,
                            'location_dest_id': destination_id,
                        }
                    else:
                        vals = {
                            'name': line.name,
                            'product_uom': line.product_id.uom_id.id,
                            'picking_id': picking.id,
                            'picking_type_id': picking.picking_type_id.id,
                            'product_id': line.product_id.id,
                            'product_uom_qty': abs(line.qty),
                            'state': 'draft',
                            'location_id': location_id,
                            'location_dest_id': destination_id,
                        }
                    self.env['stock.move'].create(vals)
        return res


class pos_order_line(models.Model):
    _inherit = "pos.order.line"

    uom_id = fields.Many2one('product.uom', 'Uom', readonly=1)

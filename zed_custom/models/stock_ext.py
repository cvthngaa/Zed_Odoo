# -*- coding: utf-8 -*-
from odoo import models, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def zed_create_consumption(self, lines, company, barista=False, pos_order=False, note=False):
        """
        Tạo phiếu tiêu hao (internal) và tự xác nhận -> Done.
        :param lines: [{'product_id': int, 'qty': float}] (uom = product.uom_id)
        """
        if not lines:
            return False

        # 1) Lấy Operation Type cho internal (Internal Transfers)
        # Mặc định external id: 'stock.picking_type_internal'
        consume_type = self.env.ref('stock.picking_type_internal', raise_if_not_found=False)
        if not consume_type:
            consume_type = self.env['stock.picking.type'].search([('code', '=', 'internal')], limit=1)
        if not consume_type:
            raise UserError(_("Không tìm thấy Operation Type (internal) để tạo phiếu tiêu hao."))

        # 2) Xác định location nguồn/đích
        src = consume_type.default_location_src_id or self.env['stock.location'].search([('usage', '=', 'internal')], limit=1)
        dest = consume_type.default_location_dest_id \
               or self.env['stock.location'].search([('scrap_location', '=', True)], limit=1) \
               or self.env['stock.location'].search([('usage', '=', 'inventory')], limit=1)
        if not (src and dest):
            raise UserError(_("Thiếu Location internal hoặc scrap/inventory để tạo phiếu tiêu hao."))

        # 3) Tạo picking
        picking_vals = {
            'company_id': company.id,
            'picking_type_id': consume_type.id,
            'location_id': src.id,
            'location_dest_id': dest.id,
            'origin': pos_order.name if pos_order else (note or _('Zed Consumption')),
            'note': note or False,
            'zed_move_type': 'consume',
            'zed_pos_order_id': pos_order.id if pos_order else False,
        }
        picking = self.create(picking_vals)

        # 4) Tạo move cho từng nguyên liệu
        Move = self.env['stock.move']
        for item in lines:
            product = self.env['product.product'].browse(int(item['product_id']))
            qty = float(item.get('qty') or 0.0)
            if not product or qty <= 0:
                continue

            Move.create({
                'description_picking': product.display_name,
                'company_id': company.id,
                'product_id': product.id,
                'product_uom': product.uom_id.id,
                'product_uom_qty': qty,           # demand
                'location_id': src.id,
                'location_dest_id': dest.id,
                'picking_id': picking.id,
            })

        # 5) Xác nhận & hoàn tất
        picking.action_confirm()
        picking.action_assign()

        # Đảm bảo có qty_done trước khi validate
        # (điền cho cả move và move line cho chắc trên Odoo 19)
        for move in picking.move_ids_without_package:
            if not move.quantity_done:
                move.quantity_done = move.product_uom_qty
        for ml in picking.move_line_ids:
            if not ml.qty_done:
                # move line đã được tạo với product_uom_qty sau action_assign
                ml.qty_done = ml.product_uom_qty

        picking.button_validate()
        return picking

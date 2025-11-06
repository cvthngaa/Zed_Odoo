# -*- coding: utf-8 -*-
from odoo import models, api, _

class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.model
    def zed_create_consumption(self, lines, company=None, barista=None, pos_order=None, note=None):
        """Tạo 1 picking 'tiêu hao nguyên liệu' từ danh sách dòng nguyên liệu.
        lines: [{'product_id': int, 'qty': float}, ...]
        """
        StockLocation = self.env['stock.location']
        Move = self.env['stock.move']
        company = company or self.env.company

        # Nguồn: internal; Đích: scrap hoặc inventory (tiêu hao)
        src = StockLocation.search([('usage', '=', 'internal'), ('company_id', 'in', [company.id, False])], limit=1)
        dest = StockLocation.search([('scrap_location', '=', True), ('company_id', 'in', [company.id, False])], limit=1) \
            or StockLocation.search([('usage', '=', 'inventory'), ('company_id', 'in', [company.id, False])], limit=1)

        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'internal'),
            ('warehouse_id.company_id', 'in', [company.id, False])
        ], limit=1)

        picking_vals = {
            'picking_type_id': picking_type.id if picking_type else False,
            'location_id': src.id if src else False,
            'location_dest_id': dest.id if dest else False,
            'origin': pos_order and f"POS {pos_order.name}" or "ZED-CONSUME",
            'note': note or False,
            'company_id': company.id,
        }
        # field tùy biến nếu có
        if 'zed_move_type' in self._fields:
            picking_vals['zed_move_type'] = 'consume'
        if 'zed_pos_order_id' in self._fields and pos_order:
            picking_vals['zed_pos_order_id'] = pos_order.id
        if 'zed_barista_id' in self._fields and barista:
            picking_vals['zed_barista_id'] = barista.id

        picking = self.create(picking_vals)

        move_vals = []
        for item in lines:
            prod = self.env['product.product'].browse(item['product_id'])
            qty = float(item['qty'])
            if qty <= 0 or not prod:
                continue
            mv = {
                'name': f"[CONSUME] {prod.display_name}",
                'product_id': prod.id,
                'product_uom': prod.uom_id.id,
                'product_uom_qty': qty,
                'quantity_done': qty,
                'location_id': picking.location_id.id,
                'location_dest_id': picking.location_dest_id.id,
                'picking_id': picking.id,
                'company_id': company.id,
            }
            if 'zed_is_consumption' in Move._fields:
                mv['zed_is_consumption'] = True
            if 'zed_source_order' in Move._fields and pos_order:
                mv['zed_source_order'] = pos_order.id
            move_vals.append(mv)

        if move_vals:
            Move.create(move_vals)

        # Xác nhận & hoàn tất
        picking.action_confirm()
        picking.action_assign()
        picking.button_validate()
        return picking

# -*- coding: utf-8 -*-
from collections import defaultdict
from odoo import models, _


class PosOrder(models.Model):
    _inherit = 'pos.order'

    def _zed_payload_consumption(self):
        """
        Gom NGUYÊN LIỆU cần trừ kho theo công thức:
        - Ưu tiên BoM của product.product (biến thể)
        - Fallback sang BoM của product.template
        Trả về: [{'product_id': int(product.product id), 'qty': float}, ...]
        """
        agg = defaultdict(float)  # product.product.id -> qty (theo uom chuẩn của nguyên liệu)

        for line in self.lines:
            if line.qty <= 0:
                continue

            product = line.product_id  # product.product bán ra
            if not product:
                continue

            # LẤY BoM ƯU TIÊN BIẾN THỂ
            bom = product.zed_get_bom()
            if not bom:
                continue

            # Cộng dồn nguyên liệu
            for bl in bom.bom_line_ids:
                mat = bl.product_id  # product.product nguyên liệu (bắt buộc)
                if not mat:
                    continue
                qty_need = (bl.product_qty or 0.0) * line.qty

                # Quy đổi về UoM chuẩn của nguyên liệu nếu BoM dùng UoM khác
                if bl.product_uom_id and bl.product_uom_id != mat.uom_id:
                    qty_need = bl.product_uom_id._compute_quantity(
                        qty_need, mat.uom_id, rounding_method='HALF-UP'
                    )

                # (tuỳ chọn) chỉ trừ kho với Storable:
                # if mat.detailed_type != 'product':
                #     continue

                agg[mat.id] += qty_need

        return [{'product_id': pid, 'qty': qty} for pid, qty in agg.items() if qty > 0]

    def action_pos_order_paid(self):
        """
        Sau khi thanh toán POS:
        - Lấy payload nguyên liệu theo công thức
        - Tạo phiếu tiêu hao nội bộ và tự Done
        """
        res = super().action_pos_order_paid()
        Picking = self.env['stock.picking']

        for order in self:
            payload = order._zed_payload_consumption()
            if not payload:
                continue

            barista = getattr(order, 'employee_id', False) or getattr(order.session_id, 'employee_id', False)

            Picking.sudo().zed_create_consumption(
                lines=payload,
                company=order.company_id,
                barista=barista,
                pos_order=order,
                note=_("Tiêu hao từ POS Order %s") % (order.name,),
            )
        return res

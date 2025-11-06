# -*- coding: utf-8 -*-
from collections import defaultdict
from odoo import models, _

class PosOrder(models.Model):
    _inherit = 'pos.order'

    def _zed_payload_consumption(self):
        """Gom nguyên liệu cần trừ theo công thức của từng line POS.
        Trả về [{'product_id': int, 'qty': float}, ...]
        """
        agg = defaultdict(float)
        for line in self.lines:
            if line.qty <= 0:
                continue
            recipe = line.product_id.product_tmpl_id.zed_recipe_id
            if not recipe:
                continue
            for r in recipe.line_ids:
                mat = r.material_id  # product.product
                if not mat:
                    continue
                agg[mat.id] += (r.qty or 0.0) * line.qty
        return [{'product_id': pid, 'qty': q} for pid, q in agg.items() if q > 0]

    def action_pos_order_paid(self):
        """Sau khi thanh toán POS: tự tạo Picking tiêu hao nguyên liệu."""
        res = super().action_pos_order_paid()
        Picking = self.env['stock.picking']
        for order in self:
            payload = order._zed_payload_consumption()
            if not payload:
                continue

            barista = False
            if hasattr(order.session_id, "employee_id"):
                barista = order.session_id.employee_id

            # Gọi helper trong stock_ext.py
            Picking.sudo().zed_create_consumption(
                lines=payload,
                company=order.company_id,
                barista=barista,
                pos_order=order,
                note=_("Tiêu hao từ POS Order %s") % (order.name,),
            )
        return res

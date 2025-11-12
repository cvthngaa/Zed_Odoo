# -*- coding: utf-8 -*-
from odoo import models, fields

# ===============================
#  PRODUCT.TEMPLATE (ZED)
# ===============================
class ProductTemplate(models.Model):
    _inherit = "product.template"

    # Dùng BoM theo template (fallback)
    zed_recipe_id = fields.Many2one(
        "mrp.bom",
        string="BoM (Zed)",
        domain="[('product_tmpl_id', '=', id)]",
        help="BoM chung cho template. Nếu biến thể có BoM riêng thì sẽ ưu tiên BoM biến thể.",
    )
    zed_type = fields.Selection(
        [
            ("ingredient", "Nguyên liệu"),
            ("semi", "Bán thành phẩm"),
            ("finished", "Thành phẩm"),
        ],
        string="Loại Zed",
        default="finished",
    )
    low_stock_threshold = fields.Float("Ngưỡng cảnh báo tồn (Zed)", default=0.0)


# ===============================
#  PRODUCT.PRODUCT (ZED) – BoM theo BIẾN THỂ
# ===============================
class ProductProduct(models.Model):
    _inherit = "product.product"

    # BoM ở cấp biến thể (ưu tiên dùng)
    zed_recipe_id = fields.Many2one(
        "mrp.bom",
        string="BoM (Zed) - Variant",
        domain="[('product_id', '=', id)]",
        help="Nếu có, POS sẽ tiêu hao theo BoM của biến thể này. Nếu trống sẽ fallback BoM của template.",
    )

    def zed_get_bom(self):
        """Trả về BoM ưu tiên:
        1) mrp.bom gắn trực tiếp vào product.product (field zed_recipe_id hoặc search product_id)
        2) mrp.bom gắn vào product.template (field zed_recipe_id hoặc search theo product_tmpl_id)
        """
        self.ensure_one()
        Bom = self.env["mrp.bom"]
        # 1) BoM set tay cho biến thể
        if self.zed_recipe_id:
            return self.zed_recipe_id
        # 1b) Search theo product_id
        bom = Bom.search([("product_id", "=", self.id)], limit=1)
        if bom:
            return bom
        # 2) BoM set tay cho template
        if self.product_tmpl_id.zed_recipe_id:
            return self.product_tmpl_id.zed_recipe_id
        # 2b) Search theo template (BoM chung)
        return Bom.search(
            [("product_tmpl_id", "=", self.product_tmpl_id.id), ("product_id", "=", False)],
            limit=1,
        )


# ===============================
#  NHÂN VIÊN (HR EMPLOYEE)
# ===============================
class HrEmployee(models.Model):
    _inherit = "hr.employee"

    is_barista = fields.Boolean("Là Barista", default=False)
    barista_level = fields.Selection(
        [("junior", "Junior"), ("mid", "Mid"), ("senior", "Senior"), ("lead", "Lead")],
        string="Cấp độ Barista",
    )
    certification = fields.Char("Chứng chỉ/Ghi chú tay nghề")


# ===============================
#  KHÁCH HÀNG (RES.PARTNER)
# ===============================
class ResPartner(models.Model):
    _inherit = "res.partner"

    is_member = fields.Boolean("Thành viên The Zed", default=False)
    loyalty_points = fields.Integer("Điểm tích lũy", default=0)
    allergy_notes = fields.Char("Dị ứng (sữa, hạt, gluten...)")
    sweetness_pref = fields.Selection(
        [
            ("no_sugar", "Không đường"),
            ("less_sugar", "Ít đường"),
            ("normal", "Vừa ngọt"),
            ("sweet", "Ngọt"),
        ],
        string="Độ ngọt ưa thích",
        default="normal",
    )
    ice_pref = fields.Selection(
        [
            ("no_ice", "Không đá"),
            ("less_ice", "Ít đá"),
            ("normal", "Vừa đá"),
            ("more_ice", "Nhiều đá"),
        ],
        string="Độ đá ưa thích",
        default="normal",
    )


class PosOrder(models.Model):
    _inherit = "pos.order"

    member_used = fields.Many2one("res.partner", string="Thành viên sử dụng")
    earned_points = fields.Integer("Điểm thưởng nhận được", default=0)


# ===============================
#  POS ORDER LINE
# ===============================
class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    sweetness = fields.Selection(
        [
            ("no_sugar", "Không đường"),
            ("less_sugar", "Ít đường"),
            ("normal", "Vừa ngọt"),
            ("sweet", "Ngọt"),
        ],
        string="Độ ngọt",
        default="normal",
    )
    ice = fields.Selection(
        [
            ("no_ice", "Không đá"),
            ("less_ice", "Ít đá"),
            ("normal", "Vừa đá"),
            ("more_ice", "Nhiều đá"),
        ],
        string="Độ đá",
        default="normal",
    )
    allergy_note = fields.Char("Ghi chú dị ứng")


# ===============================
#  STOCK PICKING / MOVE (ZED)
# ===============================
class StockPicking(models.Model):
    _inherit = "stock.picking"

    zed_move_type = fields.Selection(
        [
            ("consume", "Tiêu hao nguyên liệu"),
            ("transfer", "Chuyển kho nội bộ"),
            ("return", "Trả hàng khách"),
        ],
        string="Loại dịch chuyển (Zed)",
    )
    zed_pos_order_id = fields.Many2one("pos.order", string="Nguồn POS (Zed)")
    zed_barista_id = fields.Many2one("hr.employee", string="Barista (Zed)")
    zed_shift_note = fields.Char("Ghi chú ca (Zed)")


class StockMove(models.Model):
    _inherit = "stock.move"

    zed_is_consumption = fields.Boolean("Là dòng tiêu hao (Zed)", default=False)
    zed_source_order = fields.Many2one("pos.order", string="Nguồn POS (Zed)")

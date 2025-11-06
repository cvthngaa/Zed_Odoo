# -*- coding: utf-8 -*-
from odoo import models, fields

# =========================
#  ZED RECIPE (CÔNG THỨC)
# =========================
class ZedRecipe(models.Model):
    _name = "zed.recipe"
    _description = "Công thức đồ uống The Zed"

    name = fields.Char("Tên công thức", required=True)
    product_tmpl_id = fields.Many2one(
        "product.template", string="Sản phẩm (đồ uống)", ondelete="cascade", index=True
    )
    line_ids = fields.One2many("zed.recipe.line", "recipe_id", string="Thành phần")


class ZedRecipeLine(models.Model):
    _name = "zed.recipe.line"
    _description = "Thành phần công thức The Zed"

    recipe_id = fields.Many2one("zed.recipe", string="Công thức", ondelete="cascade", required=True)
    material_id = fields.Many2one("product.product", string="Nguyên liệu", required=True)
    qty = fields.Float(
        "Số lượng",
        default=1.0,
        required=True,
        help="Số lượng nguyên liệu cho 1 đơn vị đồ uống. Dùng UoM mặc định của nguyên liệu.",
    )


class ProductTemplate(models.Model):
    _inherit = "product.template"

    zed_recipe_id = fields.Many2one("zed.recipe", string="Công thức chính (ZED)")
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

    # Giữ để khớp với pos_order_views.xml
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

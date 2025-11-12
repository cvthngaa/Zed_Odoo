from odoo import models, fields, tools

SQL_TEMPLATE = """
CREATE VIEW zed_consumption_report AS
SELECT
    MIN(sml.id)                                  AS id,
    COALESCE(sp.date_done, sml.date, sm.date)    AS date,
    COALESCE(sml.product_id, sm.product_id)      AS product_id,
    COALESCE(sml.product_uom_id, sm.product_uom) AS uom_id,
    SUM({qty_col})                               AS qty,
    COALESCE(sml.picking_id, sm.picking_id)      AS picking_id,
    sp.company_id                                AS company_id,
    sp.zed_pos_order_id                          AS pos_order_id,
    sp.zed_barista_id                            AS barista_id
FROM stock_move sm
JOIN stock_picking sp ON sp.id = sm.picking_id
JOIN stock_move_line sml ON sml.move_id = sm.id
WHERE sp.state = 'done'
  AND sm.state = 'done'
  AND sp.zed_move_type = 'consume'
  AND COALESCE({qty_col}, 0) > 0
GROUP BY
    COALESCE(sp.date_done, sml.date, sm.date),
    COALESCE(sml.product_id, sm.product_id),
    COALESCE(sml.product_uom_id, sm.product_uom),
    COALESCE(sml.picking_id, sm.picking_id),
    sp.company_id,
    sp.zed_pos_order_id,
    sp.zed_barista_id
"""

class ZedConsumptionReport(models.Model):
    _name = "zed.consumption.report"
    _description = "Báo cáo tiêu hao nguyên liệu (The Zed)"
    _auto = False
    _order = "date desc, id desc"

    date = fields.Datetime("Ngày")
    product_id = fields.Many2one("product.product", "Nguyên liệu", index=True)
    qty = fields.Float("Số lượng", digits="Product Unit of Measure")
    uom_id = fields.Many2one("uom.uom", "ĐVT")
    picking_id = fields.Many2one("stock.picking", "Phiếu tiêu hao")
    company_id = fields.Many2one("res.company", "Công ty", index=True)
    pos_order_id = fields.Many2one("pos.order", "Đơn POS")
    barista_id = fields.Many2one("hr.employee", "Barista")

    def init(self):
        cr = self.env.cr
        tools.drop_view_if_exists(cr, "zed_consumption_report")

        # Tìm cột số lượng thật sự có trên stock_move_line
        cr.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = current_schema()
              AND table_name = 'stock_move_line'
              AND column_name IN ('qty_done','quantity')
            ORDER BY CASE column_name WHEN 'qty_done' THEN 0 ELSE 1 END
            LIMIT 1
        """)
        row = cr.fetchone()
        # Mặc định ưu tiên qty_done; nếu không có thì dùng quantity
        qty_col_name = row[0] if row else 'qty_done'

        # Quan trọng: định danh đầy đủ với prefix sml.
        qty_col_sql = f"sml.{qty_col_name}"

        sql = SQL_TEMPLATE.format(qty_col=qty_col_sql)
        cr.execute(sql)

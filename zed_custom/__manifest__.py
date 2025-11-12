# -*- coding: utf-8 -*-
{
    "name": "Zed Custom",
    "version": "19.0.1.0.0",
    "summary": "Tùy biến tổng hợp cho Cafe The Zed (POS/Kho/MRP/CRM/HR)",
    "category": "Customization",
    "license": "LGPL-3",
    "author": "The Zed Team",
    "website": "",
    "depends": [
        "base",
        "contacts",       # mở rộng res.partner
        "uom",
        "product",
        "stock",          # kho
        "mrp",            # BoM/phantom
        "point_of_sale",  # POS
        "account",        # kế toán (POS cần)
        "hr",             # nhân viên/barista
        "crm",            # nếu dùng loyalty/khách hàng
    ],
    "post_init_hook": "post_init_assign_variant_xmlids",
    "data": [
        "security/ir.model.access.csv",
        "views/menu_root.xml",
        'views/stock_picking_views.xml',
        'views/hr_employee_views.xml',
        'views/res_partner_views.xml',
        'views/pos_order_views.xml',
        'views/product_template_views.xml',
        'views/product_search_views.xml',
        'views/zed_recipe_views.xml',
        'views/stock_move_views.xml',
        'views/zed_consumption_report_views.xml',
        'views/zed_bom_menu.xml',
        'data/hr.employee.csv',
        'data/res.partner.csv',
        'data/product.attribute.csv',
        'data/product.attribute.value.csv',
        'data/product.template.csv',                    # file của bạn
        'data/product.template.attribute.line.csv',
        # 'data/product.product.csv',
        'data/mrp.bom.csv',                             # file của bạn (đang trỏ template)
        'data/mrp.bom.line.csv',                  # dùng file FIX này thay cho file cũ
  # Khi sẵn sàng chạy theo biến thể:
        # 'data/mrp.bom.per_variant.todo.csv',
        # 'data/mrp.bom.line.per_variant.todo.csv',
        # 'data/pos.config.csv',  
        # 'data/pos.session.csv',
        # 'data/pos.order.csv',
        # 'data/pos.order.line.csv',

    ],
    # "assets": {...},   # CHƯA có JS/CSS thì bỏ hẳn dòng này
    "installable": True,
    "application": True,
    "auto_install": False,
    'license': 'LGPL-3',
}

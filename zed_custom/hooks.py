# -*- coding: utf-8 -*-
import re
import unicodedata
from odoo import api, SUPERUSER_ID
import logging



def _slug(s):
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s


def _attr_key(name):
    n = _slug(name)
    if "ngot" in n:
        return "do_ngot"
    if "tra" in n or "dam" in n:
        return "do_tra"
    if "da" in n:  # đá
        return "da"
    return n or "attr"


def _ensure_attr(env):
    """Tạo/đảm bảo tồn tại 3 thuộc tính + giá trị và đặt create_variant=always."""
    Attr = env['product.attribute']
    Val = env['product.attribute.value']

    def upsert_attr(xmlid, name):
        rec = env.ref(xmlid, raise_if_not_found=False)
        if rec:
            rec.write({'name': name, 'create_variant': 'always'})
            return rec
        rec = Attr.create({'name': name, 'create_variant': 'always'})
        env['ir.model.data'].create({
            'module': 'zed_custom', 'name': xmlid.split('.')[1],
            'model': 'product.attribute', 'res_id': rec.id, 'noupdate': True
        })
        return rec

    def upsert_val(xmlid, name, attr):
        rec = env.ref(xmlid, raise_if_not_found=False)
        if rec:
            rec.write({'name': name, 'attribute_id': attr.id})
            return rec
        rec = Val.create({'name': name, 'attribute_id': attr.id})
        env['ir.model.data'].create({
            'module': 'zed_custom', 'name': xmlid.split('.')[1],
            'model': 'product.attribute.value', 'res_id': rec.id, 'noupdate': True
        })
        return rec

    # Thuộc tính
    a_ngot = upsert_attr('zed_custom.attr_do_ngot', 'Độ ngọt')
    a_tra  = upsert_attr('zed_custom.attr_do_tra',  'Độ đậm trà')
    a_da   = upsert_attr('zed_custom.attr_da',      'Đá')

    # Giá trị
    v_ngot_it     = upsert_val('zed_custom.pav_do_ngot_it',     'Ít ngọt',   a_ngot)
    v_ngot_vua    = upsert_val('zed_custom.pav_do_ngot_vua',    'Vừa ngọt',  a_ngot)
    v_ngot_nhieu  = upsert_val('zed_custom.pav_do_ngot_nhieu',  'Ngọt nhiều', a_ngot)

    v_tra_nhat    = upsert_val('zed_custom.pav_do_tra_nhat',    'Nhạt', a_tra)
    v_tra_vua     = upsert_val('zed_custom.pav_do_tra_vua',     'Vừa',  a_tra)
    v_tra_dam     = upsert_val('zed_custom.pav_do_tra_dam',     'Đậm',  a_tra)

    v_da_khong    = upsert_val('zed_custom.pav_da_khong',       'Không đá', a_da)
    v_da_it       = upsert_val('zed_custom.pav_da_it',          'Ít đá',    a_da)
    v_da_vua      = upsert_val('zed_custom.pav_da_vua',         'Vừa đá',   a_da)
    v_da_nhieu    = upsert_val('zed_custom.pav_da_nhieu',       'Nhiều đá', a_da)

    return {
        'do_ngot': (a_ngot, [v_ngot_it, v_ngot_vua, v_ngot_nhieu]),
        'do_tra':  (a_tra,  [v_tra_nhat, v_tra_vua, v_tra_dam]),
        'da':      (a_da,   [v_da_khong, v_da_it, v_da_vua, v_da_nhieu]),
    }


def _attach_attrs_to_templates(env, attr_bundle):
    """Gán 3 thuộc tính vào toàn bộ template bán hàng (POS/sale) CHƯA có PTAL.
       Điều kiện lọc: sale_ok=True hoặc available_in_pos=True.
    """
    Tmpl = env['product.template']
    PTAL = env['product.template.attribute.line']

    tmpl_domain = ['|', ('sale_ok', '=', True), ('available_in_pos', '=', True)]
    templates = Tmpl.search(tmpl_domain)

    # Map attribute -> existing PTAL per template
    for tmpl in templates:
        existing_attrs = set(tmpl.attribute_line_ids.mapped('attribute_id.id'))
        to_create = []
        for key in ('do_ngot', 'do_tra', 'da'):
            attr, values = attr_bundle[key]
            if attr.id in existing_attrs:
                continue
            to_create.append({
                'product_tmpl_id': tmpl.id,
                'attribute_id': attr.id,
                'value_ids': [(6, 0, [v.id for v in values])],  # gán ALL values => sinh đủ biến thể
            })
        if to_create:
            PTAL.create(to_create)

    # Sau khi PTAL tạo xong, Odoo sẽ sinh product.product cho các tổ hợp


def _assign_xmlid_to_variants(env):
    """Gán XMLID cho toàn bộ product.product chưa có xmlid (module zed_custom),
       theo quy ước pp_<base>__<do_ngot_*__do_tra_*__da_*>
    """
    Ir = env['ir.model.data']
    Product = env['product.product']
    Template = env['product.template']

    # Token base cho từng template
    t2base = {}
    for tmpl in Template.search([]):
        base = tmpl.default_code or getattr(tmpl, 'code', None) or tmpl.barcode or tmpl.name
        base_token = _slug(base) or ("tmpl_%s" % tmpl.id)
        t2base[tmpl.id] = base_token

    def build_name(prod):
        base = t2base.get(prod.product_tmpl_id.id) or "product_%s" % prod.id
        parts = []
        for ptav in prod.product_template_attribute_value_ids:
            attr = ptav.attribute_id.name or ""
            val  = getattr(ptav, "name", None) or getattr(getattr(ptav, "product_attribute_value_id", None), "name", "") or ""
            key = _attr_key(attr)
            parts.append(f"{key}_{_slug(val)}")
        if parts:
            return "pp_%s__%s" % (base, "__".join(sorted(parts)))
        return "pp_%s" % base

    def ensure_unique(module, name):
        cand = name
        i = 2
        while True:
            try:
                env.ref(f"{module}.{cand}")
                cand = f"{name}_{i}"
                i += 1
            except ValueError:
                return cand

    # Gán xmlid cho toàn bộ biến thể CHƯA có xmlid
    for prod in Product.search([]):
        # nếu đã có bất kỳ xmlid nào → bỏ qua
        if Ir.search_count([('model', '=', 'product.product'), ('res_id', '=', prod.id)]):
            continue
        name = ensure_unique('zed_custom', build_name(prod))
        Ir.create({
            'module': 'zed_custom',
            'name': name,
            'model': 'product.product',
            'res_id': prod.id,
            'noupdate': True,
        })


def post_init_assign_variant_xmlids(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # B1: map pt_* -> pp_* cho biến thể mặc định (đoạn của bạn giữ nguyên)
    imd_tmpls = env['ir.model.data'].sudo().search([
        ('model', '=', 'product.template'),
        ('module', '=', 'zed_custom'),
    ])
    for imd in imd_tmpls:
        tmpl = env['product.template'].browse(imd.res_id)
        if not tmpl.exists() or not tmpl.product_variant_id:
            continue
        if imd.name.startswith('pt_'):
            pp_name = imd.name.replace('pt_', 'pp_', 1)
        else:
            pp_name = f"pp_{imd.name}"
        exists = env['ir.model.data'].sudo().search([
            ('model','=','product.product'),
            ('module','=','zed_custom'),
            ('name','=',pp_name),
        ], limit=1)
        if not exists:
            env['ir.model.data'].sudo().create({
                'module': 'zed_custom',
                'name': pp_name,
                'model': 'product.product',
                'res_id': tmpl.product_variant_id.id,
                'noupdate': True,
            })
    existing = {x.res_id for x in imd.search([('model','=','product.product')])}
    products = env['product.product'].sudo().search([])
    for p in products:
        if p.id not in existing:
            imd.create({
                'module': 'zed_custom',
                'name': f'pp_auto_{p.id}',
                'model': 'product.product',
                'res_id': p.id,
                'noupdate': True,
            })
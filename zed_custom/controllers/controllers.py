# from odoo import http


# class ZedCustom(http.Controller):
#     @http.route('/zed_custom/zed_custom', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/zed_custom/zed_custom/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('zed_custom.listing', {
#             'root': '/zed_custom/zed_custom',
#             'objects': http.request.env['zed_custom.zed_custom'].search([]),
#         })

#     @http.route('/zed_custom/zed_custom/objects/<model("zed_custom.zed_custom"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('zed_custom.object', {
#             'object': obj
#         })


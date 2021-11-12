from django.utils.translation import gettext_lazy as _
from django.template.loader import select_template, get_template
from django.template import TemplateDoesNotExist
from shop.conf import app_settings

from cmsplus.plugin_base import PlusPluginBase


class OrderPluginBase(PlusPluginBase):
    render_type = 'not-set'

    def get_render_template(self, context, instance, placeholder):
        render_template = getattr(self, 'render_template', None)
        if render_template:
            return get_template(render_template)
        try:
            t = select_template([
                '{}/order/{}.html'.format(app_settings.APP_LABEL, self.render_type),
                'shop/order/{}.html'.format(self.render_type),
            ])
        except TemplateDoesNotExist:
            t = get_template('shop/order/list.html')
        return t


class OrderListPlugin(OrderPluginBase):
    footnote_html = """
    Shows a customer order listing.
    """
    name = 'Order List'
    module = 'shop'
    allow_children = False
    cache = False
    render_type = 'list'


class OrderDetailPlugin(OrderPluginBase):
    footnote_html = """
    Shows customer order details.
    """
    name = 'Order Detail'
    module = 'shop'
    allow_children = False
    cache = False
    render_type = 'detail'

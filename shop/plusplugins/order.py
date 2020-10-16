from django.utils.translation import gettext_lazy as _

from cmsplus.plugin_base import PlusPluginBase


class OrderListPlugin(PlusPluginBase):
    name = _('Order List')
    module = 'shop'
    render_template = 'shop/order/list.html'
    allow_children = False
    cache = False


class OrderDetailPlugin(PlusPluginBase):
    name = _('Order Detail')
    module = 'shop'
    render_template = 'shop/order/detail.html'
    allow_children = False
    cache = False

from django.forms import fields, widgets
from django.template import TemplateDoesNotExist
from django.template.loader import select_template, get_template
from django.utils.translation import gettext_lazy as _

from cms.plugin_pool import plugin_pool

from cmsplus.forms import PlusPluginFormBase, get_style_form_fields
from cmsplus.plugin_base import StylePluginMixin, PlusPluginBase

from shop.conf import app_settings
from shop.models.cart import CartModel
from shop.serializers.cart import CartSerializer

import logging
logger = logging.getLogger('shop')


class CheckoutShippingAddressPluginForm(PlusPluginFormBase):
    CHOICES = [
        ('shipping-address-summary', _("Shipping Address Summary")),
    ]

    render_type = fields.ChoiceField(
        choices=CHOICES,
        widget=widgets.RadioSelect,
        label=_("Render as"),
        initial='summary',
        help_text=_("Shall the cart be editable or static or summary?"),
    )

    is_editable = fields.BooleanField(label=_('Is Editable'), initial=True)

    STYLE_CHOICES = 'SHOP_SHIPPING_ADDRESS_STYLES'
    extra_style, extra_classes, label, extra_css = get_style_form_fields(STYLE_CHOICES)


class CheckoutShippingAddressPlugin(StylePluginMixin, PlusPluginBase):
    name = _('Checkout Shipping Address')
    module = _('Shop')
    cache = False
    allow_children = True
    form = CheckoutShippingAddressPluginForm

    def get_render_template(self, context, instance, placeholder):
        render_template = instance.glossary.get('render_template')
        if render_template:
            return get_template(render_template)
        render_type = instance.glossary.get('render_type')
        try:
            return select_template([
                '{}/checkout/{}.html'.format(app_settings.APP_LABEL, render_type),
                'shop/checkout/{}.html'.format(render_type),
            ])
        except TemplateDoesNotExist:
            return get_template('shop/checkout/shipping-address-summary.html')

    def render(self, context, instance, placeholder):
        try:
            cart = CartModel.objects.get_from_request(context['request'])
            context['is_cart_filled'] = cart.items.exists()

            if not cart.shipping_address:
                # try to set shipping address if exist
                cart.shipping_address = context['request'].customer.shippingaddress_set.first()
                cart.save()

            context['address'] = cart.shipping_address

            # update context for static cart with items to be endered as HTML
            cart_serializer = CartSerializer(cart, context=context, label='cart', with_items=True)
            context['cart'] = cart_serializer.data

        except (KeyError, CartModel.DoesNotExist):
            pass
        return super().render(context, instance, placeholder)


plugin_pool.register_plugin(CheckoutShippingAddressPlugin)

from django.forms import fields, widgets
from django.template import TemplateDoesNotExist
from django.template.loader import select_template, get_template
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html

from cmsplus.forms import PlusPluginFormBase
from cmsplus.plugin_base import PlusPlugin
from cmsplus.cms_plugins.bootstrap.icon import IconField

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

    is_editable = fields.BooleanField(label=_('Is Editable'), initial=True, required=False)

    STYLE_CHOICES = 'SHOP_SHIPPING_ADDRESS_STYLES'


class CheckoutShippingAddressPlugin(PlusPlugin):
    footnote_html = """
    Manages the current order-checkout shipping address.
    """
    name = 'Checkout Shipping Address'
    module = 'shop'
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


class CheckoutPaymentPluginForm(PlusPluginFormBase):
    is_editable = fields.BooleanField(label=_('Is Editable'), required=False, initial=False)

    STYLE_CHOICES = 'SHOP_PAYMENT_STYLES'


class CheckoutPaymentPlugin(PlusPlugin):
    footnote_html = """
    Manages the current order-checkout payment.
    """
    name = 'Checkout Payment'
    module = 'shop'
    cache = False
    allow_children = True
    form = CheckoutPaymentPluginForm
    render_template = 'shop/checkout/payment.html'

    def render(self, context, instance, placeholder):
        try:
            cart = CartModel.objects.get_from_request(context['request'])
            context['is_cart_filled'] = cart.items.exists()
            context['address'] = cart.billing_address or cart.shipping_address

            # update context for static cart with items to be endered as HTML
            cart_serializer = CartSerializer(cart, context=context, label='cart', with_items=True)
            context['cart'] = cart_serializer.data

        except (KeyError, CartModel.DoesNotExist):
            pass
        return super().render(context, instance, placeholder)


class CheckoutButtonForm(PlusPluginFormBase):
    button_text = fields.CharField(
        max_length=255, label=_('Button Text'), required=True, initial=_('Purchase Now'),
        help_text=_('Button content, e.g.: Click me, or nothing for icon only button'))

    BUTTON_SIZES = [
        ('btn-lg', _("Large button")),
        ('', _("Default button")),
        ('btn-sm', _("Small button")),
    ]

    button_size = fields.ChoiceField(
        label=_("Button Size"),
        choices=BUTTON_SIZES,
        initial='',
        required=False,
        help_text=_("Button Size to use.")
    )

    button_block = fields.ChoiceField(
        label=_("Button Block"),
        choices=[
            ('', _('No')),
            ('btn-block', _('Block level button')),
        ],
        required=False,
        initial='',
        help_text=_("Use button block option (span left to right)?")
    )

class CheckoutButtonPluginBase(PlusPlugin):
    module = 'shop'
    form = CheckoutButtonForm
    allow_children = False

    class Media:
        js = ['cmsplus/admin/icon_plugin/js/icon_plugin.js']

    def render(self, context, instance, placeholder):
        instance.add_classes('btn')
        try:
            context['cart'] = CartModel.objects.get_from_request(context['request'])
        except Exception:
            context['cart'] = {'is_empty': True}
        return super().render(context, instance, placeholder)


class CheckoutButtonPlugin(CheckoutButtonPluginBase):
    footnote_html = """
    Shows the carts order checkout button.
    """
    name = 'Checkout Button'
    render_template = 'shop/checkout/checkout_button.html'


class PurchaseButtonPlugin(CheckoutButtonPluginBase):
    footnote_html = """
    Shows the checkouts purchase button.
    """
    name = 'Purchase Button'
    render_template = 'shop/checkout/purchase_button.html'

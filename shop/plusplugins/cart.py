from django.forms import fields, widgets
from django.template import TemplateDoesNotExist
from django.template.loader import select_template, get_template
from django.utils.translation import gettext_lazy as _
from django.utils.html import mark_safe

from cms.plugin_pool import plugin_pool

from cmsplus.forms import PlusPluginFormBase, get_style_form_fields
from cmsplus.plugin_base import StylePluginMixin, PlusPluginBase

from shop.conf import app_settings
from shop.models.cart import CartModel
from shop.serializers.cart import CartSerializer


class ShopCartPluginForm(PlusPluginFormBase):
    CHOICES = [
        ('editable', _("Editable Cart")),
        # ('static', _("Static Cart")),
        # ('summary', _("Cart Summary")),
        #  ('watch', _("Watch List")),
    ]

    render_type = fields.ChoiceField(
        choices=CHOICES,
        widget=widgets.RadioSelect,
        label=_("Render as"),
        initial='editable',
        help_text=_("Shall the cart be editable or a static summary?"),
    )

    STYLE_CHOICES = 'SHOP_CART_STYLES'
    extra_style, extra_classes, label, extra_css = get_style_form_fields(STYLE_CHOICES)


class ShopCartPlugin(StylePluginMixin, PlusPluginBase):
    name = _('Shopping Cart')
    module = _('Shop')
    cache = False
    allow_children = True
    form = ShopCartPluginForm

    @classmethod
    def get_identifier(cls, instance):
        render_type = instance.glossary.get('render_type')
        return mark_safe(dict(cls.form.CHOICES).get(render_type, ''))

    def get_render_template(self, context, instance, placeholder):
        render_template = instance.glossary.get('render_template')
        if render_template:
            return get_template(render_template)
        render_type = instance.glossary.get('render_type')
        try:
            return select_template([
                '{}/cart/{}.html'.format(app_settings.APP_LABEL, render_type),
                'shop/cart/{}.html'.format(render_type),
            ])
        except TemplateDoesNotExist:
            return get_template('shop/cart/editable.html')

    def render(self, context, instance, placeholder):
        try:
            cart = CartModel.objects.get_from_request(context['request'])
            context['is_cart_filled'] = cart.items.exists()
            render_type = instance.glossary['render_type']
            if render_type == 'static':
                # update context for static cart with items to be endered as HTML
                cart_serializer = CartSerializer(cart, context=context, label='cart', with_items=True)
                context['cart'] = cart_serializer.data
            elif render_type == 'summary':
                # update context for cart summary to be endered as HTML
                cart_serializer = CartSerializer(cart, context=context, label='cart')
                context['cart'] = cart_serializer.data
        except (KeyError, CartModel.DoesNotExist):
            pass
        return super().render(context, instance, placeholder)


plugin_pool.register_plugin(ShopCartPlugin)

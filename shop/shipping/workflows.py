from django.conf import settings
from django.db.models import Sum
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import get_language, gettext_lazy as _
from django_fsm import transition
from shop.models.delivery import DeliveryModel, DeliveryItemModel

from post_office import mail
from post_office.models import EmailTemplate

_default_order_confirmation_html_content = """
{% extends "shop/email/base.html" %}

{% block email-head %}
  {% include "shop/email/customer-information.html" %}
{% endblock %}

{% block email-body %}
  {% include "shop/email/order-detail.html" %}
{% endblock %}

{% block email-foot %}
{% endblock %}
"""


class SimpleShippingWorkflowMixin:
    """
    Workflow for simply marking the state of an Order while picking, packing and shipping items.
    It does not create a Delivery object.

    Add this class to ``settings.SHOP_ORDER_WORKFLOWS`` to mix it into the merchants Order model.
    It is mutual exclusive with :class:`shop.shipping.workflows.CommissionGoodsWorkflowMixin` or
    :class:`shop.shipping.workflows.PartialDeliveryWorkflowMixin`.

    It adds all the methods required for state transitions, while picking and packing
    the ordered goods for shipping.
    """
    TRANSITION_TARGETS = {
        'goods_picked': _("Goods picked"),
        'goods_packed': _("Goods packed"),
        'shipping_prepared': _("Shipping prepared"),
        'order_shipped': _("Shipped"),
        'order_completed': _("Completed"),
    }

    CANCELABLE_SOURCES = [
        'new', 'created', 'no_payment_required', 'payment_confirmed', 'needs_verification', 'payment_declined',
        'goods_packed',
    ]

    VERIFICATION_SOURCES = [
        'created', 'no_payment_required', 'payment_confirmed', 'payment_declined', 'goods_picked',
        'goods_packed', 'shipping_prepared', 'order_shipped', 'order_completed'
    ]

    def send_order_confirmation(self, recipients=[], **kwargs):
        """
        :kwargs: can be: sender, cc, bcc, language, context
        sends order confirmation (template `order-confirmation`) to given recipients.
        """
        recipients = recipients or [self.customer.email, ]
        language = kwargs.get('language', get_language())

        template, created = EmailTemplate.objects.get_or_create(
            name='order-confirmation',
            language=language,
            defaults={
                'description': _('send if a customer purchases an order via checkout.'),
                'subject': _('Order Confirmation {{ order.number }}'),
                'html_content': _default_order_confirmation_html_content,
            }
        )

        mail.send(
            recipients,
            sender=kwargs.get('sender',  settings.DEFAULT_FROM_EMAIL),
            cc=kwargs.get('cc'),
            bcc=kwargs.get('bcc'),
            template=template,
            language=kwargs.get('language', get_language()),
            context=kwargs.get('context', {
                'customer': self.customer,
                'order': self,
            })
        )

    @property
    def associate_with_delivery(self):
        """
        :returns: ``True`` if this Order requires a delivery object.
        """
        return False

    @property
    def allow_partial_delivery(self):
        """
        :returns: ``True`` if partial item delivery is allowed.
        """
        return False

    @transition(
        field='status', source=['no_payment_required', 'payment_confirmed', 'needs_verification'],
        target='goods_picked', custom=dict(admin=True, button_name=_("Pick the goods")))
    def goods_picked(self, by=None):
        """Change status to 'goods_picked'."""

    @transition(field='status', source=['goods_picked', 'needs_verification'], target='goods_packed',
                custom=dict(admin=True, button_name=_("Pack the goods")))
    def pack_goods(self, by=None):
        """Change status to 'goods_packed'."""

    @transition(field='status', source=['goods_packed', 'needs_verification'], target='shipping_prepared',
                custom=dict(admin=True, button_name=_("Prepare shipping")))
    def prepare_shipping(self, by=None):
        """
        Prepare the parcel for shipping. This method implicitly invokes
        :method:`shop.shipping.modifiers.ShippingModifier.ship_the_goods(delivery)`
        """

    @transition(field='status', source='shipping_prepared', target='order_shipped',
                custom=dict(auto=True))
    def ship_order(self, by=None):
        """Order was picked up by shipping service provider (method auto invoked)."""

    def update_or_create_delivery(self, orderitem_data):
        """
        Hook to create a delivery object with items.
        """

    @transition(field='status', source=['order_shipped', 'needs_verification'], target='order_completed',
                custom=dict(admin=True, button_name=_("Order completed")))
    def complete_order(self, by=None):
        """
        Order was delivered.
        """


class CommissionGoodsWorkflowMixin(SimpleShippingWorkflowMixin):
    """
    Workflow to commission all ordered items in one common Delivery.

    Add this class to ``settings.SHOP_ORDER_WORKFLOWS`` to mix it into the merchants Order model.
    It is mutual exclusive with :class:`shop.shipping.workflows.SimpleShippingWorkflowMixin` or
    :class:`shop.shipping.workflows.PartialDeliveryWorkflowMixin`.

    It adds all the methods required for state transitions, while picking and packing
    the ordered goods for shipping.
    """
    @property
    def associate_with_delivery(self):
        return True

    @transition(field='status', source='shipping_prepared', target='order_shipped',
                custom=dict(auto=True))
    def ship_order(self, by=None):
        """Order was picked up by shipping service provider (method auto invoked)."""

    def update_or_create_delivery(self, orderitem_data):
        """
        Update or create a Delivery object for all items of this Order object.
        """
        delivery, _ = DeliveryModel.objects.get_or_create(
            order=self,
            shipping_id__isnull=True,
            shipped_at__isnull=True,
            shipping_method=self.extra.get('shipping_modifier'),
            defaults={'fulfilled_at': timezone.now()}
        )
        for item in self.items.all():
            DeliveryItemModel.objects.create(
                delivery=delivery,
                item=item,
                quantity=item.quantity,
            )


class PartialDeliveryWorkflowMixin(CommissionGoodsWorkflowMixin):
    """
    Workflow to optionally commission ordered items partially.

    Add this class to ``settings.SHOP_ORDER_WORKFLOWS`` to mix it into the merchants Order model.
    It is mutual exclusive with :class:`shop.shipping.workflows.SimpleShippingWorkflowMixin` or
    :class:`shop.shipping.workflows.CommissionGoodsWorkflowMixin`.

    This mixin supports partial delivery, hence check that a materialized representation of the
    models :class:`shop.models.delivery.DeliveryModel` and :class:`shop.models.delivery.DeliveryItemModel`
    exists and is instantiated.

    Importing the classes :class:`shop.models.defaults.delivery.DeliveryModel` and
    :class:`shop.models.defaults.delivery_item.DeliveryItemModel` into the merchants
    ``models.py``, usually is enough. This adds all the methods required for state transitions,
    while picking, packing and shipping the ordered goods for delivery.
    """
    @property
    def allow_partial_delivery(self):
        return True

    @cached_property
    def unfulfilled_items(self):
        unfulfilled_items = 0
        for order_item in self.items.all():
            if not order_item.canceled:
                aggr = order_item.deliver_item.aggregate(delivered=Sum('quantity'))
                unfulfilled_items += order_item.quantity - (aggr['delivered'] or 0)
        return unfulfilled_items

    def ready_for_picking(self):
        return self.is_fully_paid() and self.unfulfilled_items > 0

    def ready_for_shipping(self):
        return self.delivery_set.filter(shipped_at__isnull=True).exists()

    @transition(field='status', source='*', target='goods_picked', conditions=[ready_for_picking],
                custom=dict(admin=True, button_name=_("Pick the goods")))
    def pick_goods(self, by=None):
        """Change status to 'goods_picked'."""

    @transition(field='status', source=['goods_picked'], target='goods_packed',
                custom=dict(admin=True, button_name=_("Pack the goods")))
    def pack_goods(self, by=None):
        """Prepare shipping object and change status to 'goods_packed'."""

    @transition(field='status', source='*', target='shipping_prepared', conditions=[ready_for_shipping],
                custom=dict(admin=True, button_name=_("Prepare Shipping")))
    def prepare_shipping(self, by=None):
        """Prepare the parcel for shipping."""

    @transition(field='status', source='shipping_prepared', target='order_shipped',
                custom=dict(auto=True))
    def ship_order(self, by=None):
        """Order was picked up by shipping service provider (method auto invoked)."""

    def update_or_create_delivery(self, orderitem_data):
        """
        Update or create a Delivery object and associate with selected ordered items.
        """
        delivery, _ = DeliveryModel.objects.get_or_create(
            order=self,
            shipping_id__isnull=True,
            shipped_at__isnull=True,
            shipping_method=self.extra.get('shipping_modifier'),
            defaults={'fulfilled_at': timezone.now()}
        )

        # create a DeliveryItem object for each ordered item to be shipped with this delivery
        for data in orderitem_data:
            if data['deliver_quantity'] > 0 and not data['canceled']:
                DeliveryItemModel.objects.create(
                    delivery=delivery,
                    item=data['id'],
                    quantity=data['deliver_quantity'],
                )
        if not delivery.items.exists():
            # since no OrderItem was added to this delivery, discard it
            delivery.delete()

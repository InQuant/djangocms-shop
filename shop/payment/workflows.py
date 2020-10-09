from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _
from django_fsm import transition, RETURN_VALUE

from shop.models.order import BaseOrder


class ManualPaymentWorkflowMixin:
    """
    Add this class to `settings.SHOP_ORDER_WORKFLOWS` to mix it into your `OrderModel`.
    It adds all the methods required for state transitions, when used with the
    `ForwardFundPayment` provider from above.
    """
    TRANSITION_TARGETS = {
        'awaiting_payment': _("Awaiting a forward fund payment"),
        'prepayment_deposited': _("Prepayment deposited"),
        'no_payment_required': _("No Payment Required"),
    }
    _manual_payment_transitions = TRANSITION_TARGETS.keys()

    def __init__(self, *args, **kwargs):
        if not isinstance(self, BaseOrder):
            raise ImproperlyConfigured("class 'ManualPaymentWorkflowMixin' is not of type 'BaseOrder'")
        CancelOrderWorkflowMixin.CANCELABLE_SOURCES.update(self._manual_payment_transitions)
        super().__init__(*args, **kwargs)

    @transition(field='status', source=['created'], target='no_payment_required')
    def no_payment_required(self):
        """
        Signals that an Order can proceed directly, by confirming a payment of value zero.
        """

    @transition(field='status', source=['created'], target='awaiting_payment')
    def awaiting_payment(self):
        """
        Signals that the current Order awaits a payment.
        Invoked by ForwardFundPayment.get_payment_request.
        """

    def payment_deposited(self):
        return self.amount_paid > 0

    @transition(field='status', source=['awaiting_payment'],
                target=RETURN_VALUE('awaiting_payment', 'prepayment_deposited'),
                conditions=[payment_deposited],
                custom=dict(admin=True, button_name=_("Payment Received")))
    def prepayment_deposited(self):
        """
        Signals that the current Order received a payment.
        """
        return 'prepayment_deposited' if self.is_fully_paid() else 'awaiting_payment'

    @transition(field='status', source=['prepayment_deposited', 'no_payment_required'],
                custom=dict(auto=True))
    def acknowledge_prepayment(self):
        """
        Acknowledge the payment. This method is invoked automatically.
        """
        self.acknowledge_payment()

    @transition(field='status', source='refund_payment', target=RETURN_VALUE('refund_payment', 'order_canceled'),
                custom=dict(admin=True, button_name=_("Mark as Refunded")))
    def payment_refunded(self):
        """
        Signals that the payment for this Order has been refunded manually.
        """
        return 'refund_payment' if self.amount_paid else 'order_canceled'


class InvoicePaymentWorkflowMixin:
    """
    Add this class to `settings.SHOP_ORDER_WORKFLOWS` to mix it into your `OrderModel`.
    It adds all the methods required for state transitions, when used with the
    `InvoicePaymentProvider` provider from above.
    """
    TRANSITION_TARGETS = {
        'no_payment_required': _("No Payment Required"),
    }
    _invoice_payment_transitions = TRANSITION_TARGETS.keys()

    def __init__(self, *args, **kwargs):
        if not isinstance(self, BaseOrder):
            raise ImproperlyConfigured("class 'InvoicePaymentWorkflowMixin' is not of type 'BaseOrder'")
        CancelOrderWorkflowMixin.CANCELABLE_SOURCES.update(self._invoice_payment_transitions)
        super().__init__(*args, **kwargs)

    @transition(field='status', source=['created'], target='no_payment_required')
    def no_payment_required(self):
        """
        Signals that an Order can proceed directly, by confirming a payment of value zero.
        """


class CancelOrderWorkflowMixin:
    """
    Add this class to `settings.SHOP_ORDER_WORKFLOWS` to mix it into your `OrderModel`.
    It adds all the methods required for state transitions, to cancel an order.
    """
    CANCELABLE_SOURCES = {
        'new', 'created', 'no_payment_required', 'payment_confirmed', 'payment_declined', 'order_shipped',
    }
    TRANSITION_TARGETS = {
        'refund_payment': _("Refund payment"), 'order_canceled': _("Order Canceled"),
    }

    def can_be_canceled(self):
        return self.status in self.CANCELABLE_SOURCES

    def has_been_canceled(self):
        return self.status == 'order_canceled'

    @transition(field='status', target=RETURN_VALUE(*TRANSITION_TARGETS.keys()),
                conditions=[can_be_canceled], custom=dict(admin=True, button_name=_("Cancel Order")))
    def cancel_order(self):
        """
        Signals that an Order shall be canceled.
        """
        self.withdraw_from_delivery()
        if self.amount_paid:
            self.refund_payment()
        return 'refund_payment' if self.amount_paid else 'order_canceled'


class VerifyOrderWorkflowMixin:
    """
    Add this class to `settings.SHOP_ORDER_WORKFLOWS` to mix it into your `OrderModel`.
    It adds all the methods required for state transitions, to verify an order.
    """
    VERIFICATION_SOURCES = [
        'created', 'no_payment_required', 'payment_confirmed', 'payment_declined', 'order_shipped',
    ]
    TRANSITION_TARGETS = {
        'needs_verification': _("Needs Verification"),
    }

    def needs_verification(self):
        return self.status == 'needs_verification'

    @transition(field='status', source=VERIFICATION_SOURCES, target='needs_verification',
                custom=dict(admin=True, button_name=_("Needs verification")))
    def verify_order(self, by=None):
        """
        Signals that an Order needs verification.
        """

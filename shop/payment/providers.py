from shop.models.order import OrderModel


class PaymentProvider:
    """
    Base class for all Payment Service Providers.
    """
    @property
    def namespace(self):
        """
        Use a unique namespace for this payment provider. It is used to build the communication URLs
        exposed to an external payment service provider.
        """
        msg = "The attribute `namespace` must be implemented by the class `{}`"
        raise NotImplementedError(msg.format(self.__class__.__name__))

    def get_urls(self):
        """
        Return a list of URL patterns for external communication with the payment service provider.
        """
        return []

    def get_payment_request(self, cart, request):
        """
        Build a JavaScript expression which is evaluated by the success handler on the page
        submitting the purchase command. When redirecting to another page, use:
        ```
        window.location.href="URL-of-other-page";
        ```
        since this expression is evaluated inside an AngularJS directive.
        """
        return ('alert("Please implement method `get_payment_request` in the Python class inheriting from '
                '`PaymentProvider`!");')


class ForwardFundPayment(PaymentProvider):
    """
    Provides a simple prepayment payment provider.
    """
    namespace = 'forward-fund-payment'

    def get_payment_request(self, cart, request):
        order = OrderModel.objects.create_from_cart(cart, request)
        order.populate_from_cart(cart, request)
        if order.total == 0:
            order.no_payment_required()  # must be declared in Workflow
        else:
            order.awaiting_payment()  # must be declared in Workflow
        order.save(with_notification=True)
        return 'window.location.href="{}";'.format(order.get_absolute_url())


class InvoicePaymentProvider(PaymentProvider):
    """
    Provides a simple pay per invoice payment provider.
    """
    namespace = 'invoice-payment'

    def get_payment_request(self, cart, request):
        order = OrderModel.objects.create_from_cart(cart, request)
        order.populate_from_cart(cart, request)
        order.no_payment_required()  # must be declared in Workflow
        order.save(with_notification=True)
        return 'window.location.href="{}";'.format(order.get_absolute_url())

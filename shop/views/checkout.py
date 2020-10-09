from rest_framework.viewsets import GenericViewSet

from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from shop import messages
from shop.exceptions import ProductNotAvailable
from shop.models.cart import CartModel
from shop.modifiers.pool import cart_modifiers_pool

import logging
logger = logging.getLogger('shop')


class CheckoutViewSet(GenericViewSet):
    """
    REST endpoint for checkout and purchase methods
    """

    @action(methods=['post'], detail=False, url_path='purchase')
    def purchase(self, request):
        """
        This is the final step on converting a cart into an order object.
        """
        cart = CartModel.objects.get_from_request(request)
        try:
            cart.update(request, raise_exception=True)
        except ProductNotAvailable as exc:
            message = _(
                "The product '{product_name}' ({product_code}) suddenly became unavailable, "
                "presumably because someone else has been faster purchasing it.\n Please "
                "recheck the cart or add an alternative product and proceed with the checkout.").format(
                    product_name=exc.product.product_name, product_code=exc.product.product_code)
            messages.error(request, message, title=_("Product Disappeared"), delay=10)
            message = _(
                "The product '{product_name}' ({product_code}) suddenly became unavailable.").format(
                    product_name=exc.product.product_name, product_code=exc.product.product_code)
            response_data = {'purchasing_error_message': message}
            return Response(data=response_data, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        cart.save()

        response_data = {}
        try:
            # Iterate over the registered modifiers, and search for the active payment service provider
            for modifier in cart_modifiers_pool.get_payment_modifiers():
                if modifier.is_active(cart.extra.get('payment_modifier')):
                    try:
                        expression = modifier.payment_provider.get_payment_request(cart, request)
                    except Exception as e:
                        logger.exception(str(e))
                        raise

                    response_data.update(expression=expression)
                    break
        except ValidationError as err:
            message = _("Please select a valid payment method.")
            messages.warning(request, message, title=_("Choose Payment Method"), delay=5)
            response_data = {'purchasing_error_message': '. '.join(err.detail)}
            return Response(data=response_data, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        return Response(data=response_data)

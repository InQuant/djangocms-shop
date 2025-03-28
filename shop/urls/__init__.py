from django.urls import include, re_path
from shop.urls import rest_api
# from shop.urls import auth
# from shop.urls import payment


app_name = 'shop'

urlpatterns = [
    re_path(r'^api/', include(rest_api)),
    # url(r'^auth/', include(auth)),
    # url(r'^payment/', include(payment)),
]

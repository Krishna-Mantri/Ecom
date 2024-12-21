from django.urls import path
from .views import order_confirmation,create_order

app_name='orders'

urlpatterns=[
    path("create",create_order,name="create_order"),
    path("confirmation/<int:order_id>",order_confirmation,name="order_confirmation"),
]
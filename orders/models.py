from django.db import models
from products.models import Product
# Create your models here.


class Order(models.Model):
    full_name=models.CharField(max_length=250)
    email=models.EmailField()
    address=models.CharField(max_length=250)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now_add=True)
    paid=models.BooleanField(default=False)

    razorpay_order_id=models.CharField(max_length=100,blank=True, null=True)
    payment_status=models.CharField(max_length=20,default="Pending")
    
    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())
    
    def get_total_cost_paisa(self):
        return int(self.get_total_cost()*100)
    
    def __str__(self):
        return f"order {self.id}-{self.full_name}"


class OrderItem(models.Model):
    order=models.ForeignKey(Order,related_name="items",on_delete=models.CASCADE)
    product=models.ForeignKey(Product,related_name="order_items",on_delete=models.CASCADE)
    price=models.DecimalField(max_digits=10, decimal_places=2)
    quantity=models.PositiveIntegerField(default=1)


    def get_cost(self):
        return self.price * self.quantity
    
    def __str__(self):
        return f"{self.quantity} X {self.product.name} in order {self.order.id}"
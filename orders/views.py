from django.shortcuts import render,redirect,get_object_or_404
import razorpay.errors
from cart.models import Cart,CartItem
from .models import OrderItem
from .forms import OrderCreateForm,Order
from django.conf import settings
from django.http import JsonResponse
import razorpay
from decimal import Decimal,InvalidOperation
# Create your views here.

razorpay_client=razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
def create_order(request):
    cart=None
    cart_id=request.session.get('cart_id')

    if cart_id:
        cart=Cart.objects.get(id=cart_id)

        if not cart or not cart.items.exists():
            return redirect("cart:cart_detail")

    if request.method=="POST":
        form=OrderCreateForm(request.POST)
        if form.is_valid():
            order=form.save(commit=False)
            order.save()

            for item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    price=item.product.price,
                    quantity=item.quantity
                )

            total_amount=sum(Decimal(item.product.price) * item.quantity for item in cart.items.all())
            total_amount_in_paise=int(total_amount * 100)

            try:

                razorpay_order=razorpay_client.order.create({
                    "amount":total_amount_in_paise,
                    "currency":"INR",
                    "payment_capture":1
                })

                order.razorpay_order_id=razorpay_order['id']
                order.save()

                cart.delete()
                del request.session["cart_id"]
                return redirect("orders:order_confirmation",order.id)
            
            except razorpay.errors.RequestError as e:
                # Handle API request errors
                return render(request, "orders/create.html", {
                    "cart": cart,
                    "form": form,
                    "error": f"Razorpay request error: {e}",
                })
            except razorpay.errors.AuthenticationError as e:
                # Handle authentication errors
                return render(request, "orders/create.html", {
                    "cart": cart,
                    "form": form,
                    "error": f"Razorpay authentication error: {e}",
                })
            except Exception as e:
                # Handle any other generic exceptions
                return render(request, "orders/create.html", {
                    "cart": cart,
                    "form": form,
                    "error": f"Error: {str(e)}",
                })
        

    else:
        form=OrderCreateForm()

    return render(request,"orders/create.html",{
        "cart":cart,"form":form
    })

def order_confirmation(request,order_id):
    order=get_object_or_404(Order,id=order_id)

    if request.method=="POST":
        data=request.POST
        try:
            razorpay_client.utility.verify_payment_signature({
                'razorpay_order_id':data['razorpay_order_id'],
                'razorpay_payment_id':data['razorpay_payment_id'],
                'razorpay_signature':data['razorpay_signature'],
                
            })
            order.payment_status="Paid"
            order.save()

            return JsonResponse({"status":"Payment successfull"})
        
        except razorpay.errors.SignatureVerificationError:
            return JsonResponse({"status":"Payment verification failed!"}, status=400)

    return render(request,"orders/confirm.html",{
        "order":order,"razorpay_key_id":settings.RAZORPAY_KEY_ID
        })
import json
from django.shortcuts import render, redirect, get_object_or_404
import razorpay.errors
from cart.models import Cart, CartItem
from .models import OrderItem
from .forms import OrderCreateForm, Order
from django.conf import settings
from django.http import JsonResponse
import razorpay
from decimal import Decimal
from django.views.decorators.csrf import csrf_exempt

# Razorpay client initialization
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

# Order creation view
def create_order(request):
    cart = None
    cart_id = request.session.get('cart_id')

    if cart_id:
        cart = Cart.objects.filter(id=cart_id).first()

        if not cart or not cart.items.exists():
            return redirect("cart:cart_detail")

    if request.method == "POST":
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.save()

            for item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    price=item.product.price,
                    quantity=item.quantity
                )

            total_amount = sum(Decimal(item.product.price) * item.quantity for item in cart.items.all())
            total_amount_in_paise = int(total_amount * 100)

            try:
                # Create Razorpay order
                razorpay_order = razorpay_client.order.create({
                    "amount": total_amount_in_paise,
                    "currency": "INR",
                    "payment_capture": 1
                })

                # Save Razorpay order ID in the database
                order.razorpay_order_id = razorpay_order['id']
                order.save()

                # Clear the cart after creating the order
                cart.delete()
                del request.session["cart_id"]

                return redirect("orders:order_confirmation", order.id)

            except razorpay.errors.RazorpayError as e:
                # General Razorpay errors
                return render(request, "orders/create.html", {
                    "cart": cart,
                    "form": form,
                    "error": f"Razorpay error: {str(e)}",
                })
            except Exception as e:
                # Handle other unexpected errors
                return render(request, "orders/create.html", {
                    "cart": cart,
                    "form": form,
                    "error": f"Unexpected error: {str(e)}",
                })

    else:
        form = OrderCreateForm()

    return render(request, "orders/create.html", {
        "cart": cart,
        "form": form
    })

# Order confirmation view
@csrf_exempt
def order_confirmation(request, order_id):
    # Fetch the order or return 404 if not found
    order = get_object_or_404(Order, id=order_id)

    if request.method == "POST":
        try:
            # Parse JSON data from the request
            data = json.loads(request.body)

            # Safely retrieve the keys using .get()
            razorpay_order_id = data.get('razorpay_order_id')
            razorpay_payment_id = data.get('razorpay_payment_id')
            razorpay_signature = data.get('razorpay_signature')

            # Validate that all required fields are present
            if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
                return JsonResponse(
                    {"status": "Missing required payment fields"},
                    status=400
                )

            # Verify Razorpay payment signature
            razorpay_client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature,
            })

            # Update the payment status to "Paid"
            order.payment_status = "Paid"
            order.save()

            return JsonResponse({"status": "Payment successful"})

        except razorpay.errors.SignatureVerificationError as e:
            # Handle signature verification errors
            return JsonResponse(
                {"status": "Payment verification failed!", "error": str(e)},
                status=400
            )
        except json.JSONDecodeError:
            # Handle invalid JSON data
            return JsonResponse(
                {"status": "Invalid request data. Please try again."},
                status=400
            )
        except Exception as e:
            # Catch other exceptions
            return JsonResponse(
                {"status": "An unexpected error occurred", "error": str(e)},
                status=500
            )

    # Render the order confirmation page
    return render(request, "orders/confirm.html", {
        "order": order,
        "razorpay_key_id": settings.RAZORPAY_KEY_ID
    })

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.conf import settings
import stripe
from orders.models import Order
from products.models import Product

stripe.api_key = settings.STRIPE_SECRET_KEY

class StripePaymentIntent(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            # Create a payment intent
            amount = int(float(request.data.get('amount', 0)) * 100)  # convert to cents
            currency = request.data.get('currency', 'usd')
            
            if amount <= 0:
                return Response(
                    {'error': 'Amount must be greater than 0'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                metadata={'user_id': request.user.id}
            )
            
            return Response({
                'client_secret': intent.client_secret,
                'amount': amount,
                'currency': currency
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class StoreStats(APIView):
    def get(self, request):
        # Public stats about the store
        product_count = Product.objects.filter(available=True).count()
        category_count = Product.objects.values('category').distinct().count()
        
        return Response({
            'product_count': product_count,
            'category_count': category_count,
            'store_name': 'myproject Platform'
        })

# Stripe webhook
class StripeWebhook(APIView):
    permission_classes = []  # No authentication required for webhooks
    
    def post(self, request):
        payload = request.body
        signature = request.META.get('HTTP_STRIPE_SIGNATURE')
        
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, settings.STRIPE_WEBHOOK_SECRET
            )
            
            # Handle successful payments
            if event['type'] == 'payment_intent.succeeded':
                payment_intent = event['data']['object']
                handle_successful_payment(payment_intent)
                
            return Response({'status': 'success'})
            
        except ValueError as e:
            # Invalid payload
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

def handle_successful_payment(payment_intent):
    # Update order status or perform other actions
    order_id = payment_intent.get('metadata', {}).get('order_id')
    if order_id:
        try:
            order = Order.objects.get(id=order_id)
            # Update order status to processing after payment
            if order.status == 'pending':
                order.status = 'processing'
                order.save()
        except Order.DoesNotExist:
            pass


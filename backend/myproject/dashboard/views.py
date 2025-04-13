from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.db.models import Count, Sum, Avg
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from orders.models import Order
from products.models import Product, Category

class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_staff

class DashboardOverview(APIView):
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        # Get current date and time
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)
        
        # Summary statistics
        total_orders = Order.objects.count()
        recent_orders = Order.objects.filter(created_at__gte=thirty_days_ago).count()
        total_products = Product.objects.count()
        total_customers = User.objects.exclude(is_staff=True).count()
        
        # Sales statistics
        total_sales = Order.objects.filter(status__in=['delivered', 'shipped']).aggregate(total=Sum('total_cost'))['total'] or 0
        recent_sales = Order.objects.filter(
            status__in=['delivered', 'shipped'],
            created_at__gte=thirty_days_ago
        ).aggregate(total=Sum('total_cost'))['total'] or 0
        
        # Order status breakdown
        status_counts = Order.objects.values('status').annotate(count=Count('id'))
        status_breakdown = {item['status']: item['count'] for item in status_counts}
        
        # Category statistics
        category_stats = Category.objects.annotate(
            product_count=Count('products'),
            total_sales=Sum('products__order_items__price')
        ).values('id', 'name', 'product_count', 'total_sales')
        
        # Recent orders
        recent_orders_data = Order.objects.all().order_by('-created_at')[:10]
        recent_orders_list = [
            {
                'id': order.id,
                'customer': f"{order.first_name} {order.last_name}",
                'email': order.email,
                'total': order.total_cost,
                'status': order.status,
                'date': order.created_at
            }
            for order in recent_orders_data
        ]
        
        return Response({
            'summary': {
                'total_orders': total_orders,
                'recent_orders': recent_orders,
                'total_products': total_products,
                'total_customers': total_customers,
                'total_sales': total_sales,
                'recent_sales': recent_sales
            },
            'status_breakdown': status_breakdown,
            'category_stats': list(category_stats),
            'recent_orders': recent_orders_list
        })

class CustomersList(APIView):
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        customers = User.objects.exclude(is_staff=True)
        
        customer_data = []
        for customer in customers:
            orders = Order.objects.filter(user=customer)
            total_spent = orders.aggregate(total=Sum('total_cost'))['total'] or 0
            order_count = orders.count()
            
            customer_data.append({
                'id': customer.id,
                'username': customer.username,
                'name': f"{customer.first_name} {customer.last_name}".strip() or customer.username,
                'email': customer.email,
                'date_joined': customer.date_joined,
                'orders_count': order_count,
                'total_spent': total_spent,
                'last_order': orders.order_by('-created_at').first().created_at if order_count > 0 else None
            })
        
        return Response(customer_data)

class OrdersAnalytics(APIView):
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        # Get date range from query params or default to last 30 days
        days = int(request.query_params.get('days', 30))
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Daily orders and revenue
        orders_by_date = {}
        current_date = start_date
        
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            day_orders = Order.objects.filter(
                created_at__date=current_date.date()
            )
            
            orders_by_date[date_str] = {
                'count': day_orders.count(),
                'revenue': day_orders.aggregate(total=Sum('total_cost'))['total'] or 0
            }
            
            current_date += timedelta(days=1)
        
        # Status distribution
        status_counts = Order.objects.values('status').annotate(count=Count('id'))
        
        # Average order value
        avg_order_value = Order.objects.aggregate(avg=Avg('total_cost'))['avg'] or 0
        
        return Response({
            'daily_data': orders_by_date,
            'status_distribution': list(status_counts),
            'average_order_value': avg_order_value
        })

class ProductAnalytics(APIView):
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        # Top selling products
        top_products = Product.objects.annotate(
            total_sold=Sum('order_items__quantity'),
            revenue=Sum('order_items__price')
        ).filter(total_sold__gt=0).order_by('-total_sold')[:10]
        
        top_products_data = [
            {
                'id': product.id,
                'name': product.name,
                'total_sold': product.total_sold or 0,
                'revenue': product.revenue or 0,
                'price': product.price,
                'category': product.category.name
            }
            for product in top_products
        ]
        
        # Low stock products
        low_stock_threshold = int(request.query_params.get('threshold', 5))
        low_stock = Product.objects.filter(stock__lte=low_stock_threshold, available=True)
        
        low_stock_data = [
            {
                'id': product.id,
                'name': product.name,
                'stock': product.stock,
                'price': product.price,
                'category': product.category.name
            }
            for product in low_stock
        ]
        
        return Response({
            'top_products': top_products_data,
            'low_stock': low_stock_data
        })
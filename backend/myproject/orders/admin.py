# admin.py
from django.contrib import admin
from django import forms
from .models import Order, OrderItem, OrderTracking

class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["price"].disabled = False  # Ensure price is editable
        self.fields["price"].required = False  # Allow price to be empty initially

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Set price based on selected product if not provided
        if instance.product and not instance.price:
            instance.price = instance.product.price
        if commit:
            instance.save()
        return instance

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    form = OrderItemForm
    extra = 1  # Show one empty row by default
    fields = ["product", "price", "quantity"]

class OrderTrackingInline(admin.TabularInline):
    model = OrderTracking
    extra = 1
    fields = ["description", "timestamp","status","location"]
    readonly_fields = ["timestamp"]

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'first_name', 'last_name', 'status', 'total_cost', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['id', 'user__username', 'first_name', 'last_name', 'email']
    readonly_fields = ['total_cost', 'products_cost', 'created_at', 'updated_at']
    inlines = [OrderItemInline, OrderTrackingInline]
    fieldsets = (
        ('Customer Information', {
            'fields': ('user', 'first_name', 'last_name', 'email', 'phone')
        }),
        ('Shipping Information', {
            'fields': ('address', 'city', 'state', 'postal_code', 'country')
        }),
        ('Order Details', {
            'fields': ('status', 'shipping_cost', 'total_cost', 'products_cost', 'notes')
        }),
        ('Date Information', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def save_formset(self, request, form, formset, change):
        formset.save()
        obj = form.instance
        products_cost = sum(item.price * item.quantity for item in obj.items.all())
        shipping_cost = obj.shipping_cost or 0
        obj.total_cost = products_cost + shipping_cost
        obj.save()
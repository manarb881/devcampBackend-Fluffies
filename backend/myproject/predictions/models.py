from django.db import models
from products.models import Product

class StockPrediction(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    week_number = models.IntegerField(default=1)  # Week of the month (1-5)
    month = models.IntegerField(default=1)       # Month number (1-12)
    store_id = models.CharField(max_length=50)
    total_price = models.FloatField()
    base_price = models.FloatField()
    is_featured_sku = models.BooleanField(default=False)
    is_display_sku = models.BooleanField(default=False)
    predicted_stock = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Prediction for {self.product.name} at store {self.store_id} for month {self.month}, week {self.week_number}"
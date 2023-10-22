from django.contrib import admin
from apps.form.models import Producer, WeightScheme, Status, Product, Order, OrderItem

admin.site.register(Producer)
admin.site.register(WeightScheme)
admin.site.register(Status)
admin.site.register(Product)
admin.site.register(Order)
admin.site.register(OrderItem)

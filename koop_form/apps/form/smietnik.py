# def calculate_available_quantity(products):
#     available_quantity = []
#     previous_friday = calculate_previous_friday()
#
#     products_with_ordered_quantities = products.annotate(
#         ordered_quantity=Sum('orderitems__quantity', filter=Q(orderitems__item_ordered_date__gte=previous_friday))).order_by('name')
#
#     for product in products_with_ordered_quantities:
#         product_ordered_quantity = product.ordered_quantity
#         if product_ordered_quantity is None:
#             product_ordered_quantity = 0
#             available_quantity.append(product.order_max_quantity - product_ordered_quantity)
#         else:
#             available_quantity.append(product.order_max_quantity - product_ordered_quantity)
#
#     return available_quantity
#
#
#
#
#
#
#
#
#
#
# @method_decorator(login_required, name='dispatch')
# class OrderItemFormView(OrderExistsTestMixin, SuccessMessageMixin, FormView):
#     model = OrderItem
#     template_name = 'form/orderitem_create.html'
#     form_class = None
#     success_message = "Produkt został dodany do zamówienia."
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.previous_friday = calculate_previous_friday()
#         self.order = None
#         self.producer = None
#         self.products_with_related = None
#         self.products = None
#         self.initial_data = None
#
#     def get_producer_order_and_products(self):
#         self.order = Order.objects.get(user=self.request.user, date_created__gte=self.previous_friday)
#         self.producer = get_object_or_404(Producer, slug=self.kwargs['slug'])
#         self.products_with_related = filter_objects_prefetch_related(Product, *['weight_schemes', 'statuses'], producer=self.producer)
#         self.products = Product.objects.filter(producer=self.producer)
#         self.initial_data = [{'product': product.id} for product in self.products]
#
#     def get_form_class(self):
#         self.get_producer_order_and_products()
#         OrderItemFormSet = modelformset_factory(
#             OrderItem,
#             form=CreateOrderItemForm,
#             formset=CreateOrderItemFormSet,
#             extra=self.products.count()
#         )
#         return OrderItemFormSet
#
#     def test_func(self):
#         return order_exists_test(self.request)
#
#     def get_success_url(self):
#         return self.request.path
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#
#         orderitems = filter_objects_select_related(OrderItem, *['product'], order=self.order.id)
#         context['order'] = self.order
#         context['orderitems'] = orderitems
#         context['order_cost'] = calculate_order_cost(orderitems)
#
#         context['producers'] = Producer.objects.all()
#         context['producer'] = self.producer
#
#         available_quantity = calculate_available_quantity(self.products)
#         products_with_forms = zip(self.products_with_related, context['form'], available_quantity)
#         context['products_with_forms'] = products_with_forms
#         return context
#
#     def get_initial(self):
#         return self.initial_data
#
#     def form_valid(self, form):
#         formset = form.save(commit=False)
#         for instance in formset:
#             if not perform_create_orderitem_validations(instance, self.request):
#                 return self.form_invalid(form)
#             instance.order = self.order
#             instance.save()
#         return super().form_valid(form)
#
#
#
#
#
#
#
#
#
# {% extends "form/base_one.html" %}
# {% load custom_filters %}
# {% block content %}
#
# <div class="col-md-8">
#     <label for="producers">Zmień producenta:</label>
#     <select name="producers" id="producers">
#       {% for producer in producers %}
#           <option value="{% url 'orderitem-create' slug=producer.slug %}">{{ producer.name }}</option>
#       {% endfor %}
#     </select>
#
#     <button onclick="goToSelectedLink()">Idź</button>
#
#     <h3>{{ producer.name }}</h3>
#     <p>{{ producer.description }}</p>
#
#     <form method="post">
#         {% csrf_token %}
#         {{ form.management_form }}
#
#         {% for product, form, available_quantity in products_with_forms %}
#             <article class="media content-section">
#               <div class="media-body">
#                 <h5 class="article-title">{{ product.name }}</h5>
#                 <div>
#                     <a class="mr-2"><strong>Cena (za szt/kg): {{ product.price }} zł</strong></a>
#                   <a class="article-content">Opis: {{ product.description }}</a>
#                 </div>
#                 <div class="article-metadata">
#                     <a class="text-muted">Dostępne wagi(kg)/liczba sztuk: </a>
#                     {% for weight_scheme in product.weight_schemes.all %}
#                         <a class="text-muted">{{ weight_scheme.quantity|format_decimal:3 }},</a>
#                     {% endfor %}
#                 </div>
#                 <div class="article-metadata">
#                     <a class="text-muted">Status produktu: </a>
#                     {% for status in product.statuses.all %}
#                         <a class="text-muted">{{ status.status_type }},</a>
#                     {% endfor %}
#                 </div>
#                 <div class="article-metadata">
#                     <a class="text-muted">Zostało jeszcze: {{ available_quantity|format_decimal:3 }} sztuk/kg </a>
#                 </div>
#                     {{ form }}
#                     <input type="submit" name="submit" value="Dodaj">
#               </div>
#             </article>
#         {% endfor %}
#
#     </form>
# </div>
#
#
# <div class="col-md-4">
#   <div class="content-section sticky-element">
#     <h3>Twoje zamówienie:</h3>
#     <p class='text-muted'>Wartość zamówienia: {{ order_cost|floatformat:"2" }} zł.</p>
#     <ul class="list-group">
#     {% for orderitem in orderitems %}
#       <li class="list-group-item list-group-item-light">{{ orderitem.product }}: {{ orderitem.quantity|format_decimal:3 }}</li>
#     {% endfor %}
#     </ul>
#   </div>
# </div>
#
# <script>
#     function goToSelectedLink() {
#         var select = document.getElementById("producers");
#         var selectedOption = select.options[select.selectedIndex].value;
#         if (selectedOption) {
#             window.location.href = selectedOption;
#         }
#     }
# </script>
#
# <script>
#     window.addEventListener('scroll', () => {
#         const stickyElement = document.querySelector('.sticky-element');
#         const content = document.querySelector('.content');
#         const container = document.querySelector('.container');
#
#         const containerRect = container.getBoundingClientRect();
#         const contentRect = content.getBoundingClientRect();
#
#         const isSticky = containerRect.top <= 0 && contentRect.bottom >= window.innerHeight;
#
#         if (isSticky) {
#             stickyElement.style.width = `${containerRect.width}px`;
#             stickyElement.style.left = `${containerRect.left}px`;
#         } else {
#             stickyElement.style.width = 'auto';
#             stickyElement.style.left = 'auto';
#         }
#     });
# </script>
#
# <script>
#         // messages.js
#     function showMessages() {
#         const messages = document.querySelectorAll('.alert');
#         messages.forEach((message) => {
#             message.style.opacity = 1;
#             message.style.visibility = 'visible';
#
#             setTimeout(() => {
#                 message.style.opacity = 0;
#                 message.style.visibility = 'hidden';
#
#                 // Remove the message from the DOM after fading out
#                 setTimeout(() => {
#                     message.remove();
#                 }, 10); // Adjust the duration for fading out (0.5s in this example)
#             }, 12000); // Hide the message after 15 seconds (15000 milliseconds)
#         });
#     }
#
#     // Call the showMessages function when the page loads
#     document.addEventListener('DOMContentLoaded', showMessages);
# </script>
#
# {% endblock content%}
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
# # quantity
# # product.price
# #
# #
#
# # "product_id",
# # "quantity",
#
# # "id",
# # "order_id",
# # "item_ordered_date"
#
#
#
# # "id",
# # "producer_id",
# # "name",
# # "description",
# # "order_max_quantity",
# # "quantity_in_stock",
# # "price",
# # "order_deadline",
# # "quantity_delivered_this_week",
# # "is_visible"
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#

from pytest_factoryboy import register
from .factories import (
    ProducerFactory,
    ProductFactory,
    WeightSchemeFactory,
    StatusFactory,
    UserFactory,
    OrderFactory,
    OrderItemFactory,
    OrderWithProductFactory,
)

register(ProducerFactory)
register(StatusFactory)
register(WeightSchemeFactory)
register(ProductFactory)
register(UserFactory)
register(OrderFactory)

register(OrderItemFactory)
register(OrderWithProductFactory)


# to chyba do śmieci

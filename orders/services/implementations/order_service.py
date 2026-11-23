from ...repositories.order_repository import or_
from .product_processor import product_processor


class OrderService:
    def process_order(self, order_id):
        order = or_.find_by_id(order_id).get()
        print(order)
        for product in order.get_items():
            product_processor.process(product)

        return order


order_service = OrderService()

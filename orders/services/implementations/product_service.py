from datetime import date, timedelta
from ...repositories.product_repository import product_repository
from .notification_service import ns

class ProductService:
    def notify_delay(self, lead_time, product):
        product.lead_time = lead_time
        product_repository.save(product)
        ns.send_delay_notification(lead_time, product.name)

    def handle_seasonal_product(self, product):
        if date.today() + timedelta(days=product.lead_time) > product.season_end_date:
            ns.send_out_of_stock_notification(product.name)
            product.available = 0
            product_repository.save(product)
        elif product.season_start_date > date.today():
            ns.send_out_of_stock_notification(product.name)
            product_repository.save(product)
        else:
            self.notify_delay(product.lead_time, product)

    def handle_expired_product(self, product):
        if product.available > 0 and product.expiry_date > date.today():
            product.available -= 1
            product_repository.save(product)
        else:
            product.available = 0
            product_repository.save(product)
            ns.send_expiry_notification(product.name)

product_service = ProductService()

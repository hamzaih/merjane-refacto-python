from datetime import date

from ...repositories.product_repository import pr
from .product_service import ps


class ProductProcessor:
    def process(self, product):
        if product.type == "NORMAL":
            self._process_normal(product)
        elif product.type == "SEASONAL":
            self._process_seasonal(product)
        elif product.type == "EXPIRABLE":
            self._process_expirable(product)

    def _process_normal(self, product):
        if product.available > 0:
            product.available -= 1
            pr.save(product)
        elif product.lead_time > 0:
            ps.notify_delay(product.lead_time, product)

    def _process_seasonal(self, product):
        if (date.today() > product.season_start_date
                and date.today() < product.season_end_date
                and product.available > 0):
            product.available -= 1
            pr.save(product)
        else:
            ps.handle_seasonal_product(product)

    def _process_expirable(self, product):
        if product.available > 0 and product.expiry_date > date.today():
            product.available -= 1
            pr.save(product)
        else:
            ps.handle_expired_product(product)

product_processor = ProductProcessor()

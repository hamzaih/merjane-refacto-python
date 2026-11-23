from abc import ABC, abstractmethod
from datetime import date

from ...repositories.product_repository import product_repository
from .product_service import product_service


class ProductProcessingStrategy(ABC):
    @abstractmethod
    def process(self, product):
        pass


class NormalProductStrategy(ProductProcessingStrategy):
    def process(self, product):
        if product.available > 0:
            product.available -= 1
            product_repository.save(product)
        elif product.lead_time > 0:
            product_service.notify_delay(product.lead_time, product)


class SeasonalProductStrategy(ProductProcessingStrategy):
    def process(self, product):
        if (date.today() > product.season_start_date
                and date.today() < product.season_end_date
                and product.available > 0):
            product.available -= 1
            product_repository.save(product)
        else:
            product_service.handle_seasonal_product(product)


class ExpirableProductStrategy(ProductProcessingStrategy):
    def process(self, product):
        if product.available > 0 and product.expiry_date > date.today():
            product.available -= 1
            product_repository.save(product)
        else:
            product_service.handle_expired_product(product)


class ProductProcessor:
    def __init__(self, strategies=None):
        self.strategies = strategies if strategies is not None else {
            'NORMAL': NormalProductStrategy(),
            'SEASONAL': SeasonalProductStrategy(),
            'EXPIRABLE': ExpirableProductStrategy(),
        }

    def process(self, product):
        strategy = self.strategies.get(product.type)
        if strategy is not None:
            strategy.process(product)


product_processor = ProductProcessor()

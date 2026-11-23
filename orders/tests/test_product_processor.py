from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock

from orders.services.implementations.product_processor import (
    ExpirableProductStrategy,
    NormalProductStrategy,
    ProductProcessor,
    SeasonalProductStrategy,
)


class TestProductProcessor(TestCase):
    def test_default_strategies_are_registered_for_each_product_type(self):
        processor = ProductProcessor()

        self.assertIsInstance(processor.strategies['NORMAL'], NormalProductStrategy)
        self.assertIsInstance(processor.strategies['SEASONAL'], SeasonalProductStrategy)
        self.assertIsInstance(processor.strategies['EXPIRABLE'], ExpirableProductStrategy)

    def test_dispatches_to_strategy_for_product_type(self):
        strategies = {
            'NORMAL': Mock(),
            'SEASONAL': Mock(),
            'EXPIRABLE': Mock(),
        }
        processor = ProductProcessor(strategies)

        for product_type, expected_strategy in strategies.items():
            with self.subTest(product_type=product_type):
                for strategy in strategies.values():
                    strategy.reset_mock()

                product = SimpleNamespace(type=product_type)
                processor.process(product)

                expected_strategy.process.assert_called_once_with(product)
                for other_type, other_strategy in strategies.items():
                    if other_type != product_type:
                        other_strategy.process.assert_not_called()

    def test_unknown_product_type_is_ignored(self):
        strategy = Mock()
        processor = ProductProcessor({'NORMAL': strategy})

        processor.process(SimpleNamespace(type='UNKNOWN'))

        strategy.process.assert_not_called()

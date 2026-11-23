# orders/tests/test_product_service_unit.py

import unittest
from datetime import date
from unittest.mock import patch

from orders.entities.product import Product
from orders.services.implementations.product_service import ProductService

class MyUnitTests(unittest.TestCase):
    @patch('orders.services.implementations.product_service.ns')
    @patch('orders.services.implementations.product_service.product_repository')
    def test_notify_delay(self, mock_product_repository, mock_ns):
        product = Product(
            name="RJ45 Cable",
            type="NORMAL",
            available=0,
            lead_time=15,
        )
        mock_product_repository.save.return_value = product
        product_service = ProductService()

        product_service.notify_delay(product.lead_time, product)

        self.assertEqual(0, product.available)
        self.assertEqual(15, product.lead_time)
        mock_product_repository.save.assert_called_once_with(product)
        mock_ns.send_delay_notification.assert_called_once_with(product.lead_time, product.name)

    @patch('orders.services.implementations.product_service.date')
    @patch('orders.services.implementations.product_service.ns')
    @patch('orders.services.implementations.product_service.product_repository')
    def test_handle_seasonal_product(self, mock_product_repository, mock_ns, mock_date):
        mock_date.today.return_value = date(2026, 6, 15)
        cases = [
            ('after season', date(2026, 6, 1), date(2026, 6, 16), 2, 0, 'stock'),
            ('before season', date(2026, 6, 20), date(2026, 7, 1), 2, 3, 'stock'),
            ('within season', date(2026, 6, 1), date(2026, 7, 1), 2, 3, 'delay'),
            ('arrival on season end', date(2026, 6, 1), date(2026, 6, 17), 2, 3, 'delay'),
        ]
        for label, start, end, lead_time, available, notification in cases:
            with self.subTest(label=label):
                mock_product_repository.reset_mock()
                mock_ns.reset_mock()
                product = Product(name='Seasonal product', type='SEASONAL', available=3,
                            lead_time=lead_time, season_start_date=start, season_end_date=end)

                ProductService().handle_seasonal_product(product)

                self.assertEqual(available, product.available)
                mock_product_repository.save.assert_called_once_with(product)
                if notification == 'stock':
                    mock_ns.send_out_of_stock_notification.assert_called_once_with(product.name)
                    mock_ns.send_delay_notification.assert_not_called()
                else:
                    mock_ns.send_delay_notification.assert_called_once_with(lead_time, product.name)
                    mock_ns.send_out_of_stock_notification.assert_not_called()

    @patch('orders.services.implementations.product_service.date')
    @patch('orders.services.implementations.product_service.ns')
    @patch('orders.services.implementations.product_service.product_repository')
    def test_handle_expiring_product(self, mock_product_repository, mock_ns, mock_date):
        mock_date.today.return_value = date(2026, 6, 15)
        cases = [
            ('available and fresh', 3, date(2026, 6, 16), 2, False),
            ('expired', 3, date(2026, 6, 14), 0, True),
            ('expires today', 3, date(2026, 6, 15), 0, True),
            ('out of stock', 0, date(2026, 6, 16), 0, True),
        ]
        for label, initial, expiry, expected, notified in cases:
            with self.subTest(label=label):
                mock_product_repository.reset_mock()
                mock_ns.reset_mock()
                product = Product(name='Expirable product', type='EXPIRABLE', available=initial,
                            expiry_date=expiry)

                ProductService().handle_expired_product(product)

                self.assertEqual(expected, product.available)
                mock_product_repository.save.assert_called_once_with(product)
                if notified:
                    mock_ns.send_expiry_notification.assert_called_once_with(product.name)
                else:
                    mock_ns.send_expiry_notification.assert_not_called()

if __name__ == '__main__':
    unittest.main()

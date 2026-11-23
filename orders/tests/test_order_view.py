from datetime import date, timedelta
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from orders.entities.product import Product
from orders.entities.order import Order


class TestOrderView(TestCase):
    def setUp(self):
        self.order = Order.objects.create()
        self.url = reverse('process_order', args=[self.order.id])
        self.today = date(2026, 6, 15)
        date_patcher = patch('orders.services.implementations.product_processor.date')
        self.mock_date = date_patcher.start()
        self.addCleanup(date_patcher.stop)
        self.mock_date.today.return_value = self.today

    def add_product(self, **fields):
        product = Product.objects.create(**fields)
        self.order.products.add(product)
        return product

    def test_available_normal_product_decreases_stock(self):
        product = self.add_product(name='Cable', type='NORMAL', available=2)
        response = self.client.post(self.url)
        product.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'id': self.order.id})
        self.assertEqual(product.available, 1)

    @patch('orders.services.implementations.product_processor.product_service')
    def test_unavailable_normal_product_with_lead_time_notifies_delay(self, service):
        product = self.add_product(name='Cable', type='NORMAL', available=0, lead_time=3)
        self.client.post(self.url)
        product.refresh_from_db()

        self.assertEqual(product.available, 0)
        service.notify_delay.assert_called_once_with(3, product)

    @patch('orders.services.implementations.product_processor.product_service')
    def test_unavailable_normal_product_without_lead_time_does_not_notify(self, service):
        product = self.add_product(name='Cable', type='NORMAL', available=0, lead_time=0)
        self.client.post(self.url)
        product.refresh_from_db()

        self.assertEqual(product.available, 0)
        service.notify_delay.assert_not_called()

    @patch('orders.services.implementations.product_processor.product_service')
    def test_available_product_during_season_decreases_stock(self, service):
        product = self.add_product(
            name='Melon', type='SEASONAL', available=2,
            season_start_date=self.today - timedelta(days=1),
            season_end_date=self.today + timedelta(days=1),
        )
        self.client.post(self.url)
        product.refresh_from_db()

        self.assertEqual(product.available, 1)
        service.handle_seasonal_product.assert_not_called()

    @patch('orders.services.implementations.product_processor.product_service')
    def test_seasonal_product_outside_season_or_out_of_stock_is_delegated(self, service):
        cases = [
            ('before season', 2, 1, 5),
            ('on season start', 2, 0, 5),
            ('on season end', 2, -5, 0),
            ('after season', 2, -5, -1),
            ('out of stock', 0, -1, 1),
        ]
        for label, available, start, end in cases:
            with self.subTest(label=label):
                self.order.products.clear()
                service.reset_mock()
                product = self.add_product(
                    name='Melon', type='SEASONAL', available=available,
                    season_start_date=self.today + timedelta(days=start),
                    season_end_date=self.today + timedelta(days=end),
                )
                self.client.post(self.url)
                product.refresh_from_db()

                self.assertEqual(product.available, available)
                service.handle_seasonal_product.assert_called_once_with(product)

    @patch('orders.services.implementations.product_processor.product_service')
    def test_available_fresh_product_decreases_stock(self, service):
        product = self.add_product(
            name='Milk', type='EXPIRABLE', available=2,
            expiry_date=self.today + timedelta(days=1),
        )
        self.client.post(self.url)
        product.refresh_from_db()

        self.assertEqual(product.available, 1)
        service.handle_expired_product.assert_not_called()

    @patch('orders.services.implementations.product_processor.product_service')
    def test_expired_or_unavailable_product_is_delegated(self, service):
        for label, available, expiry_offset in [
            ('expired', 2, -1), ('expires today', 2, 0), ('out of stock', 0, 1),
        ]:
            with self.subTest(label=label):
                self.order.products.clear()
                service.reset_mock()
                product = self.add_product(
                    name='Milk', type='EXPIRABLE', available=available,
                    expiry_date=self.today + timedelta(days=expiry_offset),
                )
                self.client.post(self.url)
                product.refresh_from_db()

                self.assertEqual(product.available, available)
                service.handle_expired_product.assert_called_once_with(product)

    def test_get_is_not_allowed(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    @patch('orders.services.implementations.product_processor.product_service')
    def test_process_order_should_return(self, mock_ns):
        products = [
            Product(available=15, lead_time=30, type="NORMAL",    name="USB Cable"),
            Product(available=10, lead_time=0,  type="NORMAL",    name="USB Dongle"),
            Product(available=15, lead_time=30, type="EXPIRABLE", name="Butter",
                    expiry_date=date.today() + timedelta(days=26)),
            Product(available=90, lead_time=6,  type="EXPIRABLE", name="Milk",
                    expiry_date=date.today() - timedelta(days=2)),
            Product(available=15, lead_time=30, type="SEASONAL",  name="Watermelon",
                    season_start_date=date.today() - timedelta(days=2),
                    season_end_date=date.today() + timedelta(days=58)),
            Product(available=15, lead_time=30, type="SEASONAL",  name="Grapes",
                    season_start_date=date.today() + timedelta(days=180),
                    season_end_date=date.today() + timedelta(days=240)),
        ]
        for product in products:
            product.save()

        o = Order.objects.create()
        o.products.set(products)

        url = reverse('process_order', args=[o.id])
        response = self.client.post(url, content_type="application/json")

        self.assertEqual(response.status_code, 200)
        result_order = Order.objects.get(id=o.id)
        self.assertEqual(result_order.id, o.id)

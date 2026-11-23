# orders/tests/test_process_order_integration.py

from datetime import date, timedelta
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from orders.entities.order import Order
from orders.entities.product import Product


class TestProcessOrderIntegration(TestCase):
    def setUp(self):
        self.today = date(2026, 8, 15)

        self.order = Order.objects.create()
        self.url = reverse("process_order", args=[self.order.id])

    @patch("orders.services.implementations.product_processor.date")
    @patch("orders.services.implementations.product_service.date")
    @patch("orders.services.implementations.product_service.ns")
    def test_expired_product_is_removed_from_stock_and_notified(
        self, mock_notifications, mock_service_date, mock_view_date
    ):
        mock_view_date.today.return_value = self.today
        mock_service_date.today.return_value = self.today

        product = Product.objects.create(
            name="Milk",
            type="EXPIRABLE",
            available=5,
            expiry_date=self.today - timedelta(days=1),
        )
        self.order.products.add(product)

        response = self.client.post(self.url)

        product.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"id": self.order.id})
        self.assertEqual(product.available, 0)
        mock_notifications.send_expiry_notification.assert_called_once_with("Milk")
from datetime import date

from ...repositories.order_repository import or_
from ...repositories.product_repository import pr
from .product_service import ps


class OrderService:
    def process_order(self, order_id):
        order = or_.find_by_id(order_id).get()
        print(order)
        for p in order.get_items():
            if p.type == "NORMAL":
                if p.available > 0:
                    p.available = p.available - 1
                    pr.save(p)
                else:
                    lead_time = p.lead_time
                    if lead_time > 0:
                        ps.notify_delay(lead_time, p)

            elif p.type == "SEASONAL":
                if (date.today() > p.season_start_date and date.today() < p.season_end_date and p.available > 0):
                    p.available = p.available - 1
                    pr.save(p)
                else:
                    ps.handle_seasonal_product(p)

            elif p.type == "EXPIRABLE":
                if p.available > 0 and p.expiry_date > date.today():
                    p.available = p.available - 1
                    pr.save(p)
                else:
                    ps.handle_expired_product(p)

        return order


order_service = OrderService()

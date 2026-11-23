from ..entities.product import Product

class ProductRepository:
    def find_by_id(self, id):
        return Product.objects.filter(pk=id)

    def save(self, product):
        product.save()

product_repository = ProductRepository()

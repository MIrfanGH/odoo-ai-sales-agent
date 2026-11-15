import logging
import xmlrpc.client

from app.config import ODOO_URL, ODOO_DB, ODOO_USER, ODOO_PASSWORD

logger = logging.getLogger(__name__)


class OdooError(Exception):
    """Single error type for all Odoo failures, so callers handle one thing."""
    

class OdooClient:
    
    def __init__(self, url=ODOO_URL, db=ODOO_DB, user=ODOO_USER, password=ODOO_PASSWORD):
        self.db = db
        self.password = password
        try:
            common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
            self.uid = common.authenticate(db, user, password, {})  # user id, or False
        except OSError as e:  # Odoo not running / wrong URL
            raise OdooError(f"Cannot reach Odoo at {url}") from e
        if not self.uid:
            raise OdooError("Odoo login failed: check ODOO_DB, ODOO_USER, ODOO_PASSWORD")
        self.models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
        logger.info("Connected to Odoo db=%s uid=%s", db, self.uid)

    def _call(self, model, method, args, kwargs=None):
        # every Odoo API call goes through execute_kw
        try:
            return self.models.execute_kw(
                self.db, self.uid, self.password, model, method, args, kwargs or {}
            )
        except xmlrpc.client.Fault as e:  # Odoo-side error (bad field, access rights...)
            logger.error("Odoo %s.%s failed: %s", model, method, e.faultString)
            raise OdooError(f"Odoo {model}.{method} failed") from e

    def find_customer(self, name, limit=5):
        return self._call(
            "res.partner", "search_read",
            [[["name", "ilike", name], ["customer_rank", ">", 0]]],
            {"fields": ["id", "name", "email"], "limit": limit},
        )

    def check_stock(self, product_name, limit=5):
        # qty_available = on-hand stock, computed by Odoo from stock.quant
        return self._call(
            "product.product", "search_read",
            [[["name", "ilike", product_name]]],
            {"fields": ["id", "name", "qty_available", "list_price"], "limit": limit},
        )

    def create_draft_quotation(self, partner_id, product_id, qty):
        if qty <= 0:
            raise ValueError("Quantity must be greater than 0")
        # (0, 0, {...}) means "create a new order line"
        order_id = self._call(
            "sale.order", "create",
            [{"partner_id": partner_id,
              "order_line": [(0, 0, {"product_id": product_id, "product_uom_qty": qty})]}],
        )
        order = self._call("sale.order", "read", [[order_id]],
                           {"fields": ["name", "amount_total", "state"]})[0]
        logger.info("Created draft quotation %s", order["name"])
        return order


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    client = OdooClient()
    customers = client.find_customer("Gemini")
    products = client.check_stock("Office Chair")
    print(customers)
    print(products)
    print(client.create_draft_quotation(customers[0]["id"], products[0]["id"], 5))
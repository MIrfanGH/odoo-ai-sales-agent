import os
from dotenv import load_dotenv

load_dotenv()

def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing environment variable: {name}")
    return value

ODOO_URL = _require("ODOO_URL")
ODOO_DB = _require("ODOO_DB")
ODOO_USER = _require("ODOO_USER")
ODOO_PASSWORD = _require("ODOO_PASSWORD")
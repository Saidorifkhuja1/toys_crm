# bot.py

import os
import io
import time
import random
import logging
import threading
import requests
import numpy as np

from faker import Faker
from concurrent.futures import ThreadPoolExecutor, as_completed

# ─── CONFIG ────────────────────────────────────────────────────────────────────

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
ADMIN_USER = os.getenv("API_USER", "admin")
ADMIN_PASS = os.getenv("API_PASS", "password")
MAX_WORKERS = 16  # tune to your CPU/RAM
FAKE_SEED = 42

logging.basicConfig(level=logging.INFO, format="%(threadName)s %(message)s")
fake = Faker()
Faker.seed(FAKE_SEED)
random.seed(FAKE_SEED)
np.random.seed(FAKE_SEED)

# ─── AUTH ──────────────────────────────────────────────────────────────────────


def get_token():
    resp = requests.post(
        f"{BASE_URL}/token/",
        json={
            "username": ADMIN_USER,
            "password": ADMIN_PASS,
        },
    )
    resp.raise_for_status()
    return resp.json()["access"]


TOKEN = get_token()
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

# ─── HELPERS ────────────────────────────────────────────────────────────────────


def paginated_get(path):
    """Fetch all objects from a DRF list endpoint."""
    url = f"{BASE_URL}{path}"
    out = []
    while url:
        r = requests.get(url, headers=HEADERS)
        r.raise_for_status()
        data = r.json()
        out.extend(data.get("results", data))
        url = data.get("next")
    return out


# ─── STEP 1: CREATE CATEGORIES ─────────────────────────────────────────────────


def create_category(_):
    name = fake.unique.word().capitalize()
    r = requests.post(f"{BASE_URL}/categories/", headers=HEADERS, json={"name": name})
    r.raise_for_status()


def seed_categories(count=200):
    logging.info("Seeding %d categories…", count)
    with ThreadPoolExecutor(MAX_WORKERS) as ex:
        list(ex.map(create_category, range(count)))


# ─── STEP 2: CREATE SUPPLIERS ──────────────────────────────────────────────────


def create_supplier(_):
    name = fake.company()
    phone = fake.phone_number()
    r = requests.post(
        f"{BASE_URL}/suppliers/",
        headers=HEADERS,
        json={
            "full_name": name,
            "phone_number": phone,
        },
    )
    r.raise_for_status()


def seed_suppliers(count=100):
    logging.info("Seeding %d suppliers…", count)
    with ThreadPoolExecutor(MAX_WORKERS) as ex:
        list(ex.map(create_supplier, range(count)))


# ─── STEP 3: CREATE DEBTORS ────────────────────────────────────────────────────


def create_debtor(_):
    r = requests.post(
        f"{BASE_URL}/debtors/",
        headers=HEADERS,
        json={
            "full_name": fake.name(),
            "phone_number": fake.phone_number(),
            "has_debt": False,
        },
    )
    r.raise_for_status()


def seed_debtors(count=500):
    logging.info("Seeding %d debtors…", count)
    with ThreadPoolExecutor(MAX_WORKERS) as ex:
        list(ex.map(create_debtor, range(count)))


# ─── STEP 4: CREATE PRODUCTS & BATCHES ─────────────────────────────────────────


def create_product_and_batch(_):
    # pick random category & supplier
    cats = paginated_get("/categories/")
    sups = paginated_get("/suppliers/")
    category = random.choice(cats)["id"]
    supplier = random.choice(sups)["id"]

    # download a random image
    img = requests.get("https://picsum.photos/300/500", timeout=5)
    img.raise_for_status()
    img_file = io.BytesIO(img.content)
    img_file.name = f"{fake.uuid4()}.jpg"

    # upload image first
    files = {"file": img_file}
    r = requests.post(f"{BASE_URL}/media/upload/", headers=HEADERS, files=files)
    r.raise_for_status()
    media_id = r.json()["id"]

    # create product
    pname = fake.word().capitalize()
    prod_resp = requests.post(
        f"{BASE_URL}/products/",
        headers=HEADERS,
        json={
            "name": pname,
            "description": fake.sentence(),
            "image": media_id,
            "product_type": random.choice(["KG", "PIECE"]),
            "category": category,
            "supplier": supplier,
        },
    )
    prod_resp.raise_for_status()
    pid = prod_resp.json()["id"]

    # create batch
    qty = random.randint(3000, 10000)
    buy = random.randint(50_000, 200_000)
    # gradually increasing sell = buy × (1.1–1.5)
    sell = int(buy * random.uniform(1.1, 1.5))
    batch_resp = requests.post(
        f"{BASE_URL}/product-batch/",
        headers=HEADERS,
        json={
            "product": pid,
            "quantity": qty,
            "buy_price": buy,
            "sell_price": sell,
            "exchange_rate": random.randint(11000, 17000),
        },
    )
    batch_resp.raise_for_status()


def seed_products_and_batches(count=1000):
    logging.info("Seeding %d products & batches…", count)
    with ThreadPoolExecutor(MAX_WORKERS) as ex:
        list(ex.map(create_product_and_batch, range(count)))


# ─── STEP 5: CREATE SALES ───────────────────────────────────────────────────────


def make_random_sale(_):
    # pick random batches
    batches = paginated_get("/product-batch/")
    debtors = paginated_get("/debtors/")
    merchants = paginated_get("/merchants/")
    debtor = random.choice(debtors)["id"]
    merchant = random.choice(merchants)["id"]

    # pick 10–90 distinct batches
    chosen = random.sample(batches, k=random.randint(10, 90))
    total_sold = 0
    items = []

    # build sale items
    for b in chosen:
        q = random.randint(50, 500)
        items.append({"product": b["product"], "quantity": q})
        total_sold += q * b["sell_price"]

    # build payments
    payments = []
    # exchange rate for sale
    er = random.randint(11000, 17000)
    remaining = total_sold
    # decide how many payments (0–3)
    for __ in range(random.randint(0, 3)):
        if remaining <= 0:
            break
        pay = random.randint(0, int(remaining))
        payments.append({"method": fake.credit_card_provider(), "amount": pay})
        remaining -= pay

    sale_payload = {
        "merchant": merchant,
        "debtor": debtor if remaining > 0 else None,
        "total_sold": total_sold,
        "total_paid": total_sold - remaining if payments else 0,
        "exchange_rate": er,
        "items": items,
        "payments": payments,
    }
    r = requests.post(f"{BASE_URL}/sales/", headers=HEADERS, json=sale_payload)
    if r.status_code != 201:
        logging.error("Sale failed: %s → %s", r.text, sale_payload)
    else:
        logging.info(
            "Sale OK, sold=%d paid=%d debt=%d",
            total_sold,
            total_sold - remaining,
            remaining,
        )


def seed_sales(count=2000):
    logging.info("Seeding %d sales…", count)
    with ThreadPoolExecutor(MAX_WORKERS) as ex:
        list(ex.map(make_random_sale, range(count)))


# ─── MAIN ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    start = time.time()

    seed_categories(200)
    seed_suppliers(100)
    seed_debtors(500)
    seed_products_and_batches(1000)
    seed_sales(2000)

    logging.info("All done in %.1fs", time.time() - start)

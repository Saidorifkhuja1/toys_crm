import json
import random
import requests
from faker import Faker
import time
from datetime import datetime
import logging
from typing import List, Dict, Optional
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import io
from PIL import Image

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("product_bot.log"), logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


class ProductCreationBot:
    def __init__(
        self, api_base_url: str, tokens_file: str = "tokens.json", max_workers: int = 5
    ):
        """
        Initialize the product creation bot

        Args:
            api_base_url: Base URL for the API (e.g., "http://localhost:8000")
            tokens_file: Path to JSON file containing authentication tokens
            max_workers: Maximum number of threads for concurrent execution
        """
        self.api_base_url = api_base_url.rstrip("/")
        self.tokens_file = tokens_file
        self.fake = Faker()
        self.tokens = self._load_tokens()
        self.session = requests.Session()
        self.max_workers = max_workers
        self.lock = threading.Lock()  # For thread-safe operations

        # Cache for categories and suppliers to avoid repeated API calls
        self.categories_cache = []
        self.suppliers_cache = []
        self.cache_lock = threading.Lock()

        # Product categories for realistic naming
        self.product_categories = [
            "Electronics",
            "Clothing",
            "Food & Beverages",
            "Home & Garden",
            "Sports & Recreation",
            "Books & Media",
            "Health & Beauty",
            "Automotive",
            "Tools & Hardware",
            "Toys & Games",
        ]

        # Product types with realistic names
        self.product_types = {
            "KG": [
                "Rice",
                "Wheat",
                "Sugar",
                "Salt",
                "Flour",
                "Coffee",
                "Tea",
                "Spices",
                "Meat",
                "Vegetables",
            ],
            "PIECE": [
                "Phone",
                "Laptop",
                "Shirt",
                "Shoes",
                "Book",
                "Toy",
                "Tool",
                "Watch",
                "Bag",
                "Bottle",
            ],
        }

        # Realistic suppliers
        self.suppliers = [
            "Global Electronics Inc",
            "Fashion Forward Ltd",
            "Fresh Foods Co",
            "Home Essentials",
            "Sports World",
            "Tech Solutions",
            "Quality Imports",
            "Local Produce",
            "Premium Goods",
            "Wholesale Direct",
        ]

    def _load_tokens(self) -> List[str]:
        """Load authentication tokens from JSON file"""
        try:
            if not os.path.exists(self.tokens_file):
                logger.error(f"Tokens file {self.tokens_file} not found")
                return []

            with open(self.tokens_file, "r") as f:
                data = json.load(f)
                tokens = data.get("tokens", [])
                logger.info(f"Loaded {len(tokens)} tokens from {self.tokens_file}")
                return tokens
        except Exception as e:
            logger.error(f"Error loading tokens: {e}")
            return []

    def _get_random_token(self) -> Optional[str]:
        """Get a random token from the loaded tokens (thread-safe)"""
        with self.lock:
            if not self.tokens:
                logger.error("No tokens available")
                return None
            return random.choice(self.tokens)

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: dict = None,
        token: str = None,
        files: dict = None,
    ) -> requests.Response:
        """Make an authenticated API request"""
        url = f"{self.api_base_url}{endpoint}"
        headers = {}

        if token:
            headers["Authorization"] = f"Bearer {token}"

        # Create a new session for each thread to avoid conflicts
        session = requests.Session()

        try:
            if method.upper() == "GET":
                response = session.get(url, headers=headers)
            elif method.upper() == "POST":
                if files:
                    # Don't set Content-Type for multipart/form-data
                    response = session.post(
                        url, data=data, files=files, headers=headers
                    )
                else:
                    headers["Content-Type"] = "application/json"
                    response = session.post(url, json=data, headers=headers)
            elif method.upper() == "PUT":
                headers["Content-Type"] = "application/json"
                response = session.put(url, json=data, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            return response
        finally:
            session.close()

    def fetch_random_image(self) -> Optional[bytes]:
        """Fetch a random image from Picsum Photos"""
        try:
            # Using 300x500 as specified
            image_url = "https://picsum.photos/300/500"
            response = requests.get(image_url, timeout=10)

            if response.status_code == 200:
                logger.info(f"Successfully fetched image from {image_url}")
                return response.content
            else:
                logger.error(f"Failed to fetch image: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error fetching image: {e}")
            return None

    def upload_image_to_product(self, image_data: bytes, product_id: int, token: str) -> bool:
        """Upload image to a specific product using the media API"""
        try:
            # Create a file-like object from image data
            image_file = io.BytesIO(image_data)

            # Generate a random filename
            filename = f"product_{product_id}_{int(time.time())}_{random.randint(1000, 9999)}.jpg"

            # Prepare files and data for multipart upload
            files = {"image": (filename, image_file, "image/jpeg")}
            data = {"product_id": str(product_id)}

            # Upload to media API endpoint
            response = self._make_request(
                "POST", "/media/upload/", data=data, files=files, token=token
            )

            if response.status_code == 201:
                logger.info(f"Successfully uploaded image for product {product_id}")
                return True
            else:
                logger.error(
                    f"Failed to upload image: {response.status_code} - {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"Error uploading image: {e}")
            return False

    def get_or_create_category(self, token: str) -> Optional[int]:
        """Get existing category or create a new one (thread-safe with caching)"""
        try:
            with self.cache_lock:
                # Check cache first
                if self.categories_cache:
                    return random.choice(self.categories_cache)["id"]

            # Try to get existing categories
            response = self._make_request("GET", "/categories/", token=token)
            if response.status_code == 200:
                categories = response.json()
                if categories:
                    with self.cache_lock:
                        self.categories_cache = categories
                    return random.choice(categories)["id"]

            # Create new category if none exist
            category_name = random.choice(self.product_categories)
            category_data = {"name": category_name}

            response = self._make_request(
                "POST", "/categories/", data=category_data, token=token
            )
            if response.status_code == 201:
                new_category = response.json()
                with self.cache_lock:
                    self.categories_cache.append(new_category)
                return new_category["id"]
            else:
                logger.error(
                    f"Failed to create category: {response.status_code} - {response.text}"
                )
                return None

        except Exception as e:
            logger.error(f"Error handling category: {e}")
            return None

    def get_or_create_supplier(self, token: str) -> Optional[int]:
        """Get existing supplier or create a new one (thread-safe with caching)"""
        try:
            with self.cache_lock:
                # Check cache first
                if self.suppliers_cache:
                    return random.choice(self.suppliers_cache)["id"]

            # Try to get existing suppliers
            response = self._make_request("GET", "/suppliers/", token=token)
            if response.status_code == 200:
                suppliers = response.json()
                if suppliers:
                    with self.cache_lock:
                        self.suppliers_cache = suppliers
                    return random.choice(suppliers)["id"]

            # Create new supplier if none exist
            supplier_name = random.choice(self.suppliers)
            supplier_data = {
                "full_name": supplier_name,
                "phone_number": self.fake.phone_number()[:20],  # Limit to 20 chars
            }

            response = self._make_request(
                "POST", "/suppliers/", data=supplier_data, token=token
            )
            if response.status_code == 201:
                new_supplier = response.json()
                with self.cache_lock:
                    self.suppliers_cache.append(new_supplier)
                return new_supplier["id"]
            else:
                logger.error(
                    f"Failed to create supplier: {response.status_code} - {response.text}"
                )
                return None

        except Exception as e:
            logger.error(f"Error handling supplier: {e}")
            return None

    def generate_product_data(self, token: str) -> Optional[Dict]:
        """Generate realistic product data"""
        try:
            # Choose product type
            product_type = random.choice(["KG", "PIECE"])

            # Generate product name based on type
            base_name = random.choice(self.product_types[product_type])
            brand = self.fake.company().split()[0]  # Take first word as brand
            adjective = random.choice(
                ["Premium", "Deluxe", "Professional", "Standard", "Economy", "Organic"]
            )

            name = f"{adjective} {brand} {base_name}"

            # Generate prices based on product type
            if product_type == "KG":
                buy_price = random.randint(1000, 10000)  # 10-100 currency units per kg
                sell_price = int(buy_price * random.uniform(1.2, 2.0))  # 20-100% markup
            else:
                buy_price = random.randint(5000, 500000)  # 50-5000 currency units per piece
                sell_price = int(buy_price * random.uniform(1.1, 1.8))  # 10-80% markup

            # Get category and supplier - these are critical and must not be None
            category_id = self.get_or_create_category(token)
            if category_id is None:
                logger.error("Failed to get/create category")
                return None

            supplier_id = self.get_or_create_supplier(token)
            # supplier_id can be None as it's optional in the model

            product_data = {
                "name": name,
                "description": f"{adjective} quality {base_name.lower()} from {brand}. {self.fake.text(max_nb_chars=200)}",
                "product_type": product_type,
                "category_id": category_id,
                "product_batch": {
                    "quantity": random.randint(10, 1000),
                    "buy_price": buy_price,
                    "sell_price": sell_price,
                    "exchange_rate": (
                        random.randint(11000, 13000)
                        if random.choice([True, False])
                        else None
                    ),
                },
            }

            # Add supplier_id only if it's not None
            if supplier_id is not None:
                product_data["supplier_id"] = supplier_id

            return product_data

        except Exception as e:
            logger.error(f"Error generating product data: {e}")
            return None

    def create_product(self, token: str) -> bool:
        """Create a single product with optional image upload"""
        try:
            # Generate product data
            product_data = self.generate_product_data(token)
            if not product_data:
                logger.error("Failed to generate product data")
                return False

            # Create the product first
            response = self._make_request(
                "POST", "/products/", data=product_data, token=token
            )

            if response.status_code == 201:
                product = response.json()
                product_id = product["id"]
                logger.info(
                    f"Successfully created product: {product['name']} (ID: {product_id}) - Thread: {threading.current_thread().name}"
                )

                # Try to upload image after product creation
                image_data = self.fetch_random_image()
                if image_data:
                    self.upload_image_to_product(image_data, product_id, token)
                else:
                    logger.warning(f"No image uploaded for product {product_id}")

                return True
            else:
                logger.error(
                    f"Failed to create product: {response.status_code} - {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"Error creating product: {e}")
            return False

    def create_single_product_with_token(self, _) -> bool:
        """Create a single product with a random token (for threading)"""
        token = self._get_random_token()
        if not token:
            logger.error("No token available, skipping product creation")
            return False

        return self.create_product(token)

    def create_products_batch(
        self, count: int, use_threading: bool = True
    ) -> Dict[str, int]:
        """Create multiple products with optional threading"""
        results = {"success": 0, "failed": 0}

        logger.info(
            f"Starting batch creation of {count} products (Threading: {use_threading})"
        )

        if use_threading:
            # Use ThreadPoolExecutor for concurrent execution
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all tasks
                futures = [
                    executor.submit(self.create_single_product_with_token, i)
                    for i in range(count)
                ]

                # Process completed tasks
                for future in as_completed(futures):
                    try:
                        if future.result():
                            results["success"] += 1
                        else:
                            results["failed"] += 1
                    except Exception as e:
                        logger.error(f"Error in threaded product creation: {e}")
                        results["failed"] += 1
        else:
            # Sequential execution (original behavior)
            for i in range(count):
                token = self._get_random_token()
                if not token:
                    logger.error("No token available, skipping product creation")
                    results["failed"] += 1
                    continue

                logger.info(f"Creating product {i+1}/{count}")

                if self.create_product(token):
                    results["success"] += 1
                else:
                    results["failed"] += 1

        logger.info(
            f"Batch creation completed: {results['success']} successful, {results['failed']} failed"
        )
        return results

    def run_continuous(
        self,
        interval: int = 60,
        products_per_batch: int = 5,
        use_threading: bool = True,
    ):
        """Run the bot continuously, creating products at intervals"""
        logger.info(
            f"Starting continuous mode: {products_per_batch} products every {interval} seconds (Threading: {use_threading})"
        )

        try:
            while True:
                logger.info("Starting new batch creation cycle")
                results = self.create_products_batch(
                    products_per_batch, use_threading=use_threading
                )

                logger.info(
                    f"Batch completed. Waiting {interval} seconds until next batch..."
                )
                time.sleep(interval)

        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.error(f"Error in continuous mode: {e}")


# Example usage
if __name__ == "__main__":
    # Configuration
    API_BASE_URL = "http://localhost:9000"  # Change to your API URL
    TOKENS_FILE = "tests/user_tokens.json"
    MAX_WORKERS = 10  # Number of concurrent threads

    # Create bot instance
    bot = ProductCreationBot(API_BASE_URL, TOKENS_FILE, max_workers=MAX_WORKERS)

    # Example 1: Create 10 products with threading
    print("Creating 100 products with threading...")
    results = bot.create_products_batch(count=100, use_threading=True)
    print(f"Results: {results}")

    # Example 2: Create products without threading (sequential)
    # print("Creating 10 products without threading...")
    # results = bot.create_products_batch(count=10, use_threading=False)
    # print(f"Results: {results}")

    # Example 3: Run continuously with threading (uncomment to use)
    # bot.run_continuous(interval=30, products_per_batch=5, use_threading=True)
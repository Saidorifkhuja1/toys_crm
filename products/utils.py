import random
import string
from datetime import datetime
import os


def generate_random_string(length=8):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def product_image_upload_path(instance, filename):
    ext = filename.split(".")[-1]
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_str = generate_random_string()
    unique_filename = f"{instance.sku}_{timestamp}_{random_str}.{ext}"
    return os.path.join("products", instance.sku, unique_filename)


def generate_sku(prefix="SKU", length=6):
    date_part = datetime.now().strftime("%Y%m%d")
    random_part = "".join(
        random.choices(string.ascii_uppercase + string.digits, k=length)
    )
    return f"{prefix}-{date_part}-{random_part}"


def remove_product_image(product):
    """
    Removes existing image file from media folder if present.
    Raises FileNotFoundError if image doesn't exist on filesystem.
    """
    if product.image:
        image_path = os.path.join("media", product.image.name)
        if os.path.isfile(image_path):
            os.remove(image_path)
        else:
            raise FileNotFoundError(f"Image file not found: {image_path}")
    else:
        raise FileNotFoundError("Product has no associated image to remove")

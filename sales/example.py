{
    "is_debt": False,
    "total": 1000000,  # Total sale amount in base currency (e.g., UZS)
    "items": [
        {
            "product": "product 1",
            "quantity": 5,
        },
        {
            "product": "product 2",
            "quantity": 3,
        },
    ],
    "payment": {
        "uzs": 700000,
        "usd": 50,
        "exchange_rate": 8600,
        "card": 100000,
        "debt": 0
    },
}


{
    "items": [
        {
            "product": 0,
            "quantity": 0,
        }
    ],
    "payments": [
        {
            "method": "Card",
            "currency": "SUM",
            "amount": 0,
        }
    ],
    "is_debt": False,
    "total": 3000,
}

{
    "id": "sale-id-123",
    "merchant": {"id": "user-id-001", "username": "merchant1"},
    "is_debt": False,
    "total": 1000000,
    "amount_paid": 1100000,
    "created_at": "2025-05-17T14:00:00Z",
    "items": [
        {
            "id": "sale-item-001",
            "product": {"sku": "product-sku-123", "name": "Product Name"},
            "total_quantity": 7,
            "batches": [
                {
                    "id": "sib-001",
                    "product_batch": {
                        "id": "batch-id-001",
                        "quantity": 0,
                        "buy_price": "10000.00",
                        "sell_price": "15000.00",
                    },
                    "quantity_used": 5,
                },
                {
                    "id": "sib-002",
                    "product_batch": {
                        "id": "batch-id-002",
                        "quantity": 10,
                        "buy_price": "12000.00",
                        "sell_price": "15500.00",
                    },
                    "quantity_used": 2,
                },
            ],
        }
    ],
    "payments": [
        {
            "id": "payment-001",
            "method": "CASH",
            "currency": "UZS",
            "amount": 700000,
            "exchange_rate": 1,
        },
        {
            "id": "payment-002",
            "method": "CARD",
            "currency": "USD",
            "amount": 50,
            "exchange_rate": 8600,
        },
    ],
}

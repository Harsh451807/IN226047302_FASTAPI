# ============================================================
# main.py — FastAPI Assignment 2
# ============================================================

from fastapi import FastAPI, Query
from pydantic import BaseModel, Field
from typing import Optional, List

app = FastAPI()

# ============================================================
# PRODUCT DATA (shared across all endpoints)
# ============================================================
products = [
    {"id": 1, "name": "Wireless Mouse", "price": 499, "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "Notebook", "price": 99, "category": "Stationery", "in_stock": True},
    {"id": 3, "name": "USB Hub", "price": 799, "category": "Electronics", "in_stock": False},
    {"id": 4, "name": "Pen Set", "price": 49, "category": "Stationery", "in_stock": True},
]

# ============================================================
# STORAGE LISTS
# ============================================================
orders = []
feedback = []

# ============================================================
# PYDANTIC MODELS
# ============================================================

# Existing model for single orders
class OrderRequest(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0, le=100)

# Q3 — Customer Feedback model
class CustomerFeedback(BaseModel):
    customer_name: str = Field(..., min_length=2, max_length=100)
    product_id: int = Field(..., gt=0)
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=300)

# Q5 — Bulk Order models
class OrderItem(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0, le=50)

class BulkOrder(BaseModel):
    company_name: str = Field(..., min_length=2)
    contact_email: str = Field(..., min_length=5)
    items: List[OrderItem] = Field(..., min_length=1)

# ============================================================
# ROOT ENDPOINT
# ============================================================
@app.get("/")
def root():
    return {"message": "Welcome to the Product Store API"}

# ============================================================
# Q4 — GET /products/summary (Product Summary Dashboard)
# NOTE: This MUST come BEFORE /products/{product_id} routes
#       to avoid FastAPI treating "summary" as a product_id
# ============================================================
@app.get("/products/summary")
def product_summary():
    in_stock = [p for p in products if p["in_stock"]]
    out_stock = [p for p in products if not p["in_stock"]]
    expensive = max(products, key=lambda p: p["price"])
    cheapest = min(products, key=lambda p: p["price"])
    categories = list(set(p["category"] for p in products))
    return {
        "total_products": len(products),
        "in_stock_count": len(in_stock),
        "out_of_stock_count": len(out_stock),
        "most_expensive": {"name": expensive["name"], "price": expensive["price"]},
        "cheapest": {"name": cheapest["name"], "price": cheapest["price"]},
        "categories": categories,
    }

# ============================================================
# Q1 — GET /products/filter (Filter Products by min_price)
# Combined with existing category and max_price filters
# ============================================================
@app.get("/products/filter")
def filter_products(
    category: str = Query(None, description="Filter by category"),
    max_price: int = Query(None, description="Maximum price"),
    min_price: int = Query(None, description="Minimum price"),
):
    result = products.copy()

    if category:
        result = [p for p in result if p["category"].lower() == category.lower()]

    if max_price:
        result = [p for p in result if p["price"] <= max_price]

    if min_price:
        result = [p for p in result if p["price"] >= min_price]

    return {"filtered_products": result, "count": len(result)}

# ============================================================
# Q2 — GET /products/{product_id}/price (Get Only Price)
# ============================================================
@app.get("/products/{product_id}/price")
def get_product_price(product_id: int):
    for product in products:
        if product["id"] == product_id:
            return {"name": product["name"], "price": product["price"]}
    return {"error": "Product not found"}

# ============================================================
# GET /products/{product_id} (Get full product by ID)
# ============================================================
@app.get("/products/{product_id}")
def get_product(product_id: int):
    for product in products:
        if product["id"] == product_id:
            return product
    return {"error": "Product not found"}

# ============================================================
# Q3 — POST /feedback (Accept Customer Feedback)
# ============================================================
@app.post("/feedback")
def submit_feedback(data: CustomerFeedback):
    feedback.append(data.dict())
    return {
        "message": "Feedback submitted successfully",
        "feedback": data.dict(),
        "total_feedback": len(feedback),
    }

# ============================================================
# BONUS — POST /orders (Place Order — status starts as pending)
# ============================================================
@app.post("/orders")
def place_order(order: OrderRequest):
    product = None
    for p in products:
        if p["id"] == order.product_id:
            product = p
            break

    if not product:
        return {"error": "Product not found"}

    if not product["in_stock"]:
        return {"error": f"{product['name']} is out of stock"}

    total = product["price"] * order.quantity
    new_order = {
        "order_id": len(orders) + 1,
        "product_name": product["name"],
        "quantity": order.quantity,
        "total_price": total,
        "status": "pending",       # BONUS: starts as pending
    }
    orders.append(new_order)
    return {"message": "Order placed successfully", "order": new_order}

# ============================================================
# BONUS — GET /orders/{order_id} (Get Order by ID)
# ============================================================
@app.get("/orders/{order_id}")
def get_order(order_id: int):
    for order in orders:
        if order["order_id"] == order_id:
            return {"order": order}
    return {"error": "Order not found"}

# ============================================================
# BONUS — PATCH /orders/{order_id}/confirm (Confirm Order)
# ============================================================
@app.patch("/orders/{order_id}/confirm")
def confirm_order(order_id: int):
    for order in orders:
        if order["order_id"] == order_id:
            order["status"] = "confirmed"
            return {"message": "Order confirmed", "order": order}
    return {"error": "Order not found"}

# ============================================================
# Q5 — POST /orders/bulk (Validate & Place Bulk Order)
# ============================================================
@app.post("/orders/bulk")
def place_bulk_order(order: BulkOrder):
    confirmed, failed, grand_total = [], [], 0
    for item in order.items:
        product = next((p for p in products if p["id"] == item.product_id), None)
        if not product:
            failed.append({
                "product_id": item.product_id,
                "reason": "Product not found"
            })
        elif not product["in_stock"]:
            failed.append({
                "product_id": item.product_id,
                "reason": f"{product['name']} is out of stock"
            })
        else:
            subtotal = product["price"] * item.quantity
            grand_total += subtotal
            confirmed.append({
                "product": product["name"],
                "qty": item.quantity,
                "subtotal": subtotal
            })
    return {
        "company": order.company_name,
        "confirmed": confirmed,
        "failed": failed,
        "grand_total": grand_total,
    }

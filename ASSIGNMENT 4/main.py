# ============================================================
# main.py — FastAPI Assignment 4: Cart System Practice
# ============================================================

from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List

app = FastAPI(title="Shopping Cart API", version="1.0")

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
# STORAGE LISTS (reset on every server restart)
# ============================================================
cart = []
orders = []

# ============================================================
# PYDANTIC MODELS
# ============================================================
class CheckoutRequest(BaseModel):
    customer_name: str = Field(..., min_length=2, max_length=100)
    delivery_address: str = Field(..., min_length=10, max_length=300)

# ============================================================
# HELPER FUNCTION — Find product by ID
# ============================================================
def find_product(product_id: int):
    for product in products:
        if product["id"] == product_id:
            return product
    return None

# ============================================================
# ROOT ENDPOINT
# ============================================================
@app.get("/")
def root():
    return {"message": "Welcome to the Shopping Cart API"}

# ============================================================
# GET /products — View all products
# ============================================================
@app.get("/products")
def get_all_products():
    return {"products": products, "total": len(products)}

# ============================================================
# POST /cart/add — Add item to cart
# Handles: new item, duplicate (update qty), out of stock, not found
# ============================================================
@app.post("/cart/add")
def add_to_cart(
    product_id: int = Query(..., gt=0, description="Product ID to add"),
    quantity: int = Query(1, gt=0, le=50, description="Quantity to add"),
):
    # Step 1: Check if product exists
    product = find_product(product_id)
    if not product:
        raise HTTPException(
            status_code=404,
            detail=f"Product with id {product_id} not found"
        )

    # Step 2: Check if product is in stock
    if not product["in_stock"]:
        raise HTTPException(
            status_code=400,
            detail=f"{product['name']} is out of stock"
        )

    # Step 3: Check if product already exists in cart (update quantity)
    for item in cart:
        if item["product_id"] == product_id:
            item["quantity"] += quantity
            item["subtotal"] = product["price"] * item["quantity"]
            return {
                "message": "Cart updated",
                "cart_item": item
            }

    # Step 4: Product not in cart yet — add new item
    cart_item = {
        "product_id": product["id"],
        "product_name": product["name"],
        "quantity": quantity,
        "unit_price": product["price"],
        "subtotal": product["price"] * quantity,
    }
    cart.append(cart_item)

    return {
        "message": "Added to cart",
        "cart_item": cart_item
    }

# ============================================================
# GET /cart — View current cart contents
# ============================================================
@app.get("/cart")
def view_cart():
    if not cart:
        return {"message": "Cart is empty"}

    grand_total = sum(item["subtotal"] for item in cart)
    return {
        "items": cart,
        "item_count": len(cart),
        "grand_total": grand_total,
    }

# ============================================================
# DELETE /cart/{product_id} — Remove item from cart
# ============================================================
@app.delete("/cart/{product_id}")
def remove_from_cart(product_id: int):
    for i, item in enumerate(cart):
        if item["product_id"] == product_id:
            removed_item = cart.pop(i)
            return {
                "message": f"{removed_item['product_name']} removed from cart",
                "removed_item": removed_item,
                "remaining_items": len(cart),
            }

    raise HTTPException(
        status_code=404,
        detail=f"Product with id {product_id} not found in cart"
    )

# ============================================================
# POST /cart/checkout — Checkout all cart items
# Creates one order per cart item, then empties the cart
# ============================================================
@app.post("/cart/checkout")
def checkout(data: CheckoutRequest):
    # Step 1: Check if cart is empty
    if not cart:
        raise HTTPException(
            status_code=400,
            detail="Cart is empty — add items first"
        )

    # Step 2: Create orders from cart items
    orders_placed = []
    grand_total = 0

    for item in cart:
        order = {
            "order_id": len(orders) + 1,
            "customer_name": data.customer_name,
            "delivery_address": data.delivery_address,
            "product": item["product_name"],
            "product_id": item["product_id"],
            "quantity": item["quantity"],
            "unit_price": item["unit_price"],
            "total_price": item["subtotal"],
            "status": "confirmed",
        }
        orders.append(order)
        orders_placed.append(order)
        grand_total += item["subtotal"]

    # Step 3: Clear the cart
    cart.clear()

    return {
        "message": "Checkout successful",
        "customer_name": data.customer_name,
        "delivery_address": data.delivery_address,
        "orders_placed": orders_placed,
        "total_items_ordered": len(orders_placed),
        "grand_total": grand_total,
    }

# ============================================================
# GET /orders — View all placed orders
# ============================================================
@app.get("/orders")
def get_all_orders():
    if not orders:
        return {"message": "No orders placed yet", "orders": [], "total_orders": 0}

    return {
        "orders": orders,
        "total_orders": len(orders),
    }

# ============================================================
# GET /orders/{order_id} — View single order by ID
# ============================================================
@app.get("/orders/{order_id}")
def get_order(order_id: int):
    for order in orders:
        if order["order_id"] == order_id:
            return {"order": order}
    return {"error": "Order not found"}
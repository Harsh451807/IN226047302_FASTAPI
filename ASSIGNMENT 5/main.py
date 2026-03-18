from fastapi import FastAPI, Query
from fastapi.responses import Response
from starlette import status
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

# ── Original 4 Products ──
products = [
    {"id": 1, "name": "Wireless Mouse", "price": 499, "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "Notebook", "price": 99, "category": "Stationery", "in_stock": True},
    {"id": 3, "name": "USB Hub", "price": 799, "category": "Electronics", "in_stock": False},
    {"id": 4, "name": "Pen Set", "price": 49, "category": "Stationery", "in_stock": True},
]

# ── Orders List ──
orders = []

# ── Pydantic Models ──
class NewProduct(BaseModel):
    name: str
    price: int
    category: str
    in_stock: bool = True

class NewOrder(BaseModel):
    customer_name: str
    product_id: int
    quantity: int = 1

# ── Helper Function ──
def find_product(product_id: int):
    for p in products:
        if p["id"] == product_id:
            return p
    return None

# ── Root ──
@app.get("/")
def home():
    return {"message": "Welcome to the Product API — Day 6"}

# ══════════════════════════════════════════════
# POST — Add Product
# ══════════════════════════════════════════════
@app.post("/products")
def add_product(product: NewProduct, response: Response):
    for p in products:
        if p["name"].lower() == product.name.lower():
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"error": f"Product '{product.name}' already exists"}

    next_id = max(p["id"] for p in products) + 1
    new = {
        "id": next_id,
        "name": product.name,
        "price": product.price,
        "category": product.category,
        "in_stock": product.in_stock,
    }
    products.append(new)
    response.status_code = status.HTTP_201_CREATED
    return {"message": "Product added", "product": new}

# ══════════════════════════════════════════════
# Q1 — GET /products/search (already built in Day 6 code)
# ══════════════════════════════════════════════
@app.get("/products/search")
def search_products(keyword: str = Query(..., description="Search keyword")):
    results = [
        p for p in products
        if keyword.lower() in p["name"].lower()
    ]
    if not results:
        return {"message": f"No products found for: {keyword}"}
    return {"keyword": keyword, "total_found": len(results), "products": results}

# ══════════════════════════════════════════════
# Q2 — GET /products/sort (already built in Day 6 code)
# ══════════════════════════════════════════════
@app.get("/products/sort")
def sort_products(
    sort_by: str = Query("price", description="Sort by 'price' or 'name'"),
    order: str = Query("asc", description="'asc' or 'desc'"),
):
    if sort_by not in ["price", "name"]:
        return {"error": "sort_by must be 'price' or 'name'"}
    if order not in ["asc", "desc"]:
        return {"error": "order must be 'asc' or 'desc'"}

    reverse = (order == "desc")
    result = sorted(products, key=lambda p: p[sort_by], reverse=reverse)
    return {"sort_by": sort_by, "order": order, "products": result, "total": len(result)}

# ══════════════════════════════════════════════
# Q3 — GET /products/page (already built in Day 6 code)
# ══════════════════════════════════════════════
@app.get("/products/page")
def get_products_paged(
    page: int = Query(1, ge=1),
    limit: int = Query(2, ge=1, le=20),
):
    start = (page - 1) * limit
    paged = products[start: start + limit]
    total_pages = -(-len(products) // limit)
    return {
        "page": page,
        "limit": limit,
        "total": len(products),
        "total_pages": total_pages,
        "products": paged,
    }

# ══════════════════════════════════════════════
# Q4 — GET /orders/search (NEW — search orders by customer name)
# ══════════════════════════════════════════════
@app.get("/orders/search")
def search_orders(customer_name: str = Query(..., description="Customer name to search")):
    results = [
        o for o in orders
        if customer_name.lower() in o["customer_name"].lower()
    ]
    if not results:
        return {"message": f"No orders found for: {customer_name}"}
    return {
        "customer_name": customer_name,
        "total_found": len(results),
        "orders": results,
    }

# ══════════════════════════════════════════════
# BONUS — GET /orders/page (NEW — paginate orders)
# ══════════════════════════════════════════════
@app.get("/orders/page")
def get_orders_paged(
    page: int = Query(1, ge=1),
    limit: int = Query(3, ge=1, le=20),
):
    start = (page - 1) * limit
    return {
        "page": page,
        "limit": limit,
        "total": len(orders),
        "total_pages": -(-len(orders) // limit) if orders else 0,
        "orders": orders[start: start + limit],
    }

# ══════════════════════════════════════════════
# Q5 — GET /products/sort-by-category (NEW)
# ══════════════════════════════════════════════
@app.get("/products/sort-by-category")
def sort_by_category():
    result = sorted(products, key=lambda p: (p["category"], p["price"]))
    return {"products": result, "total": len(result)}

# ══════════════════════════════════════════════
# Q6 — GET /products/browse (NEW — search + sort + paginate)
# ══════════════════════════════════════════════
@app.get("/products/browse")
def browse_products(
    keyword: str = Query(None),
    sort_by: str = Query("price"),
    order: str = Query("asc"),
    page: int = Query(1, ge=1),
    limit: int = Query(4, ge=1, le=20),
):
    # Step 1: Search (filter)
    result = products
    if keyword:
        result = [p for p in result if keyword.lower() in p["name"].lower()]

    # Step 2: Sort
    if sort_by in ["price", "name"]:
        result = sorted(result, key=lambda p: p[sort_by], reverse=(order == "desc"))

    # Step 3: Paginate
    total = len(result)
    start = (page - 1) * limit
    paged = result[start: start + limit]

    return {
        "keyword": keyword,
        "sort_by": sort_by,
        "order": order,
        "page": page,
        "limit": limit,
        "total_found": total,
        "total_pages": -(-total // limit) if total > 0 else 0,
        "products": paged,
    }

# ══════════════════════════════════════════════
# GET All Products (with optional filters)
# ══════════════════════════════════════════════
@app.get("/products")
def get_products(
    category: Optional[str] = None,
    in_stock: Optional[bool] = None,
    sort_by: Optional[str] = None,
):
    result = products.copy()
    if category:
        result = [p for p in result if p["category"].lower() == category.lower()]
    if in_stock is not None:
        result = [p for p in result if p["in_stock"] == in_stock]
    if sort_by and sort_by in ["price", "name"]:
        result = sorted(result, key=lambda p: p[sort_by])
    return {"products": result, "total": len(result)}

# ══════════════════════════════════════════════
# GET Single Product — MUST BE LAST among /products routes
# ══════════════════════════════════════════════
@app.get("/products/{product_id}")
def get_product(product_id: int):
    product = find_product(product_id)
    if not product:
        return {"error": "Product not found"}
    return product

# ══════════════════════════════════════════════
# PUT — Update Product
# ══════════════════════════════════════════════
@app.put("/products/{product_id}")
def update_product(
    product_id: int,
    response: Response,
    price: Optional[int] = None,
    in_stock: Optional[bool] = None,
):
    product = find_product(product_id)
    if not product:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"error": "Product not found"}
    if price is not None:
        product["price"] = price
    if in_stock is not None:
        product["in_stock"] = in_stock
    return {"message": "Product updated", "product": product}

# ══════════════════════════════════════════════
# DELETE — Remove Product
# ══════════════════════════════════════════════
@app.delete("/products/{product_id}")
def delete_product(product_id: int, response: Response):
    product = find_product(product_id)
    if not product:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"error": "Product not found"}
    products.remove(product)
    return {"message": f"Product '{product['name']}' deleted"}

# ══════════════════════════════════════════════
# POST — Place Order
# ══════════════════════════════════════════════
@app.post("/orders")
def place_order(order: NewOrder, response: Response):
    product = find_product(order.product_id)
    if not product:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"error": "Product not found"}

    order_id = len(orders) + 1
    new_order = {
        "order_id": order_id,
        "customer_name": order.customer_name,
        "product_id": order.product_id,
        "product_name": product["name"],
        "quantity": order.quantity,
        "total_price": product["price"] * order.quantity,
    }
    orders.append(new_order)
    response.status_code = status.HTTP_201_CREATED
    return {"message": "Order placed", "order": new_order}

# ── GET All Orders ──
@app.get("/orders")
def get_orders():
    return {"orders": orders, "total": len(orders)}
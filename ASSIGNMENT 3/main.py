from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

# ── Initial product catalogue ──────────────────────────────────────
products = [
    {"id": 1, "name": "Wireless Mouse", "price": 499, "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "Notebook", "price": 99, "category": "Stationery", "in_stock": True},
    {"id": 3, "name": "USB Hub", "price": 799, "category": "Electronics", "in_stock": False},
    {"id": 4, "name": "Pen Set", "price": 49, "category": "Stationery", "in_stock": True},
]


# ── Pydantic model for POST body ──────────────────────────────────
class NewProduct(BaseModel):
    name: str
    price: int
    category: str
    in_stock: bool = True


# ── Helper ─────────────────────────────────────────────────────────
def find_product(product_id: int):
    for p in products:
        if p["id"] == product_id:
            return p
    return None


# ── Root ───────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"message": "Welcome to the Product API"}


# ── POST /products  ────────────────────────────────────────────────
@app.post("/products")
def add_product(product: NewProduct):
    # Duplicate-name check
    for p in products:
        if p["name"].lower() == product.name.lower():
            return JSONResponse(
                status_code=400,
                content={"error": f"Product '{product.name}' already exists"},
            )

    next_id = max(p["id"] for p in products) + 1 if products else 1
    new = {
        "id": next_id,
        "name": product.name,
        "price": product.price,
        "category": product.category,
        "in_stock": product.in_stock,
    }
    products.append(new)
    return JSONResponse(
        status_code=201,
        content={"message": "Product added", "product": new},
    )


# ── GET /products  (list + optional filters) ──────────────────────
@app.get("/products")
def get_products(
    category: Optional[str] = None,
    in_stock: Optional[bool] = None,
    sort_by: Optional[str] = None,
):
    result = products[:]

    if category:
        result = [p for p in result if p["category"].lower() == category.lower()]
    if in_stock is not None:
        result = [p for p in result if p["in_stock"] == in_stock]
    if sort_by and sort_by in ("price", "name"):
        result = sorted(result, key=lambda p: p[sort_by])

    return {"products": result, "total": len(result)}


# ───────────────────────────────────────────────────────────────────
# ⚠️  FIXED ROUTES go here — ABOVE /products/{product_id}
# ───────────────────────────────────────────────────────────────────

# ── Q5  GET /products/audit ────────────────────────────────────────
@app.get("/products/audit")
def product_audit():
    in_stock_list = [p for p in products if p["in_stock"]]
    out_stock_list = [p for p in products if not p["in_stock"]]
    stock_value = sum(p["price"] * 10 for p in in_stock_list)
    priciest = max(products, key=lambda p: p["price"])

    return {
        "total_products": len(products),
        "in_stock_count": len(in_stock_list),
        "out_of_stock_names": [p["name"] for p in out_stock_list],
        "total_stock_value": stock_value,
        "most_expensive": {"name": priciest["name"], "price": priciest["price"]},
    }


# ── ⭐ Bonus  PUT /products/discount ──────────────────────────────
@app.put("/products/discount")
def bulk_discount(
    category: str = Query(..., description="Category to discount"),
    discount_percent: int = Query(..., ge=1, le=99, description="% off"),
):
    updated = []
    for p in products:
        if p["category"].lower() == category.lower():
            p["price"] = int(p["price"] * (1 - discount_percent / 100))
            updated.append(p)

    if not updated:
        return {"message": f"No products found in category: {category}"}

    return {
        "message": f"{discount_percent}% discount applied to {category}",
        "updated_count": len(updated),
        "updated_products": updated,
    }


# ───────────────────────────────────────────────────────────────────
# Dynamic path-param routes BELOW fixed routes
# ───────────────────────────────────────────────────────────────────

# ── GET /products/{product_id} ─────────────────────────────────────
@app.get("/products/{product_id}")
def get_product(product_id: int):
    product = find_product(product_id)
    if not product:
        return JSONResponse(status_code=404, content={"error": "Product not found"})
    return product


# ── PUT /products/{product_id} ─────────────────────────────────────
@app.put("/products/{product_id}")
def update_product(
    product_id: int,
    name: Optional[str] = None,
    price: Optional[int] = None,
    category: Optional[str] = None,
    in_stock: Optional[bool] = None,
):
    product = find_product(product_id)
    if not product:
        return JSONResponse(status_code=404, content={"error": "Product not found"})

    if name is not None:
        product["name"] = name
    if price is not None:
        product["price"] = price
    if category is not None:
        product["category"] = category
    if in_stock is not None:
        product["in_stock"] = in_stock

    return {"message": "Product updated", "product": product}


# ── DELETE /products/{product_id} ──────────────────────────────────
@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    product = find_product(product_id)
    if not product:
        return JSONResponse(status_code=404, content={"error": "Product not found"})
    products.remove(product)
    return {"message": f"Product '{product['name']}' deleted"}
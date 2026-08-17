# -*- coding: utf-8 -*-
import sys

with open('database/psql.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add missing functions for PostgreSQL
new_funcs = '''

# ============================================================
# Product CRUD (PostgreSQL)
# ============================================================

def get_products(store_id=None, page=1, per_page=50, active_only=None, limit=None, **filters):
    db = get_db()
    cur = db._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    params = []
    conditions = []
    query = "SELECT * FROM products"
    if store_id:
        conditions.append("store_id = %s")
        params.append(store_id)
    if active_only is not None:
        conditions.append("is_active = %s")
        params.append(active_only)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY id DESC"
    actual_limit = limit or per_page
    if actual_limit:
        query += " LIMIT %s OFFSET %s"
        params.append(int(actual_limit))
        params.append((int(page) - 1) * int(actual_limit))
    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()
    return [dict(r) for r in rows]


def get_product(product_id):
    db = get_db()
    cur = db._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM products WHERE id = %s", [product_id])
    row = cur.fetchone()
    cur.close()
    return dict(row) if row else None


def get_product_by_barcode(barcode, store_id=None):
    db = get_db()
    cur = db._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    params = [barcode]
    query = "SELECT * FROM products WHERE barcode = %s"
    if store_id:
        query += " AND store_id = %s"
        params.append(store_id)
    cur.execute(query, params)
    row = cur.fetchone()
    cur.close()
    return dict(row) if row else None


def get_product_by_sku(sku, store_id=None):
    db = get_db()
    cur = db._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    params = [sku]
    query = "SELECT * FROM products WHERE sku = %s"
    if store_id:
        query += " AND store_id = %s"
        params.append(store_id)
    cur.execute(query, params)
    row = cur.fetchone()
    cur.close()
    return dict(row) if row else None


def create_product(data):
    db = get_db()
    cur = db._conn.cursor()
    cur.execute(
        "INSERT INTO products (store_id, name, sku, barcode, category, price, cost, unit, image_url, description, is_active) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
        [data.get("store_id", 1), data["name"], data.get("sku", ""),
         data.get("barcode", ""), data.get("category", ""),
         float(data.get("price", 0)), float(data.get("cost", 0)),
         data.get("unit", "piece"), data.get("image_url", ""),
         data.get("description", ""), data.get("is_active", True)]
    )
    product_id = cur.fetchone()[0]
    db.commit()
    cur.close()
    return get_product(product_id)


def update_product(product_id, data):
    db = get_db()
    allowed = ["name","sku","barcode","category","price","cost","unit","image_url","description","is_active"]
    updates = []
    params = []
    for field in allowed:
        if field in data:
            updates.append(f"{field} = %s")
            params.append(data[field])
    if not updates:
        return get_product(product_id)
    params.append(product_id)
    cur = db._conn.cursor()
    cur.execute(f"UPDATE products SET {', '.join(updates)} WHERE id = %s", params)
    db.commit()
    cur.close()
    return get_product(product_id)


def search_products(query, store_id=None, limit=20):
    db = get_db()
    cur = db._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    params = [f"%{query}%", f"%{query}%"]
    sql = "SELECT * FROM products WHERE (name ILIKE %s OR sku ILIKE %s)"
    if store_id:
        sql += " AND store_id = %s"
        params.append(store_id)
    sql += " LIMIT %s"
    params.append(limit)
    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    return [dict(r) for r in rows]


# ============================================================
# Inventory (PostgreSQL)
# ============================================================

def get_inventory(product_id=None, store_id=None):
    db = get_db()
    cur = db._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    params = []
    conditions = []
    query = "SELECT * FROM inventory"
    if product_id:
        conditions.append("product_id = %s")
        params.append(product_id)
    if store_id:
        conditions.append("store_id = %s")
        params.append(store_id)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()
    return [dict(r) for r in rows]


def update_inventory(product_id, data):
    db = get_db()
    cur = db._conn.cursor()
    existing = get_inventory(product_id)
    store_id = data.get("store_id", 1)
    if existing:
        updates = []
        params = []
        for field in ["store_quantity","online_quantity","warehouse_quantity"]:
            if field in data:
                updates.append(f"{field} = %s")
                params.append(data[field])
        if updates:
            params.append(product_id)
            cur.execute(f"UPDATE inventory SET {', '.join(updates)} WHERE product_id = %s", params)
            db.commit()
    else:
        cur.execute(
            "INSERT INTO inventory (product_id, store_id, store_quantity, online_quantity, warehouse_quantity) "
            "VALUES (%s, %s, %s, %s, %s)",
            [product_id, store_id, data.get("store_quantity", 0),
             data.get("online_quantity", 0), data.get("warehouse_quantity", 0)]
        )
        db.commit()
    cur.close()
    return get_inventory(product_id)


def deduct_store_inventory(product_id, quantity, store_id=None):
    db = get_db()
    cur = db._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM inventory WHERE product_id = %s", [product_id])
    inv = cur.fetchone()
    if not inv:
        cur.close()
        return {"error": "Product not found in inventory"}
    new_qty = max(0, inv["store_quantity"] - quantity)
    cur.execute("UPDATE inventory SET store_quantity = %s WHERE product_id = %s", [new_qty, product_id])
    db.commit()
    cur.close()
    return {"store_quantity": new_qty}


def get_low_stock_items(threshold=10, store_id=None):
    db = get_db()
    cur = db._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    params = [threshold]
    query = "SELECT p.*, i.store_quantity, i.online_quantity, i.warehouse_quantity FROM products p JOIN inventory i ON i.product_id = p.id WHERE i.store_quantity < %s"
    if store_id:
        query += " AND p.store_id = %s"
        params.append(store_id)
    query += " ORDER BY i.store_quantity ASC"
    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()
    return [dict(r) for r in rows]


# ============================================================
# Sales (PostgreSQL)
# ============================================================

def create_sale(data):
    db = get_db()
    try:
        cur = db._conn.cursor()
        cur.execute(
            "INSERT INTO store_sales (store_id, customer_name, customer_phone, cashier, subtotal, discount, tax, total, payment_method, notes) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
            [data.get("store_id", 1), data.get("customer_name", ""),
             data.get("customer_phone", ""), data.get("cashier", "caisse"),
             float(data.get("subtotal", 0)), float(data.get("discount", 0)),
             float(data.get("tax", 0)), float(data.get("total", 0)),
             data.get("payment_method", "cash"), data.get("notes", "")]
        )
        sale_id = cur.fetchone()[0]
        for item in data.get("items", []):
            cur.execute(
                "INSERT INTO sale_items (sale_id, product_id, product_name, quantity, unit_price, total_price) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                [sale_id, item.get("product_id"), item.get("product_name", ""),
                 int(item.get("quantity", 1)), float(item.get("unit_price", 0)),
                 float(item.get("total_price", 0))]
            )
            deduct_store_inventory(item["product_id"], int(item.get("quantity", 1)))
        db.commit()
        cur.close()
        return {"id": sale_id}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}


def get_store_sales(store_id=None, page=1, per_page=50, **filters):
    db = get_db()
    cur = db._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    params = []
    conditions = []
    query = "SELECT * FROM store_sales"
    if store_id:
        conditions.append("store_id = %s")
        params.append(store_id)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY id DESC"
    if per_page:
        query += " LIMIT %s OFFSET %s"
        params.append(int(per_page))
        params.append((int(page) - 1) * int(per_page))
    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()
    return [dict(r) for r in rows]


def get_store_sale_items(sale_id):
    db = get_db()
    cur = db._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM sale_items WHERE sale_id = %s", [sale_id])
    rows = cur.fetchall()
    cur.close()
    return [dict(r) for r in rows]


def get_store_daily_summary(store_id=None, date=None):
    db = get_db()
    cur = db._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    from datetime import date as dt_date
    today = date or dt_date.today().isoformat()
    params = [today]
    query = "SELECT COUNT(*) as total_sales, COALESCE(SUM(total), 0) as total_revenue FROM store_sales WHERE DATE(created_at) = %s"
    if store_id:
        query += " AND store_id = %s"
        params.append(store_id)
    cur.execute(query, params)
    row = cur.fetchone()
    cur.close()
    return dict(row) if row else None


def create_expense(data):
    db = get_db()
    cur = db._conn.cursor()
    cur.execute(
        "INSERT INTO expenses (store_id, description, amount, category, paid_by, notes) "
        "VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
        [data.get("store_id", 1), data["description"], float(data["amount"]),
         data.get("category", "general"), data.get("paid_by", "caisse"), data.get("notes", "")]
    )
    expense_id = cur.fetchone()[0]
    db.commit()
    cur.close()
    return {"id": expense_id}


def get_expenses(store_id=None, page=1, per_page=50):
    db = get_db()
    cur = db._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    params = []
    conditions = []
    query = "SELECT * FROM expenses"
    if store_id:
        conditions.append("store_id = %s")
        params.append(store_id)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY id DESC"
    if per_page:
        query += " LIMIT %s OFFSET %s"
        params.append(int(per_page))
        params.append((int(page) - 1) * int(per_page))
    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()
    return [dict(r) for r in rows]


# ============================================================
# Purchases (PostgreSQL)
# ============================================================

def create_purchase_with_items(data):
    db = get_db()
    try:
        cur = db._conn.cursor()
        cur.execute(
            "INSERT INTO purchases (store_id, supplier_name, supplier_phone, reference, subtotal, discount, tax, total, notes, status) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
            [data.get("store_id", 1), data.get("supplier_name", ""),
             data.get("supplier_phone", ""), data.get("reference", ""),
             float(data.get("subtotal", 0)), float(data.get("discount", 0)),
             float(data.get("tax", 0)), float(data.get("total", 0)),
             data.get("notes", ""), data.get("status", "pending")]
        )
        purchase_id = cur.fetchone()[0]
        for item in data.get("items", []):
            cur.execute(
                "INSERT INTO purchase_items (purchase_id, product_id, product_name, quantity, unit_price, total_price) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                [purchase_id, item.get("product_id"), item.get("product_name", ""),
                 int(item.get("quantity", 1)), float(item.get("unit_price", 0)),
                 float(item.get("total_price", 0))]
            )
        db.commit()
        cur.close()
        return {"id": purchase_id}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}


def get_purchases(store_id=None, page=1, per_page=50):
    db = get_db()
    cur = db._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    params = []
    conditions = []
    query = "SELECT * FROM purchases"
    if store_id:
        conditions.append("store_id = %s")
        params.append(store_id)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY id DESC"
    if per_page:
        query += " LIMIT %s OFFSET %s"
        params.append(int(per_page))
        params.append((int(page) - 1) * int(per_page))
    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()
    return [dict(r) for r in rows]


def get_purchase_items(purchase_id):
    db = get_db()
    cur = db._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM purchase_items WHERE purchase_id = %s", [purchase_id])
    rows = cur.fetchall()
    cur.close()
    return [dict(r) for r in rows]


def get_store_purchases(store_id=None, page=1, per_page=50):
    return get_purchases(store_id, page, per_page)


def get_purchase_detail(purchase_id):
    db = get_db()
    cur = db._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM purchases WHERE id = %s", [purchase_id])
    purchase = cur.fetchone()
    if not purchase:
        cur.close()
        return None
    purchase = dict(purchase)
    cur.close()
    purchase["items"] = get_purchase_items(purchase_id)
    return purchase


# ============================================================
# Dashboard (PostgreSQL)
# ============================================================

def get_unified_dashboard(store_id=None):
    sid = store_id or 1
    from datetime import date as dt_date
    today = dt_date.today().isoformat()
    summary = get_store_daily_summary(sid, today)
    products = get_products(sid)
    sales = get_store_sales(sid, per_page=10)
    low_stock = get_low_stock_items(store_id=sid)
    online_orders = get_online_orders(sid)
    return {
        "summary": summary,
        "products_count": len(products),
        "recent_sales": sales,
        "low_stock_items": low_stock,
        "online_orders": online_orders
    }


def get_online_orders(store_id=None):
    db = get_db()
    cur = db._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    params = []
    query = "SELECT * FROM orders"
    conditions = []
    if store_id:
        conditions.append("store_id = %s")
        params.append(store_id)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY id DESC LIMIT 20"
    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()
    return [dict(r) for r in rows]
'''

with open('database/psql.py', 'a', encoding='utf-8') as f:
    f.write(new_funcs)

print("Done! All PostgreSQL CRUD functions added.")

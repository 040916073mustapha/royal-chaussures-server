#!/usr/bin/env python3
import sys

with open('database/db.py', 'r', encoding='utf-8') as f:
    content = f.read()

anchor = '''    def get_current_store_id():
        """الحصول على store_id الخاص بالطلب الحالي"""
        return getattr(_local, "store_id", 1)


    # ============================================================
    # Query helpers
    # ============================================================

    def dict_from_row(row):'''

new_functions = '''    # ============================================================
    # Product CRUD (SQLite)
    # ============================================================

    def get_products(store_id=None, page=1, per_page=50, **filters):
        db = get_db()
        query = 'SELECT * FROM products'
        params = []
        conditions = []
        if store_id:
            conditions.append('store_id = ?')
            params.append(store_id)
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
        query += ' ORDER BY id DESC'
        if per_page:
            query += f' LIMIT {int(per_page)} OFFSET {(int(page)-1)*int(per_page)}'
        return dicts_from_rows(db.execute(query, params).fetchall())

    def get_product(product_id):
        db = get_db()
        return dict_from_row(db.execute('SELECT * FROM products WHERE id = ?', [product_id]).fetchone())

    def get_product_by_barcode(barcode, store_id=None):
        db = get_db()
        params = [barcode]
        query = 'SELECT * FROM products WHERE barcode = ?'
        if store_id:
            query += ' AND store_id = ?'
            params.append(store_id)
        return dict_from_row(db.execute(query, params).fetchone())

    def get_product_by_sku(sku, store_id=None):
        db = get_db()
        params = [sku]
        query = 'SELECT * FROM products WHERE sku = ?'
        if store_id:
            query += ' AND store_id = ?'
            params.append(store_id)
        return dict_from_row(db.execute(query, params).fetchone())

    def create_product(data):
        db = get_db()
        cursor = db.execute('INSERT INTO products (store_id, name, sku, barcode, category, price, cost, unit, image_url, description, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', [data.get('store_id', 1), data['name'], data.get('sku', ''), data.get('barcode', ''), data.get('category', ''), float(data.get('price', 0)), float(data.get('cost', 0)), data.get('unit', 'piece'), data.get('image_url', ''), data.get('description', ''), data.get('is_active', True)])
        db.commit()
        return get_product(cursor.lastrowid)

    def update_product(product_id, data):
        db = get_db()
        allowed = ['name','sku','barcode','category','price','cost','unit','image_url','description','is_active']
        updates = []
        params = []
        for field in allowed:
            if field in data:
                updates.append(f'{field} = ?')
                params.append(data[field])
        if not updates:
            return get_product(product_id)
        params.append(product_id)
        db.execute(f'UPDATE products SET ' + ', '.join(updates) + ' WHERE id = ?', params)
        db.commit()
        return get_product(product_id)

    def search_products(query, store_id=None, limit=20):
        db = get_db()
        params = [f'%{query}%', f'%{query}%']
        sql = 'SELECT * FROM products WHERE (name LIKE ? OR sku LIKE ?)'
        if store_id:
            sql += ' AND store_id = ?'
            params.append(store_id)
        sql += ' LIMIT ?'
        params.append(limit)
        return dicts_from_rows(db.execute(sql, params).fetchall())

    # ============================================================
    # Inventory (SQLite)
    # ============================================================

    def get_inventory(product_id=None, store_id=None):
        db = get_db()
        params = []
        query = 'SELECT * FROM inventory'
        conditions = []
        if product_id:
            conditions.append('product_id = ?')
            params.append(product_id)
        if store_id:
            conditions.append('store_id = ?')
            params.append(store_id)
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
        return dicts_from_rows(db.execute(query, params).fetchall())

    def update_inventory(product_id, data):
        db = get_db()
        existing = get_inventory(product_id)
        store_id = data.get('store_id', 1)
        if existing:
            updates = []
            params = []
            for field in ['store_quantity','online_quantity','warehouse_quantity']:
                if field in data:
                    updates.append(f'{field} = ?')
                    params.append(data[field])
            if updates:
                params.append(product_id)
                db.execute(f'UPDATE inventory SET ' + ', '.join(updates) + ' WHERE product_id = ?', params)
                db.commit()
        else:
            db.execute('INSERT INTO inventory (product_id, store_id, store_quantity, online_quantity, warehouse_quantity) VALUES (?, ?, ?, ?, ?)', [product_id, store_id, data.get('store_quantity', 0), data.get('online_quantity', 0), data.get('warehouse_quantity', 0)])
            db.commit()
        return get_inventory(product_id)

    def deduct_store_inventory(product_id, quantity, store_id=None):
        db = get_db()
        inv = get_inventory(product_id)
        if not inv:
            return {'error': 'Product not found in inventory'}
        inv = inv[0]
        new_qty = max(0, inv['store_quantity'] - quantity)
        db.execute('UPDATE inventory SET store_quantity = ? WHERE product_id = ?', [new_qty, product_id])
        db.commit()
        return {'store_quantity': new_qty}

    def get_low_stock_items(threshold=10, store_id=None):
        db = get_db()
        params = [threshold]
        query = 'SELECT p.*, i.store_quantity, i.online_quantity, i.warehouse_quantity FROM products p JOIN inventory i ON i.product_id = p.id WHERE i.store_quantity < ?'
        if store_id:
            query += ' AND p.store_id = ?'
            params.append(store_id)
        query += ' ORDER BY i.store_quantity ASC'
        return dicts_from_rows(db.execute(query, params).fetchall())

    # ============================================================
    # Sales (SQLite)
    # ============================================================

    def create_sale(data):
        db = get_db()
        try:
            cursor = db.execute('INSERT INTO store_sales (store_id, customer_name, customer_phone, cashier, subtotal, discount, tax, total, payment_method, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', [data.get('store_id', 1), data.get('customer_name', ''), data.get('customer_phone', ''), data.get('cashier', 'caisse'), float(data.get('subtotal', 0)), float(data.get('discount', 0)), float(data.get('tax', 0)), float(data.get('total', 0)), data.get('payment_method', 'cash'), data.get('notes', '')])
            sale_id = cursor.lastrowid
            for item in data.get('items', []):
                db.execute('INSERT INTO sale_items (sale_id, product_id, product_name, quantity, unit_price, total_price) VALUES (?, ?, ?, ?, ?, ?)', [sale_id, item.get('product_id'), item.get('product_name', ''), int(item.get('quantity', 1)), float(item.get('unit_price', 0)), float(item.get('total_price', 0))])
                deduct_store_inventory(item['product_id'], int(item.get('quantity', 1)))
            db.commit()
            return {'id': sale_id}
        except Exception as e:
            db.rollback()
            return {'error': str(e)}

    def get_store_sales(store_id=None, page=1, per_page=50, **filters):
        db = get_db()
        params = []
        query = 'SELECT * FROM store_sales'
        conditions = []
        if store_id:
            conditions.append('store_id = ?')
            params.append(store_id)
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
        query += ' ORDER BY id DESC'
        if per_page:
            query += f' LIMIT {int(per_page)} OFFSET {(int(page)-1)*int(per_page)}'
        return dicts_from_rows(db.execute(query, params).fetchall())

    def get_store_sale_items(sale_id):
        db = get_db()
        return dicts_from_rows(db.execute('SELECT * FROM sale_items WHERE sale_id = ?', [sale_id]).fetchall())

    def get_store_daily_summary(store_id=None, date=None):
        db = get_db()
        from datetime import date as dt_date
        today = date or dt_date.today().isoformat()
        params = [today]
        query = 'SELECT COUNT(*) as total_sales, COALESCE(SUM(total), 0) as total_revenue FROM store_sales WHERE DATE(created_at) = ?'
        if store_id:
            query += ' AND store_id = ?'
            params.append(store_id)
        return dict_from_row(db.execute(query, params).fetchone())

    def create_expense(data):
        db = get_db()
        cursor = db.execute('INSERT INTO expenses (store_id, description, amount, category, paid_by, notes) VALUES (?, ?, ?, ?, ?, ?)', [data.get('store_id', 1), data['description'], float(data['amount']), data.get('category', 'general'), data.get('paid_by', 'caisse'), data.get('notes', '')])
        db.commit()
        return {'id': cursor.lastrowid}

    def get_expenses(store_id=None, page=1, per_page=50):
        db = get_db()
        params = []
        query = 'SELECT * FROM expenses'
        conditions = []
        if store_id:
            conditions.append('store_id = ?')
            params.append(store_id)
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
        query += ' ORDER BY id DESC'
        if per_page:
            query += f' LIMIT {int(per_page)} OFFSET {(int(page)-1)*int(per_page)}'
        return dicts_from_rows(db.execute(query, params).fetchall())

    def create_purchase_with_items(data):
        db = get_db()
        try:
            cursor = db.execute('INSERT INTO purchases (store_id, supplier_name, supplier_phone, reference, subtotal, discount, tax, total, notes, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', [data.get('store_id', 1), data.get('supplier_name', ''), data.get('supplier_phone', ''), data.get('reference', ''), float(data.get('subtotal', 0)), float(data.get('discount', 0)), float(data.get('tax', 0)), float(data.get('total', 0)), data.get('notes', ''), data.get('status', 'pending')])
            purchase_id = cursor.lastrowid
            for item in data.get('items', []):
                db.execute('INSERT INTO purchase_items (purchase_id, product_id, product_name, quantity, unit_price, total_price) VALUES (?, ?, ?, ?, ?, ?)', [purchase_id, item.get('product_id'), item.get('product_name', ''), int(item.get('quantity', 1)), float(item.get('unit_price', 0)), float(item.get('total_price', 0))])
            db.commit()
            return {'id': purchase_id}
        except Exception as e:
            db.rollback()
            return {'error': str(e)}

    def get_purchases(store_id=None, page=1, per_page=50):
        db = get_db()
        params = []
        query = 'SELECT * FROM purchases'
        conditions = []
        if store_id:
            conditions.append('store_id = ?')
            params.append(store_id)
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
        query += ' ORDER BY id DESC'
        if per_page:
            query += f' LIMIT {int(per_page)} OFFSET {(int(page)-1)*int(per_page)}'
        return dicts_from_rows(db.execute(query, params).fetchall())

    def get_purchase_items(purchase_id):
        db = get_db()
        return dicts_from_rows(db.execute('SELECT * FROM purchase_items WHERE purchase_id = ?', [purchase_id]).fetchall())

    def get_store_purchases(store_id=None, page=1, per_page=50):
        return get_purchases(store_id, page, per_page)

    def get_purchase_detail(purchase_id):
        db = get_db()
        purchase = dict_from_row(db.execute('SELECT * FROM purchases WHERE id = ?', [purchase_id]).fetchone())
        if not purchase:
            return None
        purchase['items'] = get_purchase_items(purchase_id)
        return purchase

    def get_unified_dashboard(store_id=None):
        db = get_db()
        sid = store_id or 1
        from datetime import date as dt_date
        today = dt_date.today().isoformat()
        summary = get_store_daily_summary(sid, today)
        products = get_products(sid)
        sales = get_store_sales(sid, per_page=10)
        low_stock = get_low_stock_items(store_id=sid)
        online_orders = get_online_orders(sid)
        return {'summary': summary, 'products_count': len(products), 'recent_sales': sales, 'low_stock_items': low_stock, 'online_orders': online_orders}

    def get_online_orders(store_id=None):
        db = get_db()
        params = []
        query = 'SELECT * FROM orders'
        conditions = []
        if store_id:
            conditions.append('store_id = ?')
            params.append(store_id)
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
        query += ' ORDER BY id DESC LIMIT 20'
        return dicts_from_rows(db.execute(query, params).fetchall())


'''

new_content = content.replace(anchor, new_functions + anchor)

with open('database/db.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Done! Functions inserted successfully.")
print(f"File size: {len(new_content)} chars")

import sys
sys.path.insert(0, '.')
with open('routes/store.py', 'r', encoding='utf-8') as f:
    content = f.read()

marker = 'return jsonify({"product": None, "error": str(e)}), 500\n\n\n# ============================================================\n# 🔐 Auth'

new_routes = '''
# ============================================================
# 💰 POS Sales API (Nouvelle vente) — no auth required
# ============================================================

@store_bp.route('/pos/sales', methods=['POST'])
def pos_record_sale():
    """Record a sale from POS without auth requirement"""
    try:
        import os
        _db_path = os.environ.get("STORE_DB_PATH",
                         os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "royal_store.db"))
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body required"}), 400
        if "product_id" not in data or "quantity" not in data:
            return jsonify({"error": "product_id and quantity required"}), 400

        from database.db import create_sale
        result = create_sale(data)
        if "error" in result:
            return jsonify(result), 400
        return jsonify({"sale": result})
    except Exception as e:
        import traceback
        print(f"[POS Sale] Error: {e}\n{traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500


@store_bp.route('/pos/sales', methods=['GET'])
def pos_list_sales():
    """List sales from POS without auth requirement"""
    try:
        import os
        _db_path = os.environ.get("STORE_DB_PATH",
                         os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "royal_store.db"))
        conn = sqlite3.connect(_db_path, timeout=10, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT
                ss.id, ss.receipt_number, ss.sale_date, ss.total, ss.discount as remise,
                ss.total as amount_paid, '' as status, ss.payment_method,
                ss.customer_name, ss.cashier as seller_name, ss.cashier as recorded_by,
                ss.sale_date as created_at, ss.unit_price as cost_price
            FROM store_sales ss
            WHERE ss.store_id = 1
            ORDER BY ss.sale_date DESC
            LIMIT 100 OFFSET 0
        """).fetchall()
        sales = [dict(r) for r in rows]
        conn.close()
        return jsonify({"success": True, "sales": sales})
    except Exception as e:
        import traceback
        print(f"[POS Sales List] Error: {e}\n{traceback.format_exc()}")
        return jsonify({"success": False, "sales": [], "error": str(e)}), 500


# ============================================================
# 🔐 Auth'''

if marker in content:
    content = content.replace(marker, new_routes, 1)
    with open('routes/store.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: Routes added to store.py")
else:
    print("FAIL: marker not found")
    idx = content.find('# ============================================================\n# 🔐 Auth')
    if idx >= 0:
        print(f"Found at {idx}")
        print(content[idx-200:idx+200])
    else:
        # Search more broadly
        auth_idx = content.find('# 🔐 Auth')
        if auth_idx >= 0:
            print(f"Auth section found at {auth_idx}")
            print(content[auth_idx-50:auth_idx+50])

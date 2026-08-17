"""
Additions to database/db.py for Purchase List functionality
"""

# Paste this block in database/db.py — I'll add it via the update script
PURCHASE_LIST_FUNCTIONS = '''
def get_store_purchases(store_id=None, from_date=None, to_date=None, limit=500, offset=0,
                        code=None, fournisseur=None, nom=None, cancelled=None, search=None):
    """جلب المشتريات مع فلترة متقدمة"""
    db = get_db()
    query = """
        SELECT 
            sp.id, sp.supplier as fournisseur, sp.purchase_date as date_achat,
            sp.total as montant_total, sp.notes,
            sp.created_at, sp.recorded_by,
            COALESCE((SELECT COUNT(*) FROM store_purchase_items WHERE purchase_id = sp.id), 0) as nombre_article,
            sp.total as montant_verse,
            0.0 as montant_reste,
            0.0 as tva_pct,
            0.0 as montant_tva,
            sp.total as total_ht
        FROM store_purchases sp
        WHERE 1=1
    """
    params = []
    
    if store_id:
        query += " AND sp.store_id = ?"
        params.append(store_id)
    if from_date:
        query += " AND sp.purchase_date >= ?"
        params.append(f"{from_date} 00:00:00")
    if to_date:
        query += " AND sp.purchase_date <= ?"
        params.append(f"{to_date} 23:59:59")
    if code:
        query += " AND CAST(sp.id AS TEXT) LIKE ?"
        params.append(f"%{code}%")
    if fournisseur:
        query += " AND sp.supplier LIKE ?"
        params.append(f"%{fournisseur}%")
    if nom:
        query += " AND sp.notes LIKE ?"
        params.append(f"%{nom}%")
    if not cancelled:
        query += " AND (sp.status IS NULL OR sp.status != 'cancelled')"
    
    query += " ORDER BY sp.purchase_date DESC, sp.id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    return dicts_from_rows(db.execute(query, params).fetchall())


def get_purchase_detail(purchase_id):
    """جلب تفاصيل فاتورة شراء كاملة مع العناصر"""
    db = get_db()
    purchase = dict_from_row(db.execute("""
        SELECT 
            sp.*,
            COALESCE((SELECT COUNT(*) FROM store_purchase_items WHERE purchase_id = sp.id), 0) as nombre_article
        FROM store_purchases sp WHERE sp.id = ?
    """, [purchase_id]).fetchone())
    
    if purchase:
        purchase["items"] = dicts_from_rows(db.execute("""
            SELECT spi.*, p.name as product_name
            FROM store_purchase_items spi
            LEFT JOIN products p ON p.id = spi.product_id
            WHERE spi.purchase_id = ?
            ORDER BY spi.id ASC
        """, [purchase_id]).fetchall())
    
    return purchase
'''

print(PURCHASE_LIST_FUNCTIONS)

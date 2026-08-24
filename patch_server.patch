*** Begin Patch
--- a/server.py
+++ b/server.py
@@ -1313,6 +1313,14 @@
         import traceback
         logger.error(traceback.format_exc())
         return json_utf8({"error": _safe_str(e)}, 500)
+
+@app.route('/api/store/<int:store_id>')
+def api_store_info(store_id):
+    try:
+        from database.db import get_store
+        store = get_store(store_id)
+        if store:
+            return json_utf8({"id": store["id"], "name": store["name"], "slug": store["slug"]})
+        return json_utf8({"error": "Store not found"}, 404)
+    except Exception as e:
+        return json_utf8({"error": _safe_str(e)}, 500)
 
 @app.route('/api/webhooks/registered', methods=['GET'])
 def api_list_webhooks():
*** End Patch ***
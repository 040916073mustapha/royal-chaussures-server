import sys
sys.path.insert(0, '.')
with open('static/pos/pos.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: recordSale -> use /api/v1/store/pos/sales without auth
old1 = "const r=await fetch(b+'/sales',{method:'POST',headers:this.headers(),body:JSON.stringify(d)})"
new1 = "const r=await fetch('/api/v1/store/pos/sales',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)})"
if old1 in content:
    content = content.replace(old1, new1, 1)
    print("Fix 1: recordSale URL updated")
else:
    print("Fix 1 FAILED")

# Fix 2: loadSalesList -> use /api/v1/store/pos/sales without auth
old2 = "const r=await fetch('/api/v1/store/sales?'+qs.toString(),{headers:API.headers()})"
new2 = "const r=await fetch('/api/v1/store/pos/sales?'+qs.toString(),{headers:{'Content-Type':'application/json'}})"
if old2 in content:
    content = content.replace(old2, new2, 1)
    print("Fix 2: loadSalesList URL updated")
else:
    print("Fix 2 FAILED - checking alternatives")
    idx2 = content.find("/api/v1/store/sales")
    if idx2 >= 0:
        print(f"  Found at {idx2}: {content[idx2:idx2+80]}")

# Fix 3: reprintReceipt -> use /api/v1/store/pos/sales/{id} without auth
old3 = "const r=await fetch('/api/v1/store/sales/'+sale.id,{headers:API.headers()})"
new3 = "const r=await fetch('/api/v1/store/pos/sales/'+sale.id,{headers:{'Content-Type':'application/json'}})"
if old3 in content:
    content = content.replace(old3, new3, 1)
    print("Fix 3: reprintReceipt URL updated")
else:
    print("Fix 3 FAILED - checking alternatives")
    idx3 = content.find("/api/v1/store/sales/'+sale.id")
    if idx3 >= 0:
        print(f"  Found at {idx3}: {content[idx3:idx3+80]}")

with open('static/pos/pos.js', 'w', encoding='utf-8') as f:
    f.write(content)
print("DONE")

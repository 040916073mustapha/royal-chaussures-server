/** Royal POS — JS Engine */
var STATE={token:null,user:null,cart:[],products:[],allProducts:[],categories:new Set(),selectedPayment:'cash',lastSale:null,isOffline:false,pendingSales:JSON.parse(localStorage.getItem('pos_pending')||'[]'),_lastBarcodeTime:0,_barcodeBuffer:''};
var API=(()=>{const b='/api/v1/store';return{headers:()=>({'Content-Type':'application/json','Authorization':'Bearer '+(STATE.token||'')}),async login(u,p){const r=await fetch(b+'/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:u,password:p})});return r.json()},async getProducts(){const r=await fetch(b+'/products',{headers:this.headers()});return r.json()},async searchProducts(q){const r=await fetch(b+'/products/search?q='+encodeURIComponent(q)+'&limit=50',{headers:this.headers()});return r.json()},async getByBarcode(code){const r=await fetch(b+'/products/barcode/'+encodeURIComponent(code),{headers:this.headers()});return r.json()},async recordSale(d){if(STATE.isOffline)return this._saveOffline(d);const r=await fetch(b+'/sales',{method:'POST',headers:this.headers(),body:JSON.stringify(d)});const res=await r.json();if(!r.ok&&res.error&&(res.error.includes('timeout')||r.status>=500))return this._saveOffline(d);return res},async _saveOffline(d){const p=JSON.parse(localStorage.getItem('pos_pending')||'[]');p.push({...d,_offlineId:Date.now(),_createdAt:new Date().toISOString()});localStorage.setItem('pos_pending',JSON.stringify(p));return{sale:{receipt_number:'OFFLINE-'+Date.now(),total:d.total||0},_offline:true}},async getPosProducts(){const r=await fetch('/api/v1/store/pos/products',{headers:this.headers()});return r.json()},async syncPending(){const p=JSON.parse(localStorage.getItem('pos_pending')||'[]');if(!p.length)return;const s=[];for(const x of p){try{const r=await fetch(b+'/sales',{method:'POST',headers:this.headers(),body:JSON.stringify(x)});if(!r.ok)s.push(x)}catch{s.push(x)}}localStorage.setItem('pos_pending',JSON.stringify(s))}}})();

function startClock(){function u(){const n=new Date();const e=document.getElementById('digital-clock');if(e)e.textContent=String(n.getHours()).padStart(2,'0')+':'+String(n.getMinutes()).padStart(2,'0')+':'+String(n.getSeconds()).padStart(2,'0')}u();setInterval(u,1000)}

async function login(){const u=document.getElementById('login-user').value.trim();const p=document.getElementById('login-pass').value.trim();const b=document.getElementById('login-btn');const e=document.getElementById('login-error');if(!u||!p){e.textContent='Veuillez entrer identifiant et mot de passe';e.style.display='block';return}b.disabled=true;b.innerHTML='<span class="spinner"></span> Connexion...';e.style.display='none';const r=await API.login(u,p);if(r.token){STATE.token=r.token;STATE.user=r.user;localStorage.setItem('pos_token',r.token);localStorage.setItem('pos_user',JSON.stringify(r.user));showApp();loadProducts();updateConnectionStatus();startClock()}else{e.textContent=r.error||'Erreur de connexion';e.style.display='block';b.disabled=false;b.innerHTML='<i class="fas fa-sign-in-alt"></i> Connexion'}}

(function(){const t=localStorage.getItem('pos_token');const u=localStorage.getItem('pos_user');if(t&&u){STATE.token=t;STATE.user=JSON.parse(u);showApp();loadProducts();updateConnectionStatus();startClock()}})();

function showApp(){document.getElementById('login-screen').classList.add('hidden');document.getElementById('pos-app').classList.add('active');const n=STATE.user?.display_name||STATE.user?.username||'Gerant';document.getElementById('sidebar-avatar').textContent=n.charAt(0).toUpperCase();switchView('sale')}

function logout(){STATE.token=null;STATE.user=null;STATE.cart=[];localStorage.removeItem('pos_token');localStorage.removeItem('pos_user');document.getElementById('pos-app').classList.remove('active');document.getElementById('login-screen').classList.remove('hidden');document.getElementById('login-user').value='';document.getElementById('login-pass').value='';document.getElementById('login-btn').disabled=false;document.getElementById('login-btn').innerHTML='<i class="fas fa-sign-in-alt"></i> Connexion'}

function switchView(v){document.querySelectorAll('.nav-item').forEach(i=>i.classList.toggle('active',i.dataset.view===v));document.querySelectorAll('.view-container').forEach(c=>c.classList.remove('active'));const t=document.getElementById('view-'+v);if(t)t.classList.add('active');if(v==='sale'){setTimeout(()=>document.getElementById('sale-barcode')?.focus(),100);updateSaleUI();updateSaleDate()}if(v==='purchase'){if(!STATE._purchaseInitialized){updatePurchaseDate();STATE._purchaseInitialized=true}updatePurchaseUI()}if(v==='products')renderProductsTable()}

function updateSaleDate(){const e=document.getElementById('sale-date');if(e){const d=new Date();e.textContent=d.toLocaleDateString('fr-FR')+' '+d.toLocaleTimeString('fr-FR',{hour:'2-digit',minute:'2-digit'})}}

async function loadProducts(){try{const d=await API.getProducts();STATE.allProducts=d.products||[];STATE.categories=new Set();STATE.allProducts.forEach(p=>{if(p.category)STATE.categories.add(p.category)});STATE.products=[...STATE.allProducts]}catch(e){showToast('Erreur chargement: '+e.message,'error')}}

function updateSaleUI(){const total=STATE.cart.reduce((s,i)=>s+(i.price*i.qty),0);const disc=parseFloat(document.getElementById('sale-remise')?.value)||0;const final=Math.max(0,total-disc);const el=document.getElementById('sale-total-display');if(el)el.textContent=final.toLocaleString()+' DA';const table=document.getElementById('sale-cart-table');if(!table)return;if(!STATE.cart.length){table.innerHTML='<tr><td colspan="7"><div class="no-items"><i class="fas fa-shopping-cart"></i>Panier vide &mdash; Scannez un code-barres</div></td></tr>';return}table.innerHTML=STATE.cart.map((item,i)=>{const t=item.price*item.qty;return'<tr>'+
'<td>'+(i+1)+'</td>'+
'<td>'+(item.barcode||'---')+'</td>'+
'<td>'+item.name+'</td>'+
'<td><input type="number" value="'+item.qty+'" min="1" max="'+item.stock+'" style="width:45px;text-align:center;padding:2px;border:1px solid var(--border-color);border-radius:3px;font-family:Inter,sans-serif;" onchange="updateItemQty('+item.id+',this.value)"></td>'+
'<td>'+item.price.toLocaleString()+'</td>'+
'<td>0</td>'+
'<td>'+t.toLocaleString()+'</td>'+
'</tr>'}).join('');updateSaleDate()}

function updateItemQty(id,val){const item=STATE.cart.find(i=>i.id===id);if(!item)return;const q=parseInt(val);if(isNaN(q)||q<1){removeFromCart(id);return}if(q>item.stock){showToast('Max: '+item.stock,'error');item.qty=item.stock}else item.qty=q;updateSaleUI()}

function addBarcodeItem(){const input=document.getElementById('sale-barcode');const code=input.value.trim();input.value='';if(code)lookupBarcode(code)}

function handleBarcode(e){if(e.key==='Enter'){e.preventDefault();addBarcodeItem();return}const now=Date.now();if(now-STATE._lastBarcodeTime>100)STATE._barcodeBuffer='';STATE._barcodeBuffer+=e.key;STATE._lastBarcodeTime=now;if(e.key==='Enter'&&STATE._barcodeBuffer.length>3){document.getElementById('sale-barcode').value=STATE._barcodeBuffer.replace('Enter','').trim();addBarcodeItem();STATE._barcodeBuffer=''}}

async function lookupBarcode(code){try{const d=await API.getByBarcode(code);if(d.product){const p=d.product;addToCart(p.id,p.name,p.store_price||p.online_price||0,p.store_quantity||0,p.barcode||code);showToast(p.name+' — '+((p.store_price||p.online_price||0).toLocaleString())+' DA')}else showToast('Produit introuvable','error')}catch{const f=STATE.allProducts.find(p=>p.barcode===code);if(f){addToCart(f.id,f.name,f.store_price||f.online_price||0,f.store_quantity||0,f.barcode)}else showToast('Code inconnu','error')}}

function addToCart(id,name,price,stock,barcode){if(stock<=0){showToast('Rupture de stock','error');return}const e=STATE.cart.find(i=>i.id===id);if(e){if(e.qty>=stock){showToast('Max: '+stock,'error');return}e.qty++}else STATE.cart.push({id,name,price,qty:1,stock,barcode:barcode||'---'});updateSaleUI()}

function removeFromCart(id){STATE.cart=STATE.cart.filter(i=>i.id!==id);updateSaleUI()}

function clearCart(){if(!STATE.cart.length)return;if(!confirm('Vider le panier ?'))return;STATE.cart=[];updateSaleUI()}

function quitSale(){clearCart();switchView('home')}

function removeSelectedCartItem(){if(!STATE.cart.length)return;if(!confirm('Supprimer la derniere ligne ?'))return;STATE.cart.pop();updateSaleUI()}

function adjustSelectedQty(delta){const id=STATE.cart[STATE.cart.length-1]?.id;if(!id)return;const item=STATE.cart.find(i=>i.id===id);if(!item)return;item.qty+=delta;if(item.qty<=0){removeFromCart(id);return}if(item.qty>item.stock){item.qty=item.stock}updateSaleUI()}

function numpadInput(val){const input=document.getElementById('sale-barcode');if(val==='clear'){input.value='';input.focus();return}if(val==='calc'){showToast('Calculatrice: en developpement','error');return}if(val==='enter'){addBarcodeItem();return}input.value+=val;input.focus()}

function completeSale(){if(!STATE.cart.length){showToast('Panier vide','error');return}openCheckout()}

function openCheckout(){const m=document.getElementById('payment-modal');document.getElementById('payment-form').style.display='block';document.getElementById('payment-success').style.display='none';let total=0;let html='';STATE.cart.forEach(item=>{const t=item.price*item.qty;total+=t;html+='<div class="r-item"><span>'+item.name+' x'+item.qty+'</span><span>'+t.toLocaleString()+' DA</span></div>'});const disc=parseFloat(document.getElementById('sale-remise')?.value)||0;total=Math.max(0,total-disc);document.getElementById('payment-total').textContent=total.toLocaleString()+' DA';document.getElementById('payment-items').innerHTML=html;selectPayment('cash');m.classList.add('active')}

function selectPayment(m){STATE.selectedPayment=m;document.querySelectorAll('.payment-methods button').forEach(b=>b.classList.toggle('active',b.dataset.method===m))}

document.querySelectorAll('.payment-methods button').forEach(b=>{b.onclick=function(){selectPayment(this.dataset.method)}});

async function completeSale(){const m=document.getElementById('payment-modal');document.getElementById('payment-form').style.display='block';document.getElementById('payment-success').style.display='none';let tot=0;let h='';STATE.cart.forEach(i=>{const t=i.price*i.qty;tot+=t;h+='<div class="r-item"><span>'+i.name+' x'+i.qty+'</span><span>'+t.toLocaleString()+' DA</span></div>'});const disc=parseFloat(document.getElementById('sale-remise')?.value)||0;tot=Math.max(0,tot-disc);document.getElementById('payment-total').textContent=tot.toLocaleString()+' DA';document.getElementById('payment-items').innerHTML=h;selectPayment('cash');m.classList.add('active')}

(function(){const originalComplete=completeSale;async function doSale(){try{const results=[];for(const item of STATE.cart){results.push(await API.recordSale({product_id:item.id,quantity:item.qty,unit_price:item.price,payment_method:STATE.selectedPayment,notes:''}))}const total=STATE.cart.reduce((s,i)=>s+(i.price*i.qty),0);const disc=parseFloat(document.getElementById('sale-remise')?.value)||0;const final=Math.max(0,total-disc);const receipt=results[0]?.sale?.receipt_number||'POS-'+Date.now();STATE.lastSale={receipt,total:final,items:[...STATE.cart],payment:STATE.selectedPayment};document.getElementById('payment-form').style.display='none';document.getElementById('payment-success').style.display='block';document.getElementById('success-total').textContent=final.toLocaleString()+' DA';document.getElementById('success-receipt').textContent='Facture no: '+receipt;STATE.cart=[];updateSaleUI()}catch(e){showToast('Erreur: '+e.message,'error')}}document.getElementById('btn-complete-sale').onclick=doSale})();

function resetSale(){document.getElementById('payment-form').style.display='block';document.getElementById('payment-success').style.display='none';document.getElementById('sale-barcode').focus();updateSaleUI()}

function printReceipt(){if(!STATE.lastSale)return;const s=STATE.lastSale;const ih=s.items.map(i=>'<tr><td>'+i.name+'</td><td style="text-align:center;">'+i.qty+'</td><td style="text-align:right;">'+(i.price*i.qty).toLocaleString()+'</td></tr>').join('');const m={cash:'Especes',card:'Carte',bank_transfer:'Virement',check:'Cheque'};const w=window.open('','_blank','width=300,height=600');w.document.write('<!DOCTYPE html><html dir="ltr"><head><meta charset="UTF-8"><title>Facture '+s.receipt+'</title><style>@page{margin:0;size:80mm auto}*{margin:0;padding:0;box-sizing:border-box}body{font-family:"Courier New",monospace;font-size:12px;padding:10px;width:80mm;color:#000}.header{text-align:center;margin-bottom:10px}.header h2{font-size:16px;font-weight:700}hr{border-top:1px dashed #000;margin:8px 0}table{width:100%;border-collapse:collapse}th{text-align:center;font-size:11px;border-bottom:1px solid #000;padding:4px 0}td{padding:3px 0}.total-row{font-weight:700;font-size:14px}.footer{text-align:center;margin-top:10px;font-size:10px}</style></head><body><div class="header"><h2>Royal Chaussures</h2><p>Imama</p><p>+213 659 83 24 26</p><hr><p>Facture: '+s.receipt+'</p><p>Date: '+new Date().toLocaleDateString('fr-FR')+'</p></div><hr><table><thead><tr><th>Produit</th><th>Qte</th><th>Total</th></tr></thead><tbody>'+ih+'</tbody></table><hr><div style="display:flex;justify-content:space-between;"><span>Total</span><span class="total-row">'+s.total.toLocaleString()+' DA</span></div><div style="display:flex;justify-content:space-between;margin:5px 0 0;"><span>Paiement</span><span>'+(m[s.payment]||s.payment)+'</span></div><hr><div class="footer"><p>Merci de votre visite chez Royal Chaussures</p></div><script>window.onload=function(){window.print();window.close()}<\\/script></body></html>');w.document.close()}

function closeModal(id){document.getElementById(id).classList.remove('active')}
document.getElementById('payment-modal')?.addEventListener('click',function(e){if(e.target===this)closeModal('payment-modal')});
document.addEventListener('keydown',function(e){if(e.key==='Escape')closeModal('payment-modal');if(e.key==='F1'){e.preventDefault();completeSale()};if(e.key==='F2'){e.preventDefault();document.getElementById('sale-barcode')?.focus()}});

var ARTICLES_DATA=[];var ARTICLES_SELECTED=null;

async function renderProductsTable(){
    const t=document.getElementById('articles-table-body');
    if(!t)return;
    try{
        const res=await API.getPosProducts();
        ARTICLES_DATA=res.products||[];
        document.getElementById('article-total-badge').textContent=res.total_articles||0;
    }catch(e){
        ARTICLES_DATA=[];
        showToast('Erreur chargement articles','error');
    }
    renderArticleTableRows();
}

function renderArticleTableRows(filteredData){
    const t=document.getElementById('articles-table-body');
    if(!t)return;
    const data=filteredData||ARTICLES_DATA;
    if(!data.length){
        t.innerHTML='<tr><td colspan="11"><div class="no-items"><i class="fas fa-box-open"></i>Aucun article trouve</div></td></tr>';
        document.getElementById('article-sum-qty').textContent='0';
        document.getElementById('article-sum-total').textContent='0';
        return;
    }
    let totalQty=0;
    t.innerHTML=data.map(function(p,i){
        const q=p.total_quantity||p.store_quantity||0;
        totalQty+=q;
        var qcls='qte-ok',qdisp=q;
        if(q<=0){qcls='qte-rupture';qdisp=0}
        else if(q<=5){qcls='qte-low'}
        var ph='<i class="fas fa-camera photo-icon'+(p.image_url?' has-photo':'')+'"></i>';
        var pa=p.cost_price||0;
        var pv=p.store_price||p.online_price||0;
        var pr=p.store_price||0;
        var sa=p.low_stock_threshold||5;
        var rm=p.remise_pct||0;
        var cat=p.category||'---';
        return '<tr onclick="selectArticleRow(this,'+p.id+')" data-id="'+p.id+'">'+
            '<td>'+(i+1)+'</td>'+
            '<td>'+(p.sku||'---')+'</td>'+
            '<td>'+(p.name||'')+'</td>'+
            '<td class="'+qcls+'">'+qdisp+'</td>'+
            '<td>'+ph+'</td>'+
            '<td>'+cat+'</td>'+
            '<td>'+pa.toLocaleString()+'</td>'+
            '<td>'+pv.toLocaleString()+'</td>'+
            '<td>'+pr.toLocaleString()+'</td>'+
            '<td>'+(q<=sa?'<span style="color:#dc2626;font-weight:700;"><i class="fas fa-exclamation-triangle"></i>'+sa+'</span>':sa)+'</td>'+
            '<td>'+(rm>0?rm+'%':'---')+'</td>'+
            '</tr>';
    }).join('');
    document.getElementById('article-sum-qty').textContent=totalQty;
    document.getElementById('article-sum-total').textContent=data.length;
    ARTICLES_SELECTED=null;
    document.getElementById('art-btn-edit').disabled=true;
    document.getElementById('art-btn-del').disabled=true;
    document.getElementById('art-btn-stock').disabled=true;
    document.getElementById('art-btn-print').disabled=true;
    document.getElementById('art-btn-remise').disabled=true;
}

function selectArticleRow(row,id){
    document.querySelectorAll('#articles-table-body tr').forEach(function(r){r.classList.remove('selected')});
    row.classList.add('selected');
    ARTICLES_SELECTED=id;
    document.getElementById('art-btn-edit').disabled=false;
    document.getElementById('art-btn-del').disabled=false;
    document.getElementById('art-btn-stock').disabled=false;
    document.getElementById('art-btn-print').disabled=false;
    document.getElementById('art-btn-remise').disabled=false;
}

function filterArticles(){
    var de=document.getElementById('af-prix-de').value;
    var a=document.getElementById('af-prix-a').value;
    var cb=document.getElementById('af-cb').value.toLowerCase().trim();
    var des=document.getElementById('af-designation').value.toLowerCase().trim();
    var fam=document.getElementById('af-famille').value.toLowerCase().trim();
    var filtered=ARTICLES_DATA.filter(function(p){
        if(de&&(p.store_price||0)<parseFloat(de))return false;
        if(a&&(p.store_price||0)>parseFloat(a))return false;
        if(cb&&!(p.barcode||'').toLowerCase().includes(cb))return false;
        if(des&&!(p.name||'').toLowerCase().includes(des))return false;
        if(fam&&!(p.category||'').toLowerCase().includes(fam))return false;
        return true;
    });
    renderArticleTableRows(filtered);
}

function clearFilterArticles(){
    document.getElementById('af-prix-de').value='';
    document.getElementById('af-prix-a').value='';
    document.getElementById('af-cb').value='';
    document.getElementById('af-designation').value='';
    document.getElementById('af-famille').value='';
    renderArticleTableRows(ARTICLES_DATA);
}

function openArticleModal(){
    showToast('Ajout article - en developpement','error');
}

function editSelectedArticle(){
    if(!ARTICLES_SELECTED){showToast('Selectionnez un article','error');return}
    showToast('Modification article #'+ARTICLES_SELECTED+' - en developpement','error');
}

function deleteSelectedArticle(){
    if(!ARTICLES_SELECTED){showToast('Selectionnez un article','error');return}
    if(!confirm('Supprimer cet article ?'))return;
    showToast('Suppression - en developpement','error');
}

function exportArticles(){
    if(!ARTICLES_DATA.length){showToast('Aucun article a exporter','error');return}
    var csv='Pos,Code,Designation,Qte,Photo,Famille,Prix achat,Prix vente,Px Revendeur,Stock alerte,Remise\n';
    ARTICLES_DATA.forEach(function(p,i){
        csv+=(i+1)+','+(p.sku||'')+','+(p.name||'')+','+(p.total_quantity||0)+',,'+(p.category||'')+','+(p.cost_price||0)+','+(p.store_price||0)+','+(p.store_price||0)+','+(p.low_stock_threshold||5)+','+(p.remise_pct||0)+'\n';
    });
    var blob=new Blob([csv],{type:'text/csv;charset=utf-8;'});
    var link=document.createElement('a');
    link.href=URL.createObjectURL(blob);
    link.download='articles_'+new Date().toISOString().slice(0,10)+'.csv';
    link.click();
    showToast('Exporte: '+ARTICLES_DATA.length+' articles','success');
}

function importArticles(){
    showToast('Import - en developpement','error');
}

function updateConnectionStatus(){const d=document.getElementById('conn-dot');const t=document.getElementById('conn-text');function c(){const o=navigator.onLine;if(d)d.className='dot '+(o?'online':'offline');if(t)t.textContent=o?'Connecte':'Hors ligne';STATE.isOffline=!o}c();window.addEventListener('online',c);window.addEventListener('offline',c)}

(function(){const p=JSON.parse(localStorage.getItem('pos_pending')||'[]');if(p.length)STATE.pendingSales=p})();

function showToast(msg,type){const t=document.getElementById('toast');if(!t)return;t.textContent=msg;t.className='toast show '+(type||'success');t.style.display='block';setTimeout(()=>{t.classList.remove('show');t.style.display='none'},3000)}

// ============================================================
// PURCHASE ENGINE (Nouvel achat)
// ============================================================

function updatePurchaseDate(){const e=document.getElementById('purchase-date');if(e){const d=new Date();e.value=d.toISOString().split('T')[0]}updatePurchaseNumber()}function updatePurchaseNumber(){const e=document.getElementById('purchase-number');if(e){const n=STATE._purchaseCounter||0;e.textContent=String(1000001+n).padStart(9,'0');STATE._purchaseCounter=(STATE._purchaseCounter||0)+1}}
function updatePurchaseUI(){if(!document.getElementById('purchase-cart-table'))return;const table=document.getElementById('purchase-cart-table');if(!STATE.purchaseCart.length){table.innerHTML='<tr><td colspan="8"><div class="no-items"><i class="fas fa-cart-plus"></i>Cliquez sur "Ajouter article" pour commencer</div></td></tr>';updatePurchaseSummary();return}table.innerHTML=STATE.purchaseCart.map((item,i)=>{const t=item.prix_achat*item.quantite;return'<tr>'+
'<td>'+(i+1)+'</td>'+
'<td>'+(item.barcode||'---')+'</td>'+
'<td style="font-weight:500;">'+item.designation+'</td>'+
'<td style="color:var(--accent-blue-dark);font-weight:700;">'+item.prix_vente.toLocaleString()+'</td>'+
'<td><input type="number" value="'+item.quantite+'" min="1" style="width:40px;text-align:center;padding:2px;border:1px solid var(--border-color);border-radius:3px;font-family:Inter,sans-serif;" onchange="updatePurchaseQty('+i+',this.value)"></td>'+
'<td style="color:var(--accent-red);">'+item.prix_achat.toLocaleString()+'</td>'+
'<td>'+t.toLocaleString()+'</td>'+
'<td><button class="btn-del-item" onclick="removePurchaseItem('+i+')"><i class="fas fa-trash-alt"></i></button></td>'+
'</tr>'}).join('');updatePurchaseSummary()}

function updatePurchaseQty(idx,val){const q=parseInt(val);if(isNaN(q)||q<1){STATE.purchaseCart.splice(idx,1)}else{STATE.purchaseCart[idx].quantite=q}updatePurchaseUI()}
function removePurchaseItem(idx){STATE.purchaseCart.splice(idx,1);updatePurchaseUI()}

function updatePurchaseSummary(){let total=0;let qty=0;let last=STATE.purchaseCart[STATE.purchaseCart.length-1];STATE.purchaseCart.forEach(i=>{total+=i.prix_achat*i.quantite;qty+=i.quantite});const td=document.getElementById('purchase-total-display');if(td)td.textContent=total.toLocaleString()+' DA';const s=document.getElementById('purchase-summary-total');if(s)s.textContent=total.toLocaleString()+' DA';const ic=document.getElementById('purchase-item-count');if(ic)ic.textContent=STATE.purchaseCart.length;const tq=document.getElementById('purchase-total-qty');if(tq)tq.textContent=qty;const st=document.getElementById('purchase-status-msg');if(st){if(last){st.innerHTML='<i class="fas fa-check-circle"></i> Article: '+last.designation+' quantite: '+last.quantite+' total: '+total.toLocaleString()+' DA'}else{st.innerHTML='<i class="fas fa-info-circle"></i> Pret a saisir'}}}

function openArticleModal(){document.getElementById('art-barcode').value='';document.getElementById('art-designation').value='';document.getElementById('art-famille').value='';document.getElementById('art-qty').value='1';document.getElementById('art-remise').value='0';document.getElementById('art-stock-alert').value='5';document.getElementById('art-prix-achat').value='';document.getElementById('art-prix-vente').value='';document.getElementById('art-marge-pct').textContent='0%';document.getElementById('art-marge-mt').textContent='0 DA';document.getElementById('secondary-barcodes').innerHTML='<div class="sb-row"><input type="text" class="input-lg" placeholder="Code barre supplementaire..."><button class="btn-add-sb" onclick="addSecondaryBarcode()" title="Ajouter"><i class="fas fa-plus"></i></button></div>';const pp=document.getElementById('art-photo-placeholder');if(pp)pp.innerHTML='<i class="fas fa-camera"></i><span>Photo produit</span><span class="photo-hint">Cliquez pour ajouter</span>';document.getElementById('article-modal').classList.add('active');setTimeout(()=>document.getElementById('art-designation')?.focus(),200)}

async function generateBarcode(){const btn=document.querySelector('.btn-gen');btn.disabled=true;btn.innerHTML='<span class=\"spinner\"></span>';try{const r=await API.generateBarcode();if(r.barcode){document.getElementById('art-barcode').value=r.barcode;showToast('Code barre genere: '+r.barcode)}}catch{showToast('Erreur generation','error')}finally{btn.disabled=false;btn.innerHTML='<i class=\"fas fa-qrcode\"></i> Generer'}}

function calcMarge(){const pa=parseFloat(document.getElementById('art-prix-achat').value)||0;const pv=parseFloat(document.getElementById('art-prix-vente').value)||0;const marge=Math.max(0,pv-pa);const pct=pa>0?((marge/pa)*100).toFixed(1):0;document.getElementById('art-marge-pct').textContent=pct+'%';document.getElementById('art-marge-mt').textContent=marge.toLocaleString()+' DA'}

function validateArticle(){const designation=document.getElementById('art-designation').value.trim();const qty=parseInt(document.getElementById('art-qty').value)||1;const prixAchat=parseFloat(document.getElementById('art-prix-achat').value)||0;const prixVente=parseFloat(document.getElementById('art-prix-vente').value)||0;const barcode=document.getElementById('art-barcode').value.trim();const famille=document.getElementById('art-famille')?.value||'';const remise=parseFloat(document.getElementById('art-remise')?.value)||0;const stockAlert=parseInt(document.getElementById('art-stock-alert')?.value)||5;if(!designation){showToast('Veuillez entrer la designation','error');document.getElementById('art-designation').focus();return}if(prixAchat<=0){showToast('Veuillez entrer le prix achat','error');document.getElementById('art-prix-achat').focus();return}if(prixVente<=0){showToast('Veuillez entrer le prix vente','error');document.getElementById('art-prix-vente').focus();return}STATE.purchaseCart.push({designation,quantite:qty,prix_achat:prixAchat,prix_vente:prixVente,barcode,famille,remise,stock_alert:stockAlert});closeModal('article-modal');updatePurchaseUI();showToast(designation+' ajoute(e) a l\'achat')}

async function fillDemoData(){try{showToast('Generation des donnees de test...');const r=await API.getDemoData();if(r.articles&&r.articles.length){r.articles.forEach(a=>{STATE.purchaseCart.push({designation:a.designation,quantite:1,prix_achat:a.prix_achat,prix_vente:a.prix_vente,barcode:a.barcode,famille:'chaussures',remise:0,stock_alert:5})});updatePurchaseUI();showToast(r.articles.length+' articles de test ajoutes!','success')}}catch(e){showToast('Erreur: '+e.message,'error')}}

async function validatePurchase(){if(!STATE.purchaseCart.length){showToast('Ajoutez au moins un article','error');return}if(!confirm('Valider l\'achat de '+STATE.purchaseCart.length+' article(s) ?'))return;const btn=document.getElementById('btn-validate-purchase');btn.disabled=true;btn.innerHTML='<span class=\"spinner\"></span> Validation...';try{const supplier=document.getElementById('purchase-supplier')?.value||'divers';const dateInput=document.getElementById('purchase-date')?.value||'';const payload={supplier,purchase_date:dateInput,items:STATE.purchaseCart.map((item,i)=>({...item,pos:i+1}))};const r=await API.recordPurchase(payload);if(r.purchase){showToast('Achat valide! Total: '+r.purchase.total.toLocaleString()+' DA','success');STATE.purchaseCart=[];STATE._purchaseInitialized=false;updatePurchaseUI();updatePurchaseDate()}else if(r.error){showToast('Erreur: '+r.error,'error')}}catch(e){showToast('Erreur: '+e.message,'error')}finally{btn.disabled=false;btn.innerHTML='<i class=\"fas fa-check-circle\"></i> Valider l\'achat <span class=\"shortcut\">[F1]</span>'}}

function clearPurchaseCart(){if(!STATE.purchaseCart.length)return;if(!confirm('Vider tous les articles ?'))return;STATE.purchaseCart=[];updatePurchaseUI()}

function addSecondaryBarcode(){const container=document.getElementById('secondary-barcodes');const row=document.createElement('div');row.className='sb-row';row.innerHTML='<input type="text" class="input-lg" placeholder="Code barre supplementaire..."><button class="btn-add-sb" onclick="this.parentElement.remove()" title="Supprimer" style="background:#e74c3c"><i class="fas fa-times"></i></button>';container.appendChild(row)}function previewArticlePhoto(event){const file=event.target.files[0];if(!file)return;const reader=new FileReader();reader.onload=function(e){const p=document.getElementById('art-photo-placeholder');if(p)p.innerHTML='<img src="'+e.target.result+'" class="photo-preview" style="max-height:180px">'};reader.readAsDataURL(file)}
// ============================================================
// PURCHASE LIST ENGINE (Liste des achats)
// ============================================================

async function loadPurchaseList(){try{const d=document.getElementById('pl-filter-date-from'),dd=document.getElementById('pl-filter-date-to'),code=document.getElementById('pl-filter-code'),art=document.getElementById('pl-filter-article'),nom=document.getElementById('pl-filter-nom'),four=document.getElementById('pl-filter-fournisseur'),can=document.getElementById('pl-filter-cancelled');const qs=new URLSearchParams();if(d&&d.value)qs.set('date_from',d.value);if(dd&&dd.value)qs.set('date_to',dd.value);if(code&&code.value)qs.set('code',code.value);if(art&&art.value)qs.set('article_code',art.value);if(nom&&nom.value)qs.set('nom',nom.value);if(four&&four.value)qs.set('fournisseur',four.value);if(can&&can.checked)qs.set('cancelled','1');const q=document.getElementById('pl-quick-search');if(q&&q.value)qs.set('q',q.value);const r=await fetch('/api/v1/store/purchases/list?'+qs.toString(),{headers:API.headers()});const data=await r.json();renderPurchaseTable(data.purchases||[])}catch(e){showToast('Erreur chargement: '+e.message,'error')}}

function renderPurchaseTable(purchases){const t=document.getElementById('purchase-list-table-body');if(!t)return;const c=document.getElementById('pl-total-count');if(c)c.textContent=purchases.length;if(!purchases.length){t.innerHTML='<tr><td colspan="12"><div class="no-items"><i class="fas fa-file-invoice"></i>Aucun achat trouve</div></td></tr>';updatePurchaseSummary([]);return}let sumTotal=0,sumPaid=0,sumTva=0;t.innerHTML=purchases.map((p,i)=>{const mt=p.montant_total||0;const mv=p.montant_verse||0;const mr=p.montant_reste||0;const tva=p.montant_tva||0;const ht=p.total_ht||0;const na=p.nombre_article||0;sumTotal+=mt;sumPaid+=mv;sumTva+=tva;const dt=p.date_achat||p.created_at||'';const dtr=dt?dt.split(' ')[0]||dt:'---';return '<tr onclick="selectPurchaseRow('+i+')" id="pl-row-'+i+'" style="cursor:pointer">'+'<td>'+(i+1)+'</td>'+'<td><i class="fas fa-check-circle" style="color:#27ae60"></i></td>'+'<td style="font-weight:600">'+(p.id||'---')+'</td>'+'<td>'+(p.supplier||'---')+'</td>'+'<td>'+dtr+'</td>'+'<td style="text-align:center">'+na+'</td>'+'<td style="font-weight:700">'+mt.toLocaleString()+'</td>'+'<td>'+mv.toLocaleString()+'</td>'+'<td>'+(mr||0).toLocaleString()+'</td>'+'<td>'+(p.tva_pct||0)+'%</td>'+'<td>'+tva.toLocaleString()+'</td>'+'<td>'+ht.toLocaleString()+'</td>'+'</tr>'}).join('');updatePurchaseSummary({total:sumTotal,paid:sumPaid,tva:sumTva,ht:sumTotal});STATE._purchaseListData=purchases}

function updatePurchaseSummary(data){const t=document.getElementById('pl-sum-total');if(t)t.textContent=(data.total||0).toLocaleString()+' DA';const p=document.getElementById('pl-sum-paid');if(p)p.textContent=(data.paid||0).toLocaleString()+' DA';const b=document.getElementById('pl-sum-balance');if(b)b.textContent=Math.max(0,(data.total||0)-(data.paid||0)).toLocaleString()+' DA';const tv=document.getElementById('pl-sum-tva');if(tv)tv.textContent=(data.tva||0).toLocaleString()+' DA';const h=document.getElementById('pl-sum-ht');if(h)h.textContent=(data.ht||0).toLocaleString()+' DA'}

function selectPurchaseRow(idx){const rows=document.querySelectorAll('#purchase-list-table-body tr');rows.forEach(r=>r.classList.remove('selected'));const row=document.getElementById('pl-row-'+idx);if(row)row.classList.add('selected');STATE._selectedPurchaseIndex=idx;document.getElementById('pl-btn-edit').disabled=false;document.getElementById('pl-btn-print').disabled=false;document.getElementById('pl-btn-delete').disabled=false}

function resetPurchaseFilter(){document.getElementById('pl-filter-date-from').value='';document.getElementById('pl-filter-date-to').value='';document.getElementById('pl-filter-code').value='';document.getElementById('pl-filter-article').value='';document.getElementById('pl-filter-nom').value='';document.getElementById('pl-filter-fournisseur').value='';document.getElementById('pl-filter-cancelled').checked=false;document.getElementById('pl-quick-search').value='';loadPurchaseList()}

async function reprintPurchase(){const idx=STATE._selectedPurchaseIndex;if(idx===undefined||!STATE._purchaseListData||!STATE._purchaseListData[idx])return;const p=STATE._purchaseListData[idx];if(!p||!p.id)return;try{const r=await fetch('/api/v1/store/purchases/'+p.id+'/detail',{headers:API.headers()});const data=await r.json();if(!data||data.error){showToast('Erreur: '+(data.error||'Achat introuvable'),'error');return}const items=data.items||[];const ih=items.map(i=>'<tr><td>'+(i.product_name||i.designation||'Article')+'</td><td style="text-align:center;">'+(i.quantite||1)+'</td><td style="text-align:right;">'+(i.prix_achat||0).toLocaleString()+'</td><td style="text-align:right;">'+(i.prix_total||0).toLocaleString()+'</td></tr>').join('');const w=window.open('','_blank','width=350,height=600');w.document.write('<!DOCTYPE html><html dir="ltr"><head><meta charset="UTF-8"><title>Bon achat '+(p.id||'')+'</title><style>@page{margin:0;size:80mm auto}*{margin:0;padding:0;box-sizing:border-box}body{font-family:"Courier New",monospace;font-size:12px;padding:10px;width:80mm;color:#000}.header{text-align:center;margin-bottom:10px}.header h2{font-size:16px;font-weight:700}hr{border-top:1px dashed #000;margin:8px 0}table{width:100%;border-collapse:collapse}th{border-bottom:1px solid #000;padding:4px 0;font-size:11px;text-align:center}td{padding:3px 0}.total-row{font-weight:700;font-size:14px}.footer{text-align:center;margin-top:10px;font-size:10px}</style></head><body><div class="header"><h2>Royal Chaussures</h2><p>Bon d\'achat N°: '+(p.id||'')+'</p><p>Date: '+(p.date_achat||'')+'</p><p>Fournisseur: '+(p.supplier||'divers')+'</p></div><hr><table><thead><tr><th>Article</th><th>Qte</th><th>P.U</th><th>Total</th></tr></thead><tbody>'+ih+'</tbody></table><hr><div style="display:flex;justify-content:space-between;"><span>Total achat</span><span class="total-row">'+(p.montant_total||0).toLocaleString()+' DA</span></div><hr><div class="footer"><p>Royal Chaussures</p></div><script>window.onload=function(){window.print();window.close()}<\/script></body></html>');w.document.close()}catch(e){showToast('Erreur: '+e.message,'error')}}

function exportPurchaseList(){const purchases=STATE._purchaseListData||[];if(!purchases.length){showToast('Aucune donnee a exporter','error');return}let csv='Code,Fournisseur,Date achat,Nombre article,Montant Total,Montant verse,Montant reste,TVA %,Montant TVA,Total H.T\n';purchases.forEach(p=>{const n=p.nombre_article||0;csv+=(p.id||'')+','+(p.supplier||'')+','+(p.date_achat||'')+','+n+','+(p.montant_total||0)+','+(p.montant_verse||0)+','+(p.montant_reste||0)+','+(p.tva_pct||0)+','+(p.montant_tva||0)+','+(p.total_ht||0)+'\n'});const blob=new Blob([csv],{type:'text/csv;charset=utf-8;'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='achats_'+new Date().toISOString().split('T')[0]+'.csv';a.click();URL.revokeObjectURL(url);showToast('Exporte avec succes!','success')}

// Override switchView to load purchase list
(function(){const orig=switchView;switchView=function(v){orig(v);if(v==='purchases-list')loadPurchaseList()}})();

console.log('Royal POS Engine Ready');
console.log('Purchase Engine Ready');


// ============================================================
// SALES LIST ENGINE (Liste des ventes)
// ============================================================

async function loadSalesList(){try{const d=document.getElementById('sl-filter-date-from'),dd=document.getElementById('sl-filter-date-to'),code=document.getElementById('sl-filter-code'),art=document.getElementById('sl-filter-article'),client=document.getElementById('sl-filter-client'),vendeur=document.getElementById('sl-filter-vendeur'),can=document.getElementById('sl-filter-cancelled'),cred=document.getElementById('sl-filter-credit');const qs=new URLSearchParams();if(d&&d.value)qs.set('date_from',d.value);if(dd&&dd.value)qs.set('date_to',dd.value);if(code&&code.value)qs.set('code',code.value);if(art&&art.value)qs.set('article_code',art.value);if(client&&client.value)qs.set('client',client.value);if(vendeur&&vendeur.value)qs.set('vendeur',vendeur.value);if(can&&can.checked)qs.set('cancelled','1');if(cred&&cred.checked)qs.set('credit','1');const q=document.getElementById('sl-quick-search');if(q&&q.value)qs.set('q',q.value);const r=await fetch('/api/v1/store/sales?'+qs.toString(),{headers:API.headers()});const data=await r.json();renderSalesTable(data.sales||[]);}catch(e){showToast('Erreur chargement: '+e.message,'error')}}

function renderSalesTable(sales){const t=document.getElementById('sales-list-table-body');if(!t)return;const c=document.getElementById('sl-total-count');if(c)c.textContent=sales.length;if(!sales.length){t.innerHTML='<tr><td colspan="13"><div class="no-items"><i class="fas fa-shopping-cart"></i>Aucune vente trouvee</div></td></tr>';updateSalesSummary([]);return}let sumTotal=0,sumPaid=0,sumCost=0;t.innerHTML=sales.map((s,i)=>{const total=s.total||0;const paid=s.amount_paid||s.amount_received||0;const solde=total-paid;const remise=s.discount||s.remise||0;const cost=s.cost_price||s.cout_achat||0;sumTotal+=total;sumPaid+=paid;sumCost+=cost;const etat=s.status||'completed';const badge={'completed':'Validee','cancelled':'Annulee','credit':'Credit'}[etat]||etat;const bclass=(etat==='cancelled'?'cancelled':etat==='credit'?'credit':'completed');const dt=s.created_at||s.date_vente||s.sale_date||'';const dtr=saleDateFmt(dt);return '<tr onclick="selectSaleRow('+i+')" id="sl-row-'+i+'" style="cursor:pointer">'+'<td>'+(i+1)+'</td>'+'<td><span class="state-badge '+bclass+'">'+badge+'</span></td>'+'<td style="font-weight:600">'+(s.receipt_number||s.code||'---')+'</td>'+'<td>'+(s.customer_name||s.client||'Passager')+'</td>'+'<td>'+(s.seller_name||s.vendeur||'---')+'</td>'+'<td>'+dtr+'</td>'+'<td style="font-weight:700">'+total.toLocaleString()+'</td>'+'<td>'+paid.toLocaleString()+'</td>'+'<td style="color:'+(solde>0?'#e74c3c':'#27ae60')+';font-weight:600">'+Math.max(0,solde).toLocaleString()+'</td>'+'<td>'+remise.toLocaleString()+'</td>'+'<td>'+dtr+'</td>'+'<td>'+(s.recorded_by||s.par||'---')+'</td>'+'<td>'+cost.toLocaleString()+'</td>'+'</tr>'}).join('');updateSalesSummary({total:sumTotal,paid:sumPaid,cost:sumCost,remise:sales.reduce((a,s)=>a+(s.discount||s.remise||0),0)});STATE._salesData=sales}

function updateSalesSummary(data){const r=document.getElementById('sl-sum-remise');if(r)r.textContent=(data.remise||0).toLocaleString()+' DA';const t=document.getElementById('sl-sum-total');if(t)t.textContent=(data.total||0).toLocaleString()+' DA';const p=document.getElementById('sl-sum-paid');if(p)p.textContent=(data.paid||0).toLocaleString()+' DA';const b=document.getElementById('sl-sum-balance');if(b)b.textContent=Math.max(0,(data.total||0)-(data.paid||0)).toLocaleString()+' DA';const c=document.getElementById('sl-sum-cost');if(c)c.textContent=(data.cost||0).toLocaleString()+' DA'}

function saleDateFmt(dt){if(!dt)return '---';try{const d=new Date(dt);if(isNaN(d.getTime()))return dt;return d.toLocaleDateString('fr-FR')+' '+d.toLocaleTimeString('fr-FR',{hour:'2-digit',minute:'2-digit'})}catch{return dt}}

function selectSaleRow(idx){const rows=document.querySelectorAll('#sales-list-table-body tr');rows.forEach(r=>r.classList.remove('selected'));const row=document.getElementById('sl-row-'+idx);if(row)row.classList.add('selected');STATE._selectedSaleIndex=idx;document.getElementById('sl-btn-edit').disabled=false;document.getElementById('sl-btn-print').disabled=false;document.getElementById('sl-btn-delete').disabled=false}

function resetSalesFilter(){document.getElementById('sl-filter-date-from').value='';document.getElementById('sl-filter-date-to').value='';document.getElementById('sl-filter-code').value='';document.getElementById('sl-filter-article').value='';document.getElementById('sl-filter-client').value='';document.getElementById('sl-filter-vendeur').value='';document.getElementById('sl-filter-cancelled').checked=false;document.getElementById('sl-filter-credit').checked=false;document.getElementById('sl-quick-search').value='';loadSalesList()}

async function reprintReceipt(){const idx=STATE._selectedSaleIndex;if(idx===undefined||!STATE._salesData||!STATE._salesData[idx])return;const sale=STATE._salesData[idx];if(!sale)return;try{const r=await fetch('/api/v1/store/sales/'+sale.id,{headers:API.headers()});const data=await r.json();const s=data.sale||sale;const items = data.items || [];const ih=items.map(i=>'<tr><td>'+(i.product_name||i.designation||'Article')+'</td><td style="text-align:center;">'+(i.quantity||1)+'</td><td style="text-align:right;">'+((i.unit_price||0)*(i.quantity||1)).toLocaleString()+'</td></tr>').join('');const m={cash:'Especes',card:'Carte',bank_transfer:'Virement',check:'Cheque'};const w=window.open('','_blank','width=300,height=600');w.document.write('<!DOCTYPE html><html dir="ltr"><head><meta charset="UTF-8"><title>Facture '+(s.receipt_number||'')+'</title><style>@page{margin:0;size:80mm auto}*{margin:0;padding:0;box-sizing:border-box}body{font-family:"Courier New",monospace;font-size:12px;padding:10px;width:80mm;color:#000}.header{text-align:center;margin-bottom:10px}.header h2{font-size:16px;font-weight:700}hr{border-top:1px dashed #000;margin:8px 0}table{width:100%;border-collapse:collapse}th{text-align:center;font-size:11px;border-bottom:1px solid #000;padding:4px 0}td{padding:3px 0}.total-row{font-weight:700;font-size:14px}.footer{text-align:center;margin-top:10px;font-size:10px}</style></head><body><div class="header"><h2>Royal Chaussures</h2><p>Imama</p><p>+213 659 83 24 26</p><hr><p>Facture: '+(s.receipt_number||'')+'</p><p>Date: '+saleDateFmt(s.created_at)+'</p></div><hr><table><thead><tr><th>Produit</th><th>Qte</th><th>Total</th></tr></thead><tbody>'+ih+'</tbody></table><hr><div style="display:flex;justify-content:space-between;"><span>Total</span><span class="total-row">'+(s.total||0).toLocaleString()+' DA</span></div><div style="display:flex;justify-content:space-between;margin:5px 0 0;"><span>Paiement</span><span>'+(m[s.payment_method]||s.payment_method||'Especes')+'</span></div><hr><div class="footer"><p>Merci de votre visite chez Royal Chaussures</p></div><script>window.onload=function(){window.print();window.close()}<\/script></body></html>');w.document.close()}catch(e){showToast('Erreur: '+e.message,'error')}}

function exportSalesList(){const sales=STATE._salesData||[];if(!sales.length){showToast('Aucune donnee a exporter','error');return}let csv='Etat,Code,Client,Vendeur,Date vente,Montant total,Somme verse,Solde,Total remise,Cree le,Par,Cout achat\n';sales.forEach(s=>{const total=s.total||0;const paid=s.amount_paid||0;const solde=total-paid;const etat=s.status||'completed';csv+=etat+','+(s.receipt_number||'')+','+(s.customer_name||'Passager')+','+(s.seller_name||'')+','+(s.created_at||'')+','+total+','+paid+','+solde+','+(s.discount||0)+','+(s.created_at||'')+','+(s.recorded_by||'')+','+(s.cost_price||0)+'\n'});const blob=new Blob([csv],{type:'text/csv;charset=utf-8;'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='ventes_'+new Date().toISOString().split('T')[0]+'.csv';a.click();URL.revokeObjectURL(url);showToast('Exporte avec succes!','success')}

// Auto-init: load sales when switching to sales-list view
if(!window._slAutoInit){window._slAutoInit=true;const orig=switchView;switchView=function(v){orig(v);if(v==='sales-list')loadSalesList()}}

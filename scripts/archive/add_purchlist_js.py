with open('C:/Users/Micro-Tech/.openclaw/workspace/static/pos/pos.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Find where to insert — before the final console.log
old_end = "console.log('Royal POS Engine Ready');\nconsole.log('Purchase Engine Ready');"

new_section = """
// ============================================================
// PURCHASE LIST ENGINE (Liste des achats)
// ============================================================

async function loadPurchaseList(){try{const d=document.getElementById('pl-filter-date-from'),dd=document.getElementById('pl-filter-date-to'),code=document.getElementById('pl-filter-code'),art=document.getElementById('pl-filter-article'),nom=document.getElementById('pl-filter-nom'),four=document.getElementById('pl-filter-fournisseur'),can=document.getElementById('pl-filter-cancelled');const qs=new URLSearchParams();if(d&&d.value)qs.set('date_from',d.value);if(dd&&dd.value)qs.set('date_to',dd.value);if(code&&code.value)qs.set('code',code.value);if(art&&art.value)qs.set('article_code',art.value);if(nom&&nom.value)qs.set('nom',nom.value);if(four&&four.value)qs.set('fournisseur',four.value);if(can&&can.checked)qs.set('cancelled','1');const q=document.getElementById('pl-quick-search');if(q&&q.value)qs.set('q',q.value);const r=await fetch('/api/v1/store/purchases/list?'+qs.toString(),{headers:API.headers()});const data=await r.json();renderPurchaseTable(data.purchases||[])}catch(e){showToast('Erreur chargement: '+e.message,'error')}}

function renderPurchaseTable(purchases){const t=document.getElementById('purchase-list-table-body');if(!t)return;const c=document.getElementById('pl-total-count');if(c)c.textContent=purchases.length;if(!purchases.length){t.innerHTML='<tr><td colspan="12"><div class="no-items"><i class="fas fa-file-invoice"></i>Aucun achat trouve</div></td></tr>';updatePurchaseSummary([]);return}let sumTotal=0,sumPaid=0,sumTva=0;t.innerHTML=purchases.map((p,i)=>{const mt=p.montant_total||0;const mv=p.montant_verse||0;const mr=p.montant_reste||0;const tva=p.montant_tva||0;const ht=p.total_ht||0;const na=p.nombre_article||0;sumTotal+=mt;sumPaid+=mv;sumTva+=tva;const dt=p.date_achat||p.created_at||'';const dtr=dt?dt.split(' ')[0]||dt:'---';return '<tr onclick="selectPurchaseRow('+i+')" id="pl-row-'+i+'" style="cursor:pointer">'+'<td>'+(i+1)+'</td>'+'<td><i class="fas fa-check-circle" style="color:#27ae60"></i></td>'+'<td style="font-weight:600">'+(p.id||'---')+'</td>'+'<td>'+(p.supplier||'---')+'</td>'+'<td>'+dtr+'</td>'+'<td style="text-align:center">'+na+'</td>'+'<td style="font-weight:700">'+mt.toLocaleString()+'</td>'+'<td>'+mv.toLocaleString()+'</td>'+'<td>'+(mr||0).toLocaleString()+'</td>'+'<td>'+(p.tva_pct||0)+'%</td>'+'<td>'+tva.toLocaleString()+'</td>'+'<td>'+ht.toLocaleString()+'</td>'+'</tr>'}).join('');updatePurchaseSummary({total:sumTotal,paid:sumPaid,tva:sumTva,ht:sumTotal});STATE._purchaseListData=purchases}

function updatePurchaseSummary(data){const t=document.getElementById('pl-sum-total');if(t)t.textContent=(data.total||0).toLocaleString()+' DA';const p=document.getElementById('pl-sum-paid');if(p)p.textContent=(data.paid||0).toLocaleString()+' DA';const b=document.getElementById('pl-sum-balance');if(b)b.textContent=Math.max(0,(data.total||0)-(data.paid||0)).toLocaleString()+' DA';const tv=document.getElementById('pl-sum-tva');if(tv)tv.textContent=(data.tva||0).toLocaleString()+' DA';const h=document.getElementById('pl-sum-ht');if(h)h.textContent=(data.ht||0).toLocaleString()+' DA'}

function selectPurchaseRow(idx){const rows=document.querySelectorAll('#purchase-list-table-body tr');rows.forEach(r=>r.classList.remove('selected'));const row=document.getElementById('pl-row-'+idx);if(row)row.classList.add('selected');STATE._selectedPurchaseIndex=idx;document.getElementById('pl-btn-edit').disabled=false;document.getElementById('pl-btn-print').disabled=false;document.getElementById('pl-btn-delete').disabled=false}

function resetPurchaseFilter(){document.getElementById('pl-filter-date-from').value='';document.getElementById('pl-filter-date-to').value='';document.getElementById('pl-filter-code').value='';document.getElementById('pl-filter-article').value='';document.getElementById('pl-filter-nom').value='';document.getElementById('pl-filter-fournisseur').value='';document.getElementById('pl-filter-cancelled').checked=false;document.getElementById('pl-quick-search').value='';loadPurchaseList()}

async function reprintPurchase(){const idx=STATE._selectedPurchaseIndex;if(idx===undefined||!STATE._purchaseListData||!STATE._purchaseListData[idx])return;const p=STATE._purchaseListData[idx];if(!p||!p.id)return;try{const r=await fetch('/api/v1/store/purchases/'+p.id+'/detail',{headers:API.headers()});const data=await r.json();if(!data||data.error){showToast('Erreur: '+(data.error||'Achat introuvable'),'error');return}const items=data.items||[];const ih=items.map(i=>'<tr><td>'+(i.product_name||i.designation||'Article')+'</td><td style=\"text-align:center;\">'+(i.quantite||1)+'</td><td style=\"text-align:right;\">'+(i.prix_achat||0).toLocaleString()+'</td><td style=\"text-align:right;\">'+(i.prix_total||0).toLocaleString()+'</td></tr>').join('');const w=window.open('','_blank','width=350,height=600');w.document.write('<!DOCTYPE html><html dir=\"ltr\"><head><meta charset=\"UTF-8\"><title>Bon achat '+(p.id||'')+'</title><style>@page{margin:0;size:80mm auto}*{margin:0;padding:0;box-sizing:border-box}body{font-family:\"Courier New\",monospace;font-size:12px;padding:10px;width:80mm;color:#000}.header{text-align:center;margin-bottom:10px}.header h2{font-size:16px;font-weight:700}hr{border-top:1px dashed #000;margin:8px 0}table{width:100%;border-collapse:collapse}th{border-bottom:1px solid #000;padding:4px 0;font-size:11px;text-align:center}td{padding:3px 0}.total-row{font-weight:700;font-size:14px}.footer{text-align:center;margin-top:10px;font-size:10px}</style></head><body><div class=\"header\"><h2>Royal Chaussures</h2><p>Bon d\\'achat N°: '+(p.id||'')+'</p><p>Date: '+(p.date_achat||'')+'</p><p>Fournisseur: '+(p.supplier||'divers')+'</p></div><hr><table><thead><tr><th>Article</th><th>Qte</th><th>P.U</th><th>Total</th></tr></thead><tbody>'+ih+'</tbody></table><hr><div style=\"display:flex;justify-content:space-between;\"><span>Total achat</span><span class=\"total-row\">'+(p.montant_total||0).toLocaleString()+' DA</span></div><hr><div class=\"footer\"><p>Royal Chaussures</p></div><script>window.onload=function(){window.print();window.close()}<\\/script></body></html>');w.document.close()}catch(e){showToast('Erreur: '+e.message,'error')}}

function exportPurchaseList(){const purchases=STATE._purchaseListData||[];if(!purchases.length){showToast('Aucune donnee a exporter','error');return}let csv='Code,Fournisseur,Date achat,Nombre article,Montant Total,Montant verse,Montant reste,TVA %,Montant TVA,Total H.T\\n';purchases.forEach(p=>{const n=p.nombre_article||0;csv+=(p.id||'')+','+(p.supplier||'')+','+(p.date_achat||'')+','+n+','+(p.montant_total||0)+','+(p.montant_verse||0)+','+(p.montant_reste||0)+','+(p.tva_pct||0)+','+(p.montant_tva||0)+','+(p.total_ht||0)+'\\n'});const blob=new Blob([csv],{type:'text/csv;charset=utf-8;'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='achats_'+new Date().toISOString().split('T')[0]+'.csv';a.click();URL.revokeObjectURL(url);showToast('Exporte avec succes!','success')}

// Override switchView to load purchase list
(function(){const orig=switchView;switchView=function(v){orig(v);if(v==='purchases-list')loadPurchaseList()}})();

console.log('Royal POS Engine Ready');
console.log('Purchase Engine Ready');
"""

if old_end in js:
    js = js.replace(old_end, new_section)
    print('Purchase list functions added: OK')
else:
    print('End marker not found!')
    # Find what's actually at the end
    print(f'Last 200 chars: ...{js[-200:]}')

with open('C:/Users/Micro-Tech/.openclaw/workspace/static/pos/pos.js', 'w', encoding='utf-8') as f:
    f.write(js)
print('Done!')

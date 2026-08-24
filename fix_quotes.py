with open('rcagents_saas_core/frontend/templates/dashboard.html', 'r', encoding='utf-8') as f:
    tpl = f.read()

# Replace all inner HTML quotes in connect methods with &quot;
tpl = tpl.replace('class=\u0022text-neon-cyan\u0022', 'class=&quot;text-neon-cyan&quot;')
tpl = tpl.replace('class=\u0022text-emerald-400\u0022', 'class=&quot;text-emerald-400&quot;')
tpl = tpl.replace('class=\u0022text-rose-400\u0022', 'class=&quot;text-rose-400&quot;')

with open('rcagents_saas_core/frontend/templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(tpl)

print('Done - quotes escaped!')

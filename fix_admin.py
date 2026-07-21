with open('applns.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = '<a href="/admin" class="action-btn" style="border-color:rgba(102,126,234,0.3);"><div class="icon">⚙️</div><div class="label">Admin Panel</div></a>'
new = '<a href="/admin-login" class="action-btn" style="border-color:rgba(255,107,107,0.3);"><div class="icon">🛡️</div><div class="label">Admin Panel</div></a>'

if old in content:
    content = content.replace(old, new)
    print("Done. 1/1 fix applied.")
else:
    print("NOT FOUND: dashboard admin panel link")

with open('applns.py', 'w', encoding='utf-8') as f:
    f.write(content)
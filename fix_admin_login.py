with open('applns.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = """    if is_authenticated():
        if is_admin():
            return redirect('/admin')
        return redirect('/')
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email, role='admin').first()"""

new = """    if is_authenticated() and is_admin():
        return redirect('/admin')
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email, role='admin').first()"""

if old in content:
    content = content.replace(old, new)
    print("Done. 1/1 fix applied.")
else:
    print("NOT FOUND: admin_login_page redirect block")

with open('applns.py', 'w', encoding='utf-8') as f:
    f.write(content)
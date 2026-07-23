with open('applns.py', 'r', encoding='utf-8') as f:
    content = f.read()

changed = 0

old_nav = '''        <div class="admin-nav">
            <a href="/admin" class="active"><i class="fas fa-chart-pie"></i> Dashboard</a>
            <a href="/admin/users"><i class="fas fa-users"></i> Users</a>
            <a href="/admin/schedule"><i class="fas fa-calendar-plus"></i> Schedule</a>
            <a href="/logout" class="logout-btn"><i class="fas fa-sign-out-alt"></i> Logout</a>
        </div>'''

new_nav = '''        <div class="admin-nav">
            <a href="/admin" class="{% if active_tab == 'dashboard' %}active{% endif %}"><i class="fas fa-chart-pie"></i> Dashboard</a>
            <a href="/admin/users" class="{% if active_tab == 'users' %}active{% endif %}"><i class="fas fa-users"></i> Users</a>
            <a href="/admin/schedule" class="{% if active_tab == 'schedule' %}active{% endif %}"><i class="fas fa-calendar-plus"></i> Schedule</a>
            <a href="/logout" class="logout-btn"><i class="fas fa-sign-out-alt"></i> Logout</a>
        </div>'''

if old_nav in content:
    content = content.replace(old_nav, new_nav)
    changed += 1
    print("Fix 1a done: nav active-tab highlighting")
else:
    print("NOT FOUND: admin nav block")

old_table_title = '''        <div class="table-title"><i class="fas fa-users"></i> All Users</div>'''
new_table_title = '''        <div class="table-title"><i class="fas fa-users"></i> {{ table_title }}</div>'''
if old_table_title in content:
    content = content.replace(old_table_title, new_table_title)
    changed += 1
    print("Fix 1b done: dynamic table title")
else:
    print("NOT FOUND: table title block")

old_routes = '''@app.route('/admin')
def admin():
    if not is_authenticated() or not is_admin():
        return redirect('/')
    users = User.query.order_by(User.created_at.desc()).all()
    non_admin_users = [u for u in users if u.role != 'admin']
    completed = [u for u in non_admin_users if u.interview_complete]
    stats = {
        'total_users': len(users),
        'completed_interviews': len(completed),
        'pending_interviews': len(non_admin_users) - len(completed),
        'avg_score': get_avg_score(non_admin_users),
        'pass_rate': get_pass_rate(non_admin_users),
    }
    return render_template_string(ADMIN_HTML, users=users, stats=stats)

@app.route('/admin/users')
def admin_users():
    if not is_authenticated() or not is_admin():
        return redirect('/')
    return admin()

@app.route('/admin/schedule')
def admin_schedule():
    if not is_authenticated() or not is_admin():
        return redirect('/')
    return admin()'''

new_routes = '''def _admin_stats_and_all_users():
    users = User.query.order_by(User.created_at.desc()).all()
    non_admin_users = [u for u in users if u.role != 'admin']
    completed = [u for u in non_admin_users if u.interview_complete]
    stats = {
        'total_users': len(users),
        'completed_interviews': len(completed),
        'pending_interviews': len(non_admin_users) - len(completed),
        'avg_score': get_avg_score(non_admin_users),
        'pass_rate': get_pass_rate(non_admin_users),
    }
    return users, stats


@app.route('/admin')
def admin():
    if not is_authenticated() or not is_admin():
        return redirect('/')
    users, stats = _admin_stats_and_all_users()
    return render_template_string(ADMIN_HTML, users=users, stats=stats,
                                   active_tab='dashboard', table_title='All Users')

@app.route('/admin/users')
def admin_users():
    if not is_authenticated() or not is_admin():
        return redirect('/')
    users, stats = _admin_stats_and_all_users()
    return render_template_string(ADMIN_HTML, users=users, stats=stats,
                                   active_tab='users', table_title='All Users')

@app.route('/admin/schedule')
def admin_schedule():
    if not is_authenticated() or not is_admin():
        return redirect('/')
    all_users, stats = _admin_stats_and_all_users()
    pending_users = [u for u in all_users if u.role != 'admin' and not u.interview_complete]
    return render_template_string(ADMIN_HTML, users=pending_users, stats=stats,
                                   active_tab='schedule', table_title='Users Awaiting Interview Scheduling')'''

if old_routes in content:
    content = content.replace(old_routes, new_routes)
    changed += 1
    print("Fix 2 done: admin/users/schedule routes")
else:
    print("NOT FOUND: admin routes block")

old_select = '''            <select name="user_type" required>
                <option value="">Select User Type</option>
                <option value="student">🎓 Student</option>
                <option value="professional">💼 Professional</option>
                <option value="entrepreneur">🚀 Entrepreneur</option>
                <option value="other">Other</option>
            </select>'''

new_select = '''            <select name="user_type" id="userTypeSelect" required onchange="toggleCgpaField()">
                <option value="">Select User Type</option>
                <option value="student">🎓 Student</option>
                <option value="professional">💼 Professional</option>
                <option value="entrepreneur">🚀 Entrepreneur</option>
                <option value="other">Other</option>
            </select>'''

if old_select in content:
    content = content.replace(old_select, new_select)
    changed += 1
    print("Fix 3a done: user_type select id + onchange")
else:
    print("NOT FOUND: user_type select block")

old_cgpa_row = '''            <div class="row">
                <select name="experience_years">
                    <option value="0">0 - Fresher</option>
                    <option value="1">1 year</option>
                    <option value="2">2 years</option>
                    <option value="3">3 years</option>
                    <option value="4">4 years</option>
                    <option value="5">5+ years</option>
                </select>
                <input type="number" name="cgpa" step="0.01" placeholder="CGPA (0-10)">
            </div>'''

new_cgpa_row = '''            <div class="row">
                <select name="experience_years">
                    <option value="0">0 - Fresher</option>
                    <option value="1">1 year</option>
                    <option value="2">2 years</option>
                    <option value="3">3 years</option>
                    <option value="4">4 years</option>
                    <option value="5">5+ years</option>
                </select>
                <input type="number" name="cgpa" id="cgpaField" step="0.01" placeholder="CGPA (0-10)" style="display:none;">
            </div>'''

if old_cgpa_row in content:
    content = content.replace(old_cgpa_row, new_cgpa_row)
    changed += 1
    print("Fix 3b done: cgpa field hidden by default")
else:
    print("NOT FOUND: cgpa row block")

old_script_start = '''<script>
document.getElementById('registerForm').addEventListener('submit', async function(e) {'''

new_script_start = '''<script>
function toggleCgpaField() {
    const type = document.getElementById('userTypeSelect').value;
    const cgpa = document.getElementById('cgpaField');
    if (type === 'student') {
        cgpa.style.display = 'block';
    } else {
        cgpa.style.display = 'none';
        cgpa.value = '';
    }
}

document.getElementById('registerForm').addEventListener('submit', async function(e) {'''

if old_script_start in content:
    content = content.replace(old_script_start, new_script_start)
    changed += 1
    print("Fix 3c done: toggleCgpaField JS function added")
else:
    print("NOT FOUND: register form script start")

with open('applns.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\nDone. {changed}/6 fixes applied.")
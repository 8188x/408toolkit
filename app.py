"""408Toolkit - 408考研学习平台 (含用户/题库/刷题/错题/资料)"""
import json, hashlib, os, random, re, time, functools
from flask import Flask, request, render_template, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = os.urandom(24).hex()
DB = os.path.join(os.path.dirname(__file__), 'data.json')

# ─── Cache ───
_cache = {}
CACHE_TTL = 60  # seconds

def load():
    now = time.time()
    if 'data' in _cache and now - _cache.get('ts', 0) < CACHE_TTL:
        return _cache['data']
    try:
        with open(DB) as f:
            data = json.load(f)
        _cache['data'] = data
        _cache['ts'] = now
        return data
    except (FileNotFoundError, json.JSONDecodeError):
        return {'questions':[], 'users':[], 'subjects':{}, 'codes':[], 'materials':{}}

def save(data):
    try:
        with open(DB, 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        # Invalidate cache
        _cache.pop('data', None)
    except Exception as e:
        print(f"Save error: {e}")

def get_user():
    uid = session.get('user_id')
    if uid:
        data = load()
        for u in data.get('users', []):
            if u['id'] == uid:
                return u
    return None

def hash_pwd(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.context_processor
def inject_user():
    return dict(current_user=get_user(), subjects=load().get('subjects', {}))

# ── Pages ──
@app.route('/')
def index():
    return render_template('index.html')

PAGE_SIZE = 20

@app.route('/questions')
def questions():
    data = load()
    qs = data.get('questions', [])
    sub = request.args.get('sub', '')
    q = request.args.get('q', '')
    page = int(request.args.get('page', '1'))
    if sub: qs = [x for x in qs if x.get('sub') == sub]
    if q: qs = [x for x in qs if q.lower() in x.get('q', '').lower()]
    total = len(qs)
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(1, min(page, total_pages))
    start = (page - 1) * PAGE_SIZE
    qs_page = qs[start:start + PAGE_SIZE]
    return render_template('questions.html', questions=qs_page, subjects=data.get('subjects', {}),
                           sel=sub, sq=q, page=page, total_pages=total_pages, total=total)

@app.route('/quiz')
def quiz():
    data = load()
    qs = list(data.get('questions', []))
    sub = request.args.get('sub', '')
    if sub: qs = [x for x in qs if x.get('sub') == sub]
    random.shuffle(qs)
    return render_template('quiz.html', questions=qs, subjects=data.get('subjects', {}), sel=sub)

@app.route('/code')
def code():
    data = load()
    cs = data.get('codes', [])
    sub = request.args.get('sub', '')
    if sub: cs = [x for x in cs if x.get('sub') == sub]
    return render_template('code.html', codes=cs, subjects=data.get('subjects', {}), sel=sub)

@app.route('/materials')
def materials():
    data = load()
    return render_template('materials.html', materials=data.get('materials', {}), subjects=data.get('subjects', {}))

@app.route('/summary')
def summary():
    return render_template('summary.html')

@app.route('/wrong')
def wrong():
    user = get_user()
    if not user:
        return redirect(url_for('login'))
    data = load()
    wrong_ids = user.get('wrong', [])
    wrong_qs = [q for q in data.get('questions', []) if q['id'] in wrong_ids]
    return render_template('wrong.html', wrong=wrong_qs, subjects=data.get('subjects', {}))

# ── Auth ──
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = load()
        uname = request.form.get('username', '').strip()
        pwd = hash_pwd(request.form.get('password', ''))
        for u in data.get('users', []):
            if u['username'] == uname and u.get('pass') == pwd:
                session['user_id'] = u['id']
                session.permanent = True
                return redirect(url_for('index'))
        return render_template('login.html', error='用户名或密码错误')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = load()
        uname = request.form.get('username', '').strip()
        pwd = request.form.get('password', '')
        if len(uname) < 2:
            return render_template('register.html', error='用户名至少2个字符')
        if len(pwd) < 4:
            return render_template('register.html', error='密码至少4个字符')
        pwd = hash_pwd(pwd)
        users = data.get('users', [])
        if any(u['username'] == uname for u in users):
            return render_template('register.html', error='用户名已存在')
        uid = max((u['id'] for u in users), default=0) + 1
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        users.append({'id': uid, 'username': uname, 'pass': pwd, 'phone': phone, 'email': email, 'wrong': []})
        data['users'] = users
        save(data)
        session['user_id'] = uid
        session.permanent = True
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# ── API ──
@app.route('/api/wrong/add', methods=['POST'])
def api_wrong_add():
    user = get_user()
    if not user:
        return jsonify({'error': 'not logged in'}), 401
    data = load()
    qid = request.json.get('qid')
    if not qid:
        return jsonify({'error': 'invalid qid'}), 400
    for u in data['users']:
        if u['id'] == user['id']:
            if qid not in u['wrong']:
                u['wrong'].append(qid)
            break
    save(data)
    return jsonify({'ok': True})

@app.route('/api/wrong/remove', methods=['POST'])
def api_wrong_remove():
    user = get_user()
    if not user:
        return jsonify({'error': 'not logged in'}), 401
    data = load()
    qid = request.json.get('qid')
    for u in data['users']:
        if u['id'] == user['id'] and qid in u['wrong']:
            u['wrong'].remove(qid)
            break
    save(data)
    return jsonify({'ok': True})

@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    data = load()
    if request.method == 'POST':
        step = request.form.get('step', '')
        if step == 'lookup':
            uname = request.form.get('username', '').strip()
            for u in data.get('users', []):
                if u['username'] == uname:
                    return render_template('forgot.html', step='verify', uid=u['id'], uname=u['username'],
                                           email=u.get('email',''), phone=u.get('phone',''))
            return render_template('forgot.html', error='用户名不存在')
        elif step == 'do_verify':
            uid = int(request.form.get('uid', 0))
            verify = request.form.get('verify', '').strip()
            for u in data.get('users', []):
                if u['id'] == uid and (verify == u.get('email','') or verify == u.get('phone','')):
                    return render_template('forgot.html', step='reset', uid=uid)
            return render_template('forgot.html', error='验证信息不匹配', step='verify', uid=uid,
                                   uname=u.get('username',''), email=u.get('email',''), phone=u.get('phone',''))
        elif step == 'do_reset':
            uid = int(request.form.get('uid', 0))
            pwd = hash_pwd(request.form.get('password', ''))
            for u in data.get('users', []):
                if u['id'] == uid:
                    u['pass'] = pwd; break
            save(data)
            return render_template('forgot.html', done=True)
    return render_template('forgot.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5010, debug=False)

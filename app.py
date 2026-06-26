"""408Toolkit - 408考研学习平台 (含用户/题库/刷题/错题/资料)"""
import json, hashlib, os, random, re
from flask import Flask, request, render_template, redirect, url_for, session

app = Flask(__name__)
app.secret_key = os.urandom(24).hex()

@app.context_processor
def inject_user():
    return dict(current_user=get_user())
DB = os.path.join(os.path.dirname(__file__), 'data.json')

def load():
    with open(DB) as f:
        return json.load(f)

def save(data):
    with open(DB, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user():
    uid = session.get('user_id')
    if uid:
        data = load()
        for u in data.get('users', []):
            if u['id'] == uid:
                return u
    return None

# ====== Pages ======
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/questions')
def questions():
    data = load()
    qs = data['questions']
    sub = request.args.get('sub', '')
    q = request.args.get('q', '')
    if sub: qs = [x for x in qs if x['sub'] == sub]
    if q: qs = [x for x in qs if q.lower() in x['q'].lower()]
    return render_template('questions.html', questions=qs, subjects=data['subjects'], sel=sub, sq=q)

@app.route('/quiz')
def quiz():
    data = load()
    qs = list(data['questions'])
    sub = request.args.get('sub', '')
    if sub: qs = [x for x in qs if x['sub'] == sub]
    random.shuffle(qs)
    return render_template('quiz.html', questions=qs, subjects=data['subjects'], sel=sub)

@app.route('/code')
def code():
    data = load()
    cs = data['codes']
    sub = request.args.get('sub', '')
    if sub: cs = [x for x in cs if x['sub'] == sub]
    return render_template('code.html', codes=cs, subjects=data['subjects'], sel=sub)

@app.route('/materials')
def materials():
    data = load()
    return render_template('materials.html', materials=data['materials'], subjects=data['subjects'])

@app.route('/wrong')
def wrong():
    data = load()
    user = get_user()
    wrong_ids = user.get('wrong', []) if user else []
    wrong_qs = [q for q in data['questions'] if q['id'] in wrong_ids]
    return render_template('wrong.html', wrong=wrong_qs, subjects=data['subjects'])

# ====== Auth ======
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = load()
        uname = request.form.get('username', '')
        pwd = hashlib.sha256(request.form.get('password', '').encode()).hexdigest()
        for u in data.get('users', []):
            if u['username'] == uname and u.get('pass') == pwd:
                session['user_id'] = u['id']
                return redirect(url_for('index'))
        return render_template('login.html', error='用户名或密码错误')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = load()
        uname = request.form.get('username', '')
        pwd = hashlib.sha256(request.form.get('password', '').encode()).hexdigest()
        if any(u['username'] == uname for u in data.get('users', [])):
            return render_template('register.html', error='用户名已存在')
        uid = max((u['id'] for u in data.get('users', [])), default=0) + 1
        phone = request.form.get('phone', ''); email = request.form.get('email', '')
        data.setdefault('users', []).append({'id': uid, 'username': uname, 'pass': pwd, 'phone': phone, 'email': email, 'wrong': []})
        save(data)
        session['user_id'] = uid
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

# ====== API ======
@app.route('/api/wrong/add', methods=['POST'])
def api_wrong_add():
    user = get_user()
    if not user: return '{}', 200
    data = load()
    qid = request.json.get('qid')
    for u in data['users']:
        if u['id'] == user['id']:
            if qid not in u['wrong']:
                u['wrong'].append(qid)
            break
    save(data)
    return '{"ok":true}', 200


@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    data = load()
    if request.method == 'POST':
        step = request.form.get('step', '')
        if step == 'lookup':
            uname = request.form.get('username', '')
            for u in data.get('users', []):
                if u['username'] == uname:
                    return render_template('forgot.html', step='verify', uid=u['id'], uname=u['username'], email=u.get('email',''), phone=u.get('phone',''))
            return render_template('forgot.html', error='用户名不存在')
        elif step == 'do_verify':
            uid = int(request.form.get('uid', 0))
            verify = request.form.get('verify', '').strip()
            for u in data.get('users', []):
                if u['id'] == uid and (verify == u.get('email','') or verify == u.get('phone','')):
                    return render_template('forgot.html', step='reset', uid=uid)
            return render_template('forgot.html', error='验证信息不匹配', step='verify', uid=uid, uname=u.get('username',''), email=u.get('email',''), phone=u.get('phone',''))
        elif step == 'do_reset':
            uid = int(request.form.get('uid', 0))
            pwd = hashlib.sha256(request.form.get('password', '').encode()).hexdigest()
            for u in data.get('users', []):
                if u['id'] == uid:
                    u['pass'] = pwd
                    break
            save(data)
            return render_template('forgot.html', done=True)
    return render_template('forgot.html')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5010)

"""408Toolkit - 考研实用工具集 (服务器端渲染, 无需JS)"""
import json, hashlib, os
from datetime import datetime
from flask import Flask, jsonify, request, render_template, session

app = Flask(__name__)
app.secret_key = '408tk-2026'

# ============ Simple JSON database ============
DB_FILE = os.path.join(os.path.dirname(__file__), 'data.json')

def load_db():
    if not os.path.exists(DB_FILE):
        return init_db()
    with open(DB_FILE, 'r') as f:
        return json.load(f)

def save_db(db):
    with open(DB_FILE, 'w') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def init_db():
    db = {
        'users': [
            {'id':1,'username':'admin','password':hashlib.sha256(b'admin123').hexdigest(),'created':'2026-01-01'}
        ],
        'questions': [
            {'id':1,'topic':'ds','title':'在完全二叉树中，叶子结点数和度为2的节点数的关系是？','opts':[('A','n0=n2+1'),('B','n0=n2'),('C','n0=n2-1'),('D','n0=2n2')],'ans':'A','diff':2},
            {'id':2,'topic':'ds','title':'快速排序最坏情况复杂度','opts':[('A','O(n)'),('B','O(nlogn)'),('C','O(n²)'),('D','O(logn)')],'ans':'C','diff':1},
            {'id':3,'topic':'ds','title':'下列哪种遍历组合可以唯一确定二叉树','opts':[('A','先序+后序'),('B','先序+中序'),('C','中序+后序'),('D','先序+层序')],'ans':'B','diff':3},
            {'id':4,'topic':'co','title':'Cache的主要作用是','opts':[('A','扩大容量'),('B','提高CPU速度'),('C','降低功耗'),('D','管理外设')],'ans':'B','diff':1},
            {'id':5,'topic':'co','title':'虚拟存储器的原理基于','opts':[('A','时间局部性'),('B','空间局部性'),('C','局部性原理'),('D','顺序性')],'ans':'C','diff':2},
            {'id':6,'topic':'co','title':'IEEE754浮点数标准中，单精度浮点数的阶码位数是','opts':[('A','8'),('B','9'),('C','10'),('D','11')],'ans':'A','diff':3},
            {'id':7,'topic':'os','title':'TCP协议位于OSI模型的第几层','opts':[('A','3'),('B','4'),('C','5'),('D','6')],'ans':'B','diff':1},
            {'id':8,'topic':'cn','title':'HTTP默认端口','opts':[('A','21'),('B','25'),('C','80'),('D','443')],'ans':'C','diff':1},
            {'id':9,'topic':'cn','title':'CSMA/CD用于解决','opts':[('A','路由'),('B','拥塞'),('C','信道争用'),('D','流量控制')],'ans':'C','diff':2},
            {'id':10,'topic':'os','title':'分页存储中逻辑-物理地址转换由谁完成','opts':[('A','CPU'),('B','MMU'),('C','OS'),('D','编译器')],'ans':'B','diff':2},
        ],
        'topics': {
            'ds': '数据结构',
            'co': '计算机组成原理',
            'os': '操作系统',
            'cn': '计算机网络',
        }
    }
    save_db(db)
    return db


# ============ Routes ============
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/questions')
def questions():
    db = load_db()
    qs = db['questions']
    topic = request.args.get('topic', '')
    if topic:
        qs = [q for q in qs if q['topic'] == topic]
    topics = db['topics']
    return render_template('questions.html', questions=qs, topics=topics, selected=topic)

@app.route('/quiz')
def quiz():
    db = load_db()
    qs = db['questions']
    # Shuffle by importing random
    import random
    random.shuffle(qs)
    return render_template('quiz.html', questions=qs[:10], topics=db['topics'])

@app.route('/codes')
def codes():
    return render_template('codes.html')

@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/api/check')
def api_check():
    return '{"status":"ok"}'

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5010, debug=True)

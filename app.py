from flask import Flask, render_template, jsonify, request
from flask import Flask, render_template, jsonify, request, redirect, url_for
from pymongo import MongoClient
import jwt
import datetime
import hashlib
from datetime import datetime, timedelta

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True

from pymongo import MongoClient
SECRET_KEY = 'SPARTA'

# client = MongoClient('3.36.48.90', 27017, username="test", password="test")
client = MongoClient('localhost', 27017)
db = client.wherewego

## HTML 화면 보여주기
@app.route('/')
def homework():
    return render_template('index.html')
def home():
    token_receive = request.cookies.get('mytoken')
    # try 아래를 실행해서 에러가 생기면 except 구문으로 가라는 거
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        users = db.users.find_one({"id": payload["id"]})
        return render_template('index.html', users=users)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))

# 로그인 화면
@app.route('/login')
def login():
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)

@app.route('/sign_in', methods=['POST'])
def sign_in():
    # 로그인
    id_receive = request.form['id_give']
    pwd_receive = request.form['pwd_give']
    pw_hash = hashlib.sha256(pwd_receive.encode('utf-8')).hexdigest()
    result = db.users.find_one({'id': id_receive, 'pwd': pw_hash})

    if result is not None:
        payload = {
            'id': id_receive,
            'exp': datetime.utcnow() + timedelta(seconds=600)  # 로그인 유지 시간
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256').decode('utf-8')

        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


@app.route('/sign_up/save', methods=['POST'])
def sign_up():
    id_receive = request.form['id_give']
    pwd_receive = request.form['pwd_give']
    pwd_hash = hashlib.sha256(pwd_receive.encode('utf-8')).hexdigest()
    name_receive = request.form['name_give']

    doc = {
        "id": id_receive,  # 아이디
        "pwd": pwd_hash,  # 비밀번호
        "name": name_receive  # 이름
    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})

@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    id_receive = request.form['id_give']
    exists = bool(db.users.find_one({"id": id_receive}))
    return jsonify({'result': 'success', 'exists': exists})

# 캠핑 목록보기(Read) API
@app.route('/camping', methods=['GET'])
def view_campings():
    campInfos = list(db.campinfos.find({}, {'_id': False}))

    return jsonify({'campInfos': campInfos})


# 캠핑 목록 소팅(POST) - 도시
@app.route('/sort_city', methods=['POST'])
def sort_city():
    loc_receive = request.form['loc']
    camps = list(db.campinfos.find({}, {'_id': False}))

    sort_city = []

    for camp in camps:
        location = camp["location"]
        if loc_receive in location:
            sort_city.append(camp)

    return jsonify({'sort_city': sort_city})


# 캠핑 목록 소팅(POST) - 테마
@app.route('/sort_theme', methods=['POST'])
def sort_theme():
    theme_receive = request.form['theme']
    camps = list(db.campinfos.find({}, {'_id': False}))

    sort_theme = []

    for camp in camps:
        tag = camp["tag"]
        if theme_receive in tag:
            sort_theme.append(camp)

    for x in sort_theme:
        print(x)
    return jsonify({'sort_theme': sort_theme})


# 캠핑 목록 소팅(POST) - 리뷰수
@app.route('/sort_order', methods=['POST'])
def sort_view():
    order_receive = request.form['order']
    camps = list(db.campinfos.find({}, {'_id': False}))
    sort_order = []

    for camp in camps:
        camp['view'] = int(camp['view'])
    
    if order_receive == 'descending':
        sort_order = sorted(camps, key=(lambda x: x['view']), reverse=True)
        for x in sort_order:
            print(x)

    return jsonify({'sort_order': sort_order})


# 캠핑 리뷰저장(POST)
@app.route('/review', methods=['POST'])
def save_review():
    star = request.form['review_star']
    comment = request.form['review_comment']

    doc = {
        'star': star,
        'comment': comment,
    }

    db.reviews.insert_one(doc)
    reviews = list(db.reviews.find({}, {'_id': False}))

    return jsonify({'reviews': reviews})

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)

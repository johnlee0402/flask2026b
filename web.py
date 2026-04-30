import requests
from bs4 import BeautifulSoup

from flask import Flask, render_template, request
from datetime import datetime

import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

# 判斷是在 Vercel 還是本地
if os.path.exists('serviceAccountKey.json'):
    # 本地環境：讀取檔案
    cred = credentials.Certificate('serviceAccountKey.json')
else:
    # 雲端環境：從環境變數讀取 JSON 字串
    firebase_config = os.getenv('FIREBASE_CONFIG')
    cred_dict = json.loads(firebase_config)
    cred = credentials.Certificate(cred_dict)

firebase_admin.initialize_app(cred)


app = Flask(__name__)

@app.route("/")
def index():
    link = "<h1>歡迎進入李孟翰的網站20260409</h1>"
    link += "<a href=/mis>課程</a><hr>"
    link += "<a href=/today>現在日期時間</a><hr>"
    link += "<a href=/me>關於我</a><hr>"
    link += "<a href=/welcome?u=孟翰&d=靜宜資管&c=資訊管理導論>Get傳直</a><hr>"
    link += "<a href=/account>POST傳直</a><hr>"
    link += "<a href=/math>次方與根號計算</a><hr>"
    link += "<a href=/read>讀取Firestore資料</a><hr>"
    link += "<a href=/read2>讀取Firestore資料(根據姓名關鍵字)</a><hr>"
    link += "<a href=/spider1>爬蟲子青老師本學期課程</a><hr>"
    link += "<a href=/job>個人求職履歷</a><hr>"
    link += "<a href=/movie1>即將上映電影</a><hr>"
    link += "<a href=/spiderMovie>爬取即將上映電影</a><hr>"
    link += "<a href=/searchMovie>查詢即將上映電影</a><hr>"
    return link

@app.route("/searchMovie")
def searchMovie():
    keyword = request.args.get("q", "").strip()

    db = firestore.client()
    collection_ref = db.collection("電影2B")
    
    R = "<h2>電影關鍵字查詢 (資料庫)</h2>"
    R += """
        <form action="/searchMovie" method="get">
            <input type="text" name="q" placeholder="輸入片名關鍵字..." value="{}">
            <button type="submit">搜尋</button>
        </form>
        <hr>
    """.format(keyword)

    try:
        docs = collection_ref.get()
        
        found_count = 0
        table_html = """
            <table border="1" style="width:100%; border-collapse: collapse; text-align: left;">
                <tr style="background-color: #f2f2f2;">
                    <th>編號</th>
                    <th>海報</th>
                    <th>片名</th>
                    <th>上映日期</th>
                    <th>介紹頁</th>
                </tr>
        """

        for doc in docs:
            movie = doc.to_dict()
            title = movie.get("title", "")
            
            if keyword in title:
                found_count += 1
                movie_id = doc.id
                pic = movie.get("picture", "")
                link = movie.get("hyperlink", "")
                sd = movie.get("showDate", "")
                
                table_html += f"""
                    <tr>
                        <td>{movie_id}</td>
                        <td><img src="{pic}" width="100"></td>
                        <td>{title}</td>
                        <td>{sd}</td>
                        <td><a href="{link}" target="_blank">點我觀看</a></td>
                    </tr>
                """

        table_html += "</table>"

        if found_count > 0:
            R += f"<p>找到 {found_count} 部符合『{keyword}』的電影：</p>"
            R += table_html
        else:
            R += f"<p>目前資料庫中沒有關於『{keyword}』的電影。</p>"

    except Exception as e:
        R += f"查詢出錯：{e}"

    R += "<br><a href='/'>返回首頁</a>"
    return R    

@app.route("/spiderMovie")
def spiderMovie():
    R = ""
    db = firestore.client()

    import requests
    from bs4 import BeautifulSoup
    url = "http://www.atmovies.com.tw/movie/next/"
    Data = requests.get(url)
    Data.encoding = "utf-8"

    sp = BeautifulSoup(Data.text, "html.parser")
    lastUpdate = sp.find(class_="smaller09").text.replace("更新時間 :", "")

    result=sp.select(".filmListAllX li")
    total = 0
    for item in result:
        total += 1
        movie_id = item.find("a").get("href").replace("/movie/", "").replace("/", "")
        title = item.find(class_="filmtitle").text
        picture = "http://www.atmovies.com.tw" + item.find("img").get("src")
        hyperlink = "http://www.atmovies.com.tw" + item.find("a").get("href")

        showDate = item.find(class_="runtime").text[5:15]

        doc = {
            "title": title,
            "picture": picture,
            "hyperlink": hyperlink,
            "showDate": showDate,
            "lastUpdate": lastUpdate
        }

        doc_ref = db.collection("電影2B").document(movie_id)
        doc_ref.set(doc)

    R +="網站最近更新日期:"+lastUpdate+"<br>"
    R +="總共爬取" + str(total) + "部電影到資料庫"  

    return R


@app.route("/movie1")
def movie1():
    keyword = request.args.get("q", "")

    R = "<h2>電影搜尋系統</h2>"
    R += """
        <form action="/movie1" method="get">
            <input type="text" name="q" placeholder="輸入片名關鍵字..." value="{}">
            <button type="submit">搜尋電影</button>
        </form>
        <hr>
    """.format(keyword)

    url = "https://www.atmovies.com.tw/movie/next/"
    try:
        data = requests.get(url)
        data.encoding = "utf-8"
        sp = BeautifulSoup(data.text, "html.parser")
        result = sp.select(".filmListAllX li")
        
        found_count = 0
        for item in result:
            title = item.find("img").get("alt")
            
            if keyword in title:
                found_count += 1
                introduce = "https://www.atmovies.com.tw" + item.find("a").get("href")
                post = "https://www.atmovies.com.tw" + item.find("img").get("src")
                
                R += f"<div>"
                R += f"  <a href='{introduce}' style='text-decoration:none;'><strong>{title}</strong></a><br>"
                R += f"  <img src='{post}' style='width:180px; margin-top:10px; border-radius:5px;'><br><br>"
                R += f"</div>"

        if found_count == 0:
            R += f"<p>找不到包含『{keyword}』的相關電影。</p>"
            
    except Exception as e:
        R += f"發生錯誤: {e}"

    return R


@app.route("/job")
def job():
    return render_template("job.html")

@app.route("/spider1")
def spider1():
    Result = ""
    url = "https://www1.pu.edu.tw/~tcyang/course.html"
    Data = requests.get(url,verify=False)
    Data.encoding = "utf-8"
    sp = BeautifulSoup(Data.text, "html.parser")
    result=sp.select(".team-box a")

    for i in result:
        Result += i.text + i.get("href") + "<br>"
    return Result

@app.route("/")
def home():
    return render_template("teacher.html", result="")

@app.route("/read2")
def read2():
    keyword = request.args.get("keyword")

    if keyword is None or keyword.strip() == "":
        return render_template("teacher.html", result="請輸入老師姓名關鍵字")

    db = firestore.client()
    collection_ref = db.collection("靜宜資管2026B")
    docs = collection_ref.get()

    result = ""

    for doc in docs:
        teacher = doc.to_dict()
        print("teacher =", teacher)

        if "name" in teacher and "lab" in teacher:
            if keyword in str(teacher["name"]):
                result += f"{teacher['name']} 老師的研究室在 {teacher['lab']}<br>"

    if result == "":
        result = f"查無資料，關鍵字是：{keyword}"

    result = f"查詢結果（關鍵字：{keyword}）：<br><br>" + result

    return render_template("teacher.html", result=result)

@app.route("/read")
def read():
    Result = ""
    db = firestore.client()
    collection_ref = db.collection("靜宜資管2026B")    
    docs = collection_ref.order_by("lab", direction=firestore.Query.DESCENDING).get() 
    for doc in docs:         
        Result += str(doc.to_dict()) + "<br>"    
    return Result


@app.route("/mis")
def course():
    return "<h1>資訊管理導論</h1><a href=/>返回首頁</a>"

@app.route("/today")
def today():
    now = datetime.now()
    return render_template("today.html",datetime=str(now))

@app.route("/me")
def me():
    return render_template("mis2026d.html")

@app.route("/welcome", methods=["GET"])
def welcome():
    user = request.values.get("u")
    d= request.values.get("d")
    c= request.values.get("c")
    return render_template("welcome.html", name= user, dep=d, course=c)

@app.route("/account", methods=["GET", "POST"])
def account():
    if request.method == "POST":
        user = request.form["user"]
        pwd = request.form["pwd"]
        result = "您輸入的帳號是：" + user + "; 密碼為：" + pwd 
        return result
    else:
        return render_template("account.html")

@app.route("/math")
def math():
    return render_template("math.html")


if __name__ == "__main__":
    app.run()

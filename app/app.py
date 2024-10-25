from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

import os
from enum import Enum
import json

from models import User
from db_client import DBHandler

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(24)

# Flask-Login の初期化
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# DBHandlerの初期化
db = DBHandler("example.db")

@login_manager.user_loader
def load_user(user_id):
    user_data = db.select("users", fields="id, username, password", conditions={"id": user_id}, limit=1)
    if user_data:
        user = User(user_data[0]["id"], user_data[0]["username"], user_data[0]["password"])
        return user
    return None

@app.route("/")
@login_required
def index():
    # ログイン後はユーザーのマイページにリダイレクト
    return redirect(url_for("mypage"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # ユーザー認証 (パスワードはハッシュをチェック)
        user_data = db.select("users", fields="id, username, password", conditions={"username": username}, limit=1)
        if user_data and check_password_hash(user_data[0]["password"], password):
            user = User(user_data[0]["id"], user_data[0]["username"], user_data[0]["password"])
            login_user(user)
            return redirect(url_for("mypage"))  # ログイン後にマイページにリダイレクト
        else:
            flash("Invalid username or password", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

# マイページエンドポイント
@app.route("/mypage")
@login_required
def mypage():
    # 現在のユーザーのポートフォリオを取得
    portfolios = db.select("portfolios", fields="id, title, type, content", conditions={"user_id": current_user.id})
    for portfolio in portfolios:
        try:
            portfolio_type = PortfolioType(portfolio["type"])
            portfolio["type_label"] = portfolio_type.label
        except ValueError:
            portfolio["type_label"] = "未知の種類"
    # マイページテンプレートに渡す
    return render_template("mypage.html", user=current_user, portfolios=portfolios)


# ここから追加: ユーザー登録用のエンドポイント
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # ユーザーがすでに存在するか確認
        if db.data_exists("users", {"username": username}):
            flash("Username already exists. Please choose a different one.", "danger")
            return redirect(url_for("register"))

        # パスワードをハッシュ化して保存
        hashed_password = generate_password_hash(password)
        db.insert_data("users", {"username": username, "password": hashed_password})
        flash("Registration successful! You can now log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

# ポートフォリオ編集ページ
@app.route("/portfolio/edit", methods=["GET", "POST"])
@login_required
def portfolio_edit():
    if request.method == "POST":
        portfolio_id = request.form["portfolio_id"]
        new_title = request.form["title"]
        new_description = request.form["description"]

        # ポートフォリオの更新処理
        db.update_data("portfolios", updates={"title": new_title, "description": new_description}, conditions={"id": portfolio_id, "user_id": current_user.id})
        flash("ポートフォリオが更新されました", "success")
        return redirect(url_for("mypage"))

    return render_template("portfolio_edit.html")


# ポートフォリオの種類を定義
class PortfolioType(Enum):
    SKILLSET = 'skillset'
    PROJECT = 'project'
    # 他の種類も同様に追加

    @property
    def label(self):
        labels = {
            'skillset': 'スキルセット',
            'project': 'プロジェクト・制作物',
            # 他の種類のラベルも追加
        }
        return labels[self.value]

# ポートフォリオ投稿ページ
@app.route("/portfolio/create", methods=["GET", "POST"])
@login_required
def portfolio_create():
    if request.method == "POST":
        portfolio_type = request.form["portfolio_type"]
        title = request.form["title"]
        data = {
            "title": title,
            "type": portfolio_type,
            "user_id": current_user.id
        }

        # 種類ごとにデータを収集
        if portfolio_type == 'skillset':
            data["content"] = {
                "technical_skills": request.form.get("technical_skills"),
                "soft_skills": request.form.get("soft_skills"),
                "certifications": request.form.get("certifications")
            }
        elif portfolio_type == 'project':
            data["content"] = {
                "project_name": request.form.get("project_name"),
                "duration": request.form.get("duration"),
                "overview": request.form.get("overview"),
                "deliverables": request.form.get("deliverables"),
                "feedback": request.form.get("feedback")
            }
        # 他の種類も同様に処理

        # JSON形式で保存
        import json
        data["content"] = json.dumps(data["content"], ensure_ascii=False)

        # データベースに保存
        db.insert_data("portfolios", data)
        flash("ポートフォリオが投稿されました", "success")
        return redirect(url_for("mypage"))

    # テンプレートに種類を渡す
    portfolio_types = list(PortfolioType)
    return render_template("portfolio_create.html", portfolio_types=portfolio_types)

# カスタムフィルターを追加
@app.template_filter('from_json')
def from_json_filter(s):
    return json.loads(s)

if __name__ == "__main__":
    if not db.table_exists("users"):
        from db_init import initialize_db
        initialize_db()
    app.run(debug=True, port=8080)
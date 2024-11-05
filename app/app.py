from flask import Flask, render_template, redirect, url_for, request, flash, abort
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

import os
from enum import Enum
import json
from functools import wraps
from datetime import datetime

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
    user_data = db.select(
        "users",
        fields="id, username, password, role, full_name, student_number, seminar",
        conditions={"id": user_id},
        limit=1
    )
    if user_data:
        user = User(
            user_data[0]["id"],
            user_data[0]["username"],
            user_data[0]["password"],
            user_data[0]["role"],
            full_name=user_data[0].get("full_name"),
            student_number=user_data[0].get("student_number"),
            seminar=user_data[0].get("seminar")
        )
        return user
    return None

@app.route("/")
@login_required
def index():
    # ユーザーの役割に応じてリダイレクト先を変更
    if current_user.role == 'teacher':
        return redirect(url_for("teacher_dashboard"))
    else:
        return redirect(url_for("mypage"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # ユーザー認証 (パスワードはハッシュをチェック)
        user_data = db.select("users", fields="id, username, password, role", conditions={"username": username}, limit=1)
        if user_data and check_password_hash(user_data[0]["password"], password):
            user = User(user_data[0]["id"], user_data[0]["username"], user_data[0]["password"], user_data[0]["role"])
            login_user(user)
            # ユーザーの役割に応じてリダイレクト先を変更
            if user.role == 'teacher':
                return redirect(url_for("teacher_dashboard"))
            else:
                return redirect(url_for("mypage"))
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
        # このポートフォリオに対するフィードバックを取得
        feedbacks = db.execute_query("""
            SELECT feedbacks.*, users.full_name AS teacher_name
            FROM feedbacks
            JOIN users ON feedbacks.teacher_id = users.id
            WHERE feedbacks.portfolio_id = ?
        """, (portfolio["id"],), fetch="all")
        portfolio["feedbacks"] = feedbacks
    # マイページテンプレートに渡す
    return render_template("mypage.html", user=current_user, portfolios=portfolios)


# ここから追加: ユーザー登録用のエンドポイント
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]
        full_name = request.form["full_name"]
        student_number = request.form["student_number"]
        seminar = request.form.get("seminar", "")

        # ユーザーがすでに存在するか確認
        if db.data_exists("users", {"username": username}):
            flash("そのユーザー名は既に存在します。別のユーザー名を選んでください。", "danger")
            return redirect(url_for("register"))

        # パスワードをハッシュ化して保存
        hashed_password = generate_password_hash(password)
        db.insert_data("users", {
            "username": username,
            "password": hashed_password,
            "role": role,
            "full_name": full_name,
            "student_number": student_number,
            "seminar": seminar
        })
        flash("登録が完了しました！ログインしてください。", "success")
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

def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role != 'teacher':
            flash("Access denied.", "danger")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/teacher_dashboard")
@login_required
@teacher_required
def teacher_dashboard():
    # 全ての生徒を取得
    students = db.select("users", fields="id, username, full_name", conditions={"role": "student"})
    student_portfolios = {}
    for student in students:
        portfolios = db.select("portfolios", fields="id, title, type, content", conditions={"user_id": student["id"]})
        for portfolio in portfolios:
            try:
                portfolio_type = PortfolioType(portfolio["type"])
                portfolio["type_label"] = portfolio_type.label
            except ValueError:
                portfolio["type_label"] = "未知の種類"
        student_portfolios[student["id"]] = {"full_name": student["full_name"], "portfolios": portfolios}
    return render_template("teacher_dashboard.html", student_portfolios=student_portfolios)

# フィードバック送信エンドポイント
@app.route("/send_feedback", methods=["POST"])
@login_required
@teacher_required
def send_feedback():
    student_id = request.form["student_id"]
    portfolio_id = request.form["portfolio_id"]
    feedback_text = request.form["feedback"]

    data = {
        "teacher_id": current_user.id,
        "student_id": student_id,
        "portfolio_id": portfolio_id,
        "feedback": feedback_text
    }

    # フィードバックをデータベースに保存
    db.insert_data("feedbacks", data)
    flash("フィードバックを送信しました。", "success")
    return redirect(url_for('teacher_dashboard'))

# ポートフォリオ詳細ページ（掲示板付き）
@app.route("/portfolio/<int:portfolio_id>", methods=["GET", "POST"])
@login_required
def portfolio_detail(portfolio_id):
    # ポートフォリオを取得
    portfolios = db.select("portfolios", fields="id, user_id, title, type, content", conditions={"id": portfolio_id}, limit=1)
    if not portfolios:
        abort(404)
    portfolio = portfolios[0]

    # アクセス制御：生徒は自分のポートフォリオのみ、先生は全てのポートフォリオにアクセス可能
    if current_user.role == 'student' and portfolio['user_id'] != current_user.id:
        flash("アクセス権がありません。", "danger")
        return redirect(url_for('index'))

    # ポートフォリオの種類ラベルを取得
    try:
        portfolio_type = PortfolioType(portfolio["type"])
        portfolio["type_label"] = portfolio_type.label
    except ValueError:
        portfolio["type_label"] = "未知の種類"

    # ポートフォリオの内容をJSONから辞書に変換
    portfolio["content"] = json.loads(portfolio["content"])

    # コメントの取得
    comments = db.execute_query("""
        SELECT comments.*, users.full_name AS user_name
        FROM comments
        JOIN users ON comments.user_id = users.id
        WHERE comments.portfolio_id = ?
        ORDER BY comments.timestamp ASC
    """, (portfolio_id,), fetch="all")

    # コメントの投稿処理
    if request.method == "POST":
        content = request.form["content"]
        if content.strip() == "":
            flash("コメントを入力してください。", "danger")
        else:
            comment_data = {
                "portfolio_id": portfolio_id,
                "user_id": current_user.id,
                "content": content,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            db.insert_data("comments", comment_data)
            flash("コメントを投稿しました。", "success")
            return redirect(url_for("portfolio_detail", portfolio_id=portfolio_id))

    return render_template("portfolio_detail.html", portfolio=portfolio, comments=comments)

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        full_name = request.form["full_name"]
        student_number = request.form["student_number"]
        seminar = request.form["seminar"]

        # ユーザー情報の更新
        db.update_data(
            "users",
            updates={
                "full_name": full_name,
                "student_number": student_number,
                "seminar": seminar
            },
            conditions={"id": current_user.id}
        )

        # 現在のユーザー情報を更新
        current_user.full_name = full_name
        current_user.student_number = student_number
        current_user.seminar = seminar

        flash("プロフィールが更新されました。", "success")
        return redirect(url_for("profile"))

    return render_template("profile.html", user=current_user)
# カスタムフィルターを追加
@app.template_filter('from_json')
def from_json_filter(s):
    return json.loads(s)

if __name__ == "__main__":
    if not db.table_exists("users"):
        from db_init import initialize_db
        initialize_db()
    app.run(debug=True, port=8080)
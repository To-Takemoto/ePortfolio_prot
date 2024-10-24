from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

import os

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
    return f"Hello, {current_user.username}! You are logged in."

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
            return redirect(url_for("index"))
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

if __name__ == "__main__":
    if not db.table_exists("users"):
        from db_init import initialize_db
        initialize_db()
    app.run(debug=True, port=8080)

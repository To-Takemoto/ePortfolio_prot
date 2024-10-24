from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

import os

from models import User

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(24)

# Flask-Login の初期化
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"  # ログインが必要な場合、リダイレクトされるページ

# ユーザーデータの例
users = {
    "admin": User(1, "admin", "password"),
    "user": User(2, "user", "password123")
}

# ログインマネージャーがユーザーを取得する方法を定義
@login_manager.user_loader
def load_user(user_id):
    for user in users.values():
        if user.id == int(user_id):
            return user
    return None

@app.route("/")
@login_required  # ここでログインが必要なページを保護
def index():
    return f"Hello, {current_user.username}! You are logged in."

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # ユーザー認証
        user = users.get(username)
        if user and user.password == password:
            login_user(user)  # ユーザーをログイン状態にする
            flash("Login successful!", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid username or password", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/logout")
@login_required  # ログアウトもログイン済みユーザーのみ許可
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True, port = 8080)

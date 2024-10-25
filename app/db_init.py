from db_client import DBHandler
from werkzeug.security import generate_password_hash

def initialize_db():
    db = DBHandler("example.db")

    if not db.table_exists("users"):
        db.execute_query("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
        """)
        print("Table 'users' created successfully.")
    else:
        print("Table 'users' already exists.")

    # デフォルトのユーザーをハッシュ化して挿入
    default_users = [
        {"username": "admin", "password": generate_password_hash("password")},
        {"username": "user", "password": generate_password_hash("password123")}
    ]

    for user in default_users:
        if not db.data_exists("users", {"username": user["username"]}):
            db.insert_data("users", user)
            print(f"Inserted default user: {user['username']}")
        else:
            print(f"User {user['username']} already exists in the database.")

    # ポートフォリオテーブル
    if not db.table_exists("portfolios"):
        db.execute_query("""
        CREATE TABLE portfolios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """)
        print("Table 'portfolios' created successfully.")

if __name__ == "__main__":
    initialize_db()

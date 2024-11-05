from db_client import DBHandler
from werkzeug.security import generate_password_hash

def initialize_db():
    db = DBHandler("example.db")

    # ユーザーテーブルの作成または更新
    if not db.table_exists("users"):
        db.execute_query("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
        """)
        print("Table 'users' created successfully.")
    else:
        # 'role' カラムが存在しない場合は追加
        columns = db.get_metadata("users", info_type="columns")
        if 'role' not in columns:
            db.execute_query("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'student'")
            print("Added 'role' column to 'users' table.")

    # デフォルトのユーザーを挿入
    # default_users = [
    #     {"username": "admin", "password": generate_password_hash("password"), "role": "teacher"},
    #     {"username": "user", "password": generate_password_hash("password123"), "role": "student"}
    # ]

    # for user in default_users:
    #     if not db.data_exists("users", {"username": user["username"]}):
    #         db.insert_data("users", user)
    #         print(f"Inserted default user: {user['username']}")
    #     else:
    #         print(f"User {user['username']} already exists in the database.")

    # ポートフォリオテーブル
    if not db.table_exists("portfolios"):
        db.execute_query("""
        CREATE TABLE portfolios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """)
        print("Table 'portfolios' created successfully.")
    else:
        # 既存のテーブルにカラムを追加する場合
        columns = db.get_metadata("portfolios", info_type="columns")
        if 'type' not in columns:
            db.execute_query("ALTER TABLE portfolios ADD COLUMN type TEXT NOT NULL DEFAULT ''")
        if 'content' not in columns:
            db.execute_query("ALTER TABLE portfolios ADD COLUMN content TEXT NOT NULL DEFAULT ''")

    # フィードバックテーブルの作成
    if not db.table_exists("feedbacks"):
        db.execute_query("""
        CREATE TABLE feedbacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            portfolio_id INTEGER NOT NULL,
            feedback TEXT NOT NULL,
            FOREIGN KEY(teacher_id) REFERENCES users(id),
            FOREIGN KEY(student_id) REFERENCES users(id),
            FOREIGN KEY(portfolio_id) REFERENCES portfolios(id)
        )
        """)
        print("Table 'feedbacks' created successfully.")
    else:
        print("Table 'feedbacks' already exists.")

    # コメントテーブルの作成
    if not db.table_exists("comments"):
        db.execute_query("""
        CREATE TABLE comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            portfolio_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(portfolio_id) REFERENCES portfolios(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """)
        print("Table 'comments' created successfully.")
    else:
        print("Table 'comments' already exists.")

    columns = db.get_metadata("users", info_type="columns")
    if 'full_name' not in columns:
        db.execute_query("ALTER TABLE users ADD COLUMN full_name TEXT")
        print("Added 'full_name' column to 'users' table.")
    if 'student_number' not in columns:
        db.execute_query("ALTER TABLE users ADD COLUMN student_number TEXT")
        print("Added 'student_number' column to 'users' table.")
    if 'seminar' not in columns:
        db.execute_query("ALTER TABLE users ADD COLUMN seminar TEXT")
        print("Added 'seminar' column to 'users' table.")

if __name__ == "__main__":
    initialize_db()
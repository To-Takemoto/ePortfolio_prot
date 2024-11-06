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
            role TEXT NOT NULL,
            full_name TEXT,
            student_number TEXT,
            seminar TEXT
        )
        """)
        print("Table 'users' created successfully.")
    else:
        # 'full_name', 'student_number', 'seminar' カラムが存在しない場合は追加
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

    # ポートフォリオテーブルの作成または更新
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
            print("Added 'type' column to 'portfolios' table.")
        if 'content' not in columns:
            db.execute_query("ALTER TABLE portfolios ADD COLUMN content TEXT NOT NULL DEFAULT ''")
            print("Added 'content' column to 'portfolios' table.")

    # フィードバックテーブルの作成または更新
    if not db.table_exists("feedbacks"):
        db.execute_query("""
        CREATE TABLE feedbacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            portfolio_id INTEGER NOT NULL,
            feedback TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(teacher_id) REFERENCES users(id),
            FOREIGN KEY(student_id) REFERENCES users(id),
            FOREIGN KEY(portfolio_id) REFERENCES portfolios(id)
        )
        """)
        print("Table 'feedbacks' created successfully.")
    else:
        # 'timestamp' カラムが存在しない場合は追加
        columns = db.get_metadata("feedbacks", info_type="columns")
        if 'timestamp' not in columns:
            db.execute_query("ALTER TABLE feedbacks ADD COLUMN timestamp DATETIME DEFAULT CURRENT_TIMESTAMP")
            print("Added 'timestamp' column to 'feedbacks' table.")
        else:
            print("Table 'feedbacks' already exists with 'timestamp' column.")

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

    # 進捗テーブルの作成
    if not db.table_exists("progress_updates"):
        db.execute_query("""
        CREATE TABLE progress_updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            portfolio_id INTEGER NOT NULL,
            progress_number INTEGER NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(portfolio_id) REFERENCES portfolios(id)
        )
        """)
        print("Table 'progress_updates' created successfully.")
    else:
        print("Table 'progress_updates' already exists.")

if __name__ == "__main__":
    initialize_db()

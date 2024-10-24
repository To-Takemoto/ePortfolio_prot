import sqlite3
from contextlib import contextmanager

class DBHandler:
    def __init__(self, db_path: str):
        self._db_path = db_path

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        try:
            yield conn, cursor
            conn.commit()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            conn.rollback()
            raise
        except Exception as e:
            print(f"General error: {e}")
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

    def execute_query(self, query: str, params: tuple = (), fetch: str = None):
        """
        汎用的なクエリ実行関数。SELECT、INSERT、UPDATE、DELETEクエリを実行可能。
        fetch: 'one' -> fetchone() を使用, 'all' -> fetchall() を使用, None -> 結果を返さない
        """
        with self.get_connection() as (conn, cursor):
            cursor.execute(query, params)
            if fetch == "one":
                result = cursor.fetchone()
            elif fetch == "all":
                result = cursor.fetchall()
            else:
                result = None
        return result

    def data_exists(self, table_name: str, data: dict, check_columns: list = None) -> bool:
        """
        指定されたカラムのデータが存在するかを確認する。
        存在する場合は True、しない場合は False を返す。
        """
        check_columns = check_columns or list(data.keys())
        query = f"SELECT 1 FROM {table_name} WHERE " + " AND ".join([f"{col} = ?" for col in check_columns])
        values = tuple(data[col] for col in check_columns)
        result = self.execute_query(query, values, fetch="one")
        return result is not None

    def insert_data(self, table_name: str, data: dict, check_columns: list = None, hard: bool = False) -> int:
        """
        テーブルにデータを挿入する。オプションで既存データのチェックを行い、重複を避ける。
        """
        if not hard and self.data_exists(table_name, data, check_columns):
            print("Data already exists, skipping insert.")
            return None

        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

        with self.get_connection() as (conn, cursor):
            cursor.execute(query, tuple(data.values()))
            # 同じコネクションから最後に挿入された行のIDを取得
            last_row_id = cursor.lastrowid
            return last_row_id

    def select(self, table_name: str, fields: str = "*", conditions: dict = None, limit: int = None) -> list:
        """
        指定された条件とフィールドでデータを取得する汎用的な SELECT メソッド。
        """
        query = f"SELECT {fields} FROM {table_name}"
        params = ()
        if conditions:
            query += " WHERE " + " AND ".join([f"{col} = ?" for col in conditions.keys()])
            params = tuple(conditions.values())
        if limit:
            query += f" LIMIT {limit}"

        return self.execute_query(query, params, fetch="all")

    def update_data(self, table_name: str, updates: dict, conditions: dict) -> None:
        """
        特定のレコードを更新する。条件に基づいて複数のカラムを更新可能。
        """
        set_clause = ", ".join([f"{col} = ?" for col in updates.keys()])
        condition_clause = " AND ".join([f"{col} = ?" for col in conditions.keys()])
        query = f"UPDATE {table_name} SET {set_clause} WHERE {condition_clause}"
        params = tuple(updates.values()) + tuple(conditions.values())
        self.execute_query(query, params)

    def delete_data(self, table_name: str, conditions: dict) -> None:
        """
        特定の条件に基づいてデータを削除する。
        """
        condition_clause = " AND ".join([f"{col} = ?" for col in conditions.keys()])
        query = f"DELETE FROM {table_name} WHERE {condition_clause}"
        params = tuple(conditions.values())
        self.execute_query(query, params)

    def get_metadata(self, table_name: str, info_type: str = "columns") -> list:
        """
        テーブルのメタデータを取得する。カラム情報や行数など。
        info_type: 'columns' -> カラム情報, 'count' -> レコード数
        """
        if info_type == "columns":
            query = f"PRAGMA table_info({table_name})"
            columns_info = self.execute_query(query, fetch="all")
            return [col['name'] for col in columns_info]
        elif info_type == "count":
            query = f"SELECT COUNT(*) FROM {table_name}"
            count = self.execute_query(query, fetch="one")[0]
            return count

    def table_exists(self, table_name: str) -> bool:
        """
        データベースにテーブルが存在するかを確認する。
        """
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        return self.execute_query(query, (table_name,), fetch="one") is not None

if __name__ == "__main__":
    # DBHandler のインスタンス生成
    db = DBHandler("example.db")

    # テーブル作成
    if not db.table_exists("users"):
        db.execute_query("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")

    # データ挿入 (重複チェック付き)
    user_data = {"name": "Johnnnnn", "age": 32}
    user_id = db.insert_data("users", user_data, check_columns=["name"], hard=True)
    print(f"Inserted user ID: {user_id}")

    # レコード取得 (条件付き)
    record = db.select("users", fields="id, name", conditions={"id": user_id}, limit=1)
    print(f"Retrieved record: {record}")

    # データ更新
    db.update_data("users", updates={"age": 31}, conditions={"id": user_id})
    print("User age updated.")

    # レコード削除
    # db.delete_data("users", conditions={"id": user_id})
    # print("User deleted.")

    # メタデータ取得
    columns = db.get_metadata("users", info_type="columns")
    record_count = db.get_metadata("users", info_type="count")
    print(f"Columns: {columns}")
    print(f"Record count: {record_count}")

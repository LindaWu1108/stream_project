import os
from typing import Optional
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
USER = os.getenv('DB_USER')
PASSWORD = os.getenv('DB_PASSWORD')
DBNAME = os.getenv('DB_NAME')
HOST = os.getenv('DB_HOST')
PORT = os.getenv('DB_PORT')


class DB:
    connection_pool = pool.SimpleConnectionPool(
        1, 100,  # 最小和最大連線數
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT,
        dbname=DBNAME
    )

    @staticmethod
    def connect():
        return DB.connection_pool.getconn()

    @staticmethod
    def release(connection):
        DB.connection_pool.putconn(connection)

    @staticmethod
    def execute_input(sql, input):
        if not isinstance(input, (tuple, list)):
            raise TypeError(f"Input should be a tuple or list, got: {type(input).__name__}")
        connection = DB.connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, input)
                connection.commit()
        except psycopg2.Error as e:
            print(f"Error executing SQL: {e}")
            connection.rollback()
            raise e
        finally:
            DB.release(connection)

    @staticmethod
    def execute(sql):
        connection = DB.connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql)
                connection.commit()
        except psycopg2.Error as e:
            print(f"Error executing SQL: {e}")
            connection.rollback()
            raise e
        finally:
            DB.release(connection)

    @staticmethod
    def fetchall(sql, input=None):
        connection = DB.connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, input)
                return cursor.fetchall()
        except psycopg2.Error as e:
            print(f"Error fetching data: {e}")
            raise e
        finally:
            DB.release(connection)

    @staticmethod
    def fetchone(sql, input=None):
        connection = DB.connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, input)
                return cursor.fetchone()
        except psycopg2.Error as e:
            print(f"Error fetching data: {e}")
            raise e
        finally:
            DB.release(connection)


# =========================================================
# 1. 帳號 (Account) 與 訂閱 (Subscription / Plan)
# =========================================================
class Account:
    @staticmethod
    def get_by_email(email):
        sql = "SELECT accountId, email, password, regDate FROM Account WHERE email = %s"
        return DB.fetchone(sql, (email,))

    @staticmethod
    def get_by_id(account_id):
        sql = "SELECT accountId, email, password, regDate FROM Account WHERE accountId = %s"
        return DB.fetchone(sql, (account_id,))

    @staticmethod
    def get_all_emails():
        sql = "SELECT email FROM Account"
        return DB.fetchall(sql)

    @staticmethod
    def next_account_id():
        sql = "SELECT accountId FROM Account ORDER BY accountId DESC LIMIT 1"
        row = DB.fetchone(sql)
        if not row:
            return 'A001'
        num = int(row[0][1:]) + 1
        return f'A{num:03d}'

    @staticmethod
    def create_account(account_id, email, password):
        sql = "INSERT INTO Account (accountId, email, password, regDate) VALUES (%s, %s, %s, CURRENT_DATE)"
        DB.execute_input(sql, (account_id, email, password))


class Plan:
    @staticmethod
    def get_all():
        sql = "SELECT planId, planName, price, maxScreens FROM Plan ORDER BY price ASC"
        return DB.fetchall(sql)

    @staticmethod
    def get_by_id(plan_id):
        sql = "SELECT planId, planName, price, maxScreens FROM Plan WHERE planId = %s"
        return DB.fetchone(sql, (plan_id,))


class Subscription:
    @staticmethod
    def get_by_account(account_id):
        sql = """
            SELECT s.subId, TO_CHAR(s.payDate, 'YYYY-MM-DD HH24:MI:SS'), s.amount, s.endDate, s.status,
                   p.planId, p.planName, p.price, p.maxScreens
            FROM Subscription s
            JOIN Plan p ON s.planId = p.planId
            WHERE s.accountId = %s
            ORDER BY s.payDate DESC
        """
        return DB.fetchall(sql, (account_id,))

    @staticmethod
    def get_all_subscriptions():
        sql = """
            SELECT s.subId, a.email, p.planName, s.amount, TO_CHAR(s.payDate, 'YYYY-MM-DD HH24:MI:SS'), s.endDate, s.status
            FROM Subscription s
            JOIN Account a ON s.accountId = a.accountId
            JOIN Plan p ON s.planId = p.planId
            WHERE a.email NOT LIKE 'admin%%'
            ORDER BY s.payDate DESC, s.subId DESC
        """
        return DB.fetchall(sql)

    @staticmethod
    def next_sub_id():
        sql = "SELECT subId FROM Subscription ORDER BY subId DESC LIMIT 1"
        row = DB.fetchone(sql)
        if not row:
            return 'S001'
        num = int(row[0][1:]) + 1
        return f'S{num:03d}'

    @staticmethod
    def create_subscription(account_id, plan_id):
        plan = Plan.get_by_id(plan_id)
        amount = plan[2] if plan else 270
        sub_id = Subscription.next_sub_id()
        # 將該帳號原先「使用中」的訂閱狀態更新為「已更換」
        DB.execute_input(
            "UPDATE Subscription SET status = '已結束' WHERE accountId = %s AND status = '使用中'",
            (account_id,)
        )
        sql = """
            INSERT INTO Subscription (subId, payDate, amount, endDate, status, accountId, planId)
            VALUES (%s, CURRENT_TIMESTAMP, %s, CURRENT_DATE + INTERVAL '30 days', '使用中', %s, %s)
        """
        DB.execute_input(sql, (sub_id, amount, account_id, plan_id))


# =========================================================
# 2. 使用者 Profile (弱實體：依附於 Account)
# =========================================================
class Profile:
    @staticmethod
    def get_by_account(account_id):
        sql = "SELECT accountId, profileNo, profileName, isKid FROM Profile WHERE accountId = %s ORDER BY profileNo ASC"
        return DB.fetchall(sql, (account_id,))

    @staticmethod
    def get_one(account_id, profile_no):
        sql = "SELECT accountId, profileNo, profileName, isKid FROM Profile WHERE accountId = %s AND profileNo = %s"
        return DB.fetchone(sql, (account_id, profile_no))

    @staticmethod
    def create_profile(account_id, profile_name, is_kid=False):
        sql_max = "SELECT COALESCE(MAX(profileNo), 0) + 1 FROM Profile WHERE accountId = %s"
        next_no = DB.fetchone(sql_max, (account_id,))[0]
        sql = "INSERT INTO Profile (accountId, profileNo, profileName, isKid) VALUES (%s, %s, %s, %s)"
        DB.execute_input(sql, (account_id, next_no, profile_name, is_kid))
        return next_no

    @staticmethod
    def delete_profile(account_id, profile_no):
        sql = "DELETE FROM Profile WHERE accountId = %s AND profileNo = %s"
        DB.execute_input(sql, (account_id, int(profile_no)))


# =========================================================
# 3. 影片 (Movie)、類別 (Genre) 與 隸屬關係 (Belong)
# =========================================================
class Genre:
    @staticmethod
    def get_all():
        sql = "SELECT genreId, genreName, description FROM Genre ORDER BY genreId ASC"
        return DB.fetchall(sql)


class Movie:
    @staticmethod
    def count():
        sql = "SELECT COUNT(*) FROM Movie"
        return DB.fetchone(sql)

    @staticmethod
    def get_all(is_kid=False, genre_id=None, keyword=None):
        conditions = []
        params = []

        if is_kid:
            # 兒童模式只顯示普遍級與保護級
            conditions.append("m.rating IN ('普遍級', '保護級')")

        if genre_id:
            conditions.append("EXISTS (SELECT 1 FROM Belong b2 WHERE b2.movieId = m.movieId AND b2.genreId = %s)")
            params.append(genre_id)

        if keyword:
            conditions.append("m.title ILIKE %s")
            params.append(f"%{keyword}%")

        where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        sql = f"""
            SELECT m.movieId, m.title, m.duration, m.rating,
                   COALESCE(STRING_AGG(DISTINCT g.genreName, ' / '), '未分類') AS genres,
                   ROUND(AVG(w.rating), 1) AS avg_rating
            FROM Movie m
            LEFT JOIN Belong b ON m.movieId = b.movieId
            LEFT JOIN Genre g ON b.genreId = g.genreId
            LEFT JOIN Watch w ON m.movieId = w.movieId
            {where_clause}
            GROUP BY m.movieId, m.title, m.duration, m.rating
            ORDER BY m.movieId ASC
        """
        return DB.fetchall(sql, tuple(params) if params else None)

    @staticmethod
    def get_by_id(movie_id):
        sql = """
            SELECT m.movieId, m.title, m.duration, m.rating,
                   COALESCE(STRING_AGG(DISTINCT g.genreName, ' / '), '未分類') AS genres,
                   ROUND(AVG(w.rating), 1) AS avg_rating
            FROM Movie m
            LEFT JOIN Belong b ON m.movieId = b.movieId
            LEFT JOIN Genre g ON b.genreId = g.genreId
            LEFT JOIN Watch w ON m.movieId = w.movieId
            WHERE m.movieId = %s
            GROUP BY m.movieId, m.title, m.duration, m.rating
        """
        return DB.fetchone(sql, (movie_id,))

    @staticmethod
    def get_movie_genre_ids(movie_id):
        sql = "SELECT genreId FROM Belong WHERE movieId = %s"
        return [r[0] for r in DB.fetchall(sql, (movie_id,))]

    @staticmethod
    def next_movie_id():
        sql = "SELECT movieId FROM Movie ORDER BY movieId DESC LIMIT 1"
        row = DB.fetchone(sql)
        if not row:
            return 'M001'
        num = int(row[0][1:]) + 1
        return f'M{num:03d}'

    @staticmethod
    def add_movie(movie_id, title, duration, rating, genre_ids):
        sql = "INSERT INTO Movie (movieId, title, duration, rating) VALUES (%s, %s, %s, %s)"
        DB.execute_input(sql, (movie_id, title, int(duration), rating))
        for gid in genre_ids:
            DB.execute_input("INSERT INTO Belong (movieId, genreId) VALUES (%s, %s) ON CONFLICT DO NOTHING", (movie_id, gid))

    @staticmethod
    def update_movie(movie_id, title, duration, rating, genre_ids):
        sql = "UPDATE Movie SET title = %s, duration = %s, rating = %s WHERE movieId = %s"
        DB.execute_input(sql, (title, int(duration), rating, movie_id))
        DB.execute_input("DELETE FROM Belong WHERE movieId = %s", (movie_id,))
        for gid in genre_ids:
            DB.execute_input("INSERT INTO Belong (movieId, genreId) VALUES (%s, %s) ON CONFLICT DO NOTHING", (movie_id, gid))

    @staticmethod
    def delete_movie(movie_id):
        DB.execute_input("DELETE FROM Movie WHERE movieId = %s", (movie_id,))


# =========================================================
# 4. 觀看紀錄 (Watch) 與 多值觀看時間點 (Watch_Time)
# =========================================================
class Watch:
    @staticmethod
    def get_by_profile(account_id, profile_no):
        sql = """
            SELECT w.movieId, m.title, m.duration, m.rating AS age_rating,
                   w.progress, w.rating AS user_rating,
                   COALESCE(STRING_AGG(TO_CHAR(wt.watchTime, 'YYYY-MM-DD HH24:MI:SS'), '、' ORDER BY wt.watchTime DESC), '尚無觀看時間紀錄') AS watch_times,
                   COUNT(wt.watchTime) AS watch_count
            FROM Watch w
            JOIN Movie m ON w.movieId = m.movieId
            LEFT JOIN Watch_Time wt
              ON w.accountId = wt.accountId
             AND w.profileNo = wt.profileNo
             AND w.movieId = wt.movieId
            WHERE w.accountId = %s AND w.profileNo = %s
            GROUP BY w.movieId, m.title, m.duration, m.rating, w.progress, w.rating
            ORDER BY MAX(wt.watchTime) DESC NULLS LAST, w.movieId ASC
        """
        return DB.fetchall(sql, (account_id, profile_no))

    @staticmethod
    def get_one(account_id, profile_no, movie_id):
        sql = """
            SELECT progress, rating
            FROM Watch
            WHERE accountId = %s AND profileNo = %s AND movieId = %s
        """
        return DB.fetchone(sql, (account_id, profile_no, movie_id))

    @staticmethod
    def get_watch_times(account_id, profile_no, movie_id):
        sql = """
            SELECT TO_CHAR(watchTime, 'YYYY-MM-DD HH24:MI:SS')
            FROM Watch_Time
            WHERE accountId = %s AND profileNo = %s AND movieId = %s
            ORDER BY watchTime DESC
        """
        return [r[0] for r in DB.fetchall(sql, (account_id, profile_no, movie_id))]

    @staticmethod
    def record_watch(account_id, profile_no, movie_id, progress, rating):
        sql_watch = """
            INSERT INTO Watch (accountId, profileNo, movieId, progress, rating)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (accountId, profileNo, movieId)
            DO UPDATE SET progress = EXCLUDED.progress, rating = EXCLUDED.rating
        """
        DB.execute_input(sql_watch, (account_id, int(profile_no), movie_id, int(progress), int(rating) if rating else None))

        # 自動寫入當下觀看時間點 (CURRENT_TIMESTAMP) 至多值屬性表 Watch_Time
        sql_wt = """
            INSERT INTO Watch_Time (accountId, profileNo, movieId, watchTime)
            VALUES (%s, %s, %s, DATE_TRUNC('second', CURRENT_TIMESTAMP))
            ON CONFLICT DO NOTHING
        """
        DB.execute_input(sql_wt, (account_id, int(profile_no), movie_id))

    @staticmethod
    def delete_watch(account_id, profile_no, movie_id):
        sql = "DELETE FROM Watch WHERE accountId = %s AND profileNo = %s AND movieId = %s"
        DB.execute_input(sql, (account_id, int(profile_no), movie_id))

    @staticmethod
    def get_all_watch_logs():
        sql = """
            SELECT a.email, p.profileName, m.title, w.progress, w.rating,
                   COALESCE(STRING_AGG(TO_CHAR(wt.watchTime, 'YYYY-MM-DD HH24:MI'), '、' ORDER BY wt.watchTime DESC), '無') AS watch_timestamps
            FROM Watch w
            JOIN Account a ON w.accountId = a.accountId
            JOIN Profile p ON w.accountId = p.accountId AND w.profileNo = p.profileNo
            JOIN Movie m ON w.movieId = m.movieId
            LEFT JOIN Watch_Time wt
              ON w.accountId = wt.accountId AND w.profileNo = wt.profileNo AND w.movieId = wt.movieId
            GROUP BY a.email, p.profileName, m.title, w.progress, w.rating
            ORDER BY MAX(wt.watchTime) DESC NULLS LAST, a.email ASC
        """
        return DB.fetchall(sql)


# =========================================================
# 5. 後台數據分析 (Analysis)
# =========================================================
class Analysis:
    @staticmethod
    def month_price(i):
        sql = """
            SELECT EXTRACT(MONTH FROM payDate), COALESCE(SUM(amount), 0)
            FROM Subscription
            WHERE EXTRACT(MONTH FROM payDate) = %s
            GROUP BY EXTRACT(MONTH FROM payDate)
        """
        return DB.fetchall(sql, (i,))

    @staticmethod
    def month_count(i):
        sql = """
            SELECT EXTRACT(MONTH FROM payDate), COUNT(subId)
            FROM Subscription
            WHERE EXTRACT(MONTH FROM payDate) = %s
            GROUP BY EXTRACT(MONTH FROM payDate)
        """
        return DB.fetchall(sql, (i,))

    @staticmethod
    def category_sale():
        # 各類別影片被觀看的總次數分析
        sql = """
            SELECT COUNT(w.movieId), g.genreName
            FROM Genre g
            LEFT JOIN Belong b ON g.genreId = b.genreId
            LEFT JOIN Watch w ON b.movieId = w.movieId
            GROUP BY g.genreId, g.genreName
            ORDER BY COUNT(w.movieId) DESC
        """
        return DB.fetchall(sql)

    @staticmethod
    def member_sale():
        # 各一般會員帳號累積訂閱消費總額排行（排除管理員帳號）
        sql = """
            SELECT COALESCE(SUM(s.amount), 0), a.accountId, a.email
            FROM Account a
            LEFT JOIN Subscription s ON a.accountId = s.accountId
            WHERE a.email NOT LIKE 'admin%%'
            GROUP BY a.accountId, a.email
            ORDER BY COALESCE(SUM(s.amount), 0) DESC
        """
        return DB.fetchall(sql)

    @staticmethod
    def member_sale_count():
        # 各一般會員帳號總觀看影片數排行（排除管理員帳號）
        sql = """
            SELECT COUNT(w.movieId), a.accountId, a.email
            FROM Account a
            LEFT JOIN Watch w ON a.accountId = w.accountId
            WHERE a.email NOT LIKE 'admin%%'
            GROUP BY a.accountId, a.email
            ORDER BY COALESCE( (SELECT SUM(s2.amount) FROM Subscription s2 WHERE s2.accountId = a.accountId), 0) DESC
        """
        return DB.fetchall(sql)

import sqlite3 as sq

async def db_start():
    db = sq.connect("message_db")
    cur = db.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS user_data (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                quarry_date TEXT, 
                question_text TEXT NULL,
                question_status TEXT CHECK(question_status IN ('not sent','sent','under processing')) NOT NULL DEFAULT "not sent",
                reply_text TEXT NULL
                )""")
    db.commit()

async def add_message(message_text, user_id):
    db = sq.connect("message_db")
    cur = db.cursor()
    message_text = message_text.get("question")
    cur.execute("INSERT INTO user_data (question_text, user_id, quarry_date) VALUES(?, ?, datetime('now', '+3 hours'))", (message_text, user_id))
    db.commit()

async def extract_sql_data():
    db = sq.connect("message_db")
    cur = db.cursor()
    result = cur.execute("SELECT question_text FROM user_data WHERE id = 1").fetchone()
    return result


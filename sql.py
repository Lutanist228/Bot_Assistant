import sqlite3 as sq

async def db_start():
    db = sq.connect("message_db")
    cur = db.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS gpt_db (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                quarry_date TEXT, 
                question_text TEXT NULL,
                question_status TEXT CHECK(question_status IN ('not sent','sent','under processing')) NOT NULL DEFAULT "not sent",
                reply_text TEXT NULL,
                reply_received TEXT NOT NULL DEFAULT 'FALSE'
                )""")
    db.commit()

    db = sq.connect("message_db")
    cur = db.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS fuzzy_db (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                quarry_date TEXT, 
                question_text TEXT NULL,
                reply_text TEXT NULL,
                similarity_rate INTEGER DEFAULT 0,
                reply_received TEXT NOT NULL DEFAULT 'FALSE'
                )""")
    db.commit()

async def sql_add_extract_data(data_base_type, message_text, user_id):
    db = sq.connect("message_db")
    cur = db.cursor()

    if isinstance(message_text, str) == False:
        message_text = message_text.get("question")

    cur.execute(f"INSERT INTO {data_base_type} (question_text, user_id, quarry_date) VALUES(?, ?, datetime('now', '+3 hours'))", (message_text, user_id))
    db.commit()

    result = cur.execute(f"SELECT id FROM {data_base_type} WHERE question_text = ?", (message_text,)).fetchone()
    db.commit()
    return result

async def sql_update_data(data_base_type: str, primary_key_value: int, bot_reply: str, reply_status: str, similarity_rate = 0, question_status = "under processing"):
    db = sq.connect("message_db")
    cur = db.cursor()

    bot_reply = bot_reply.lower().strip()

    if data_base_type == "gpt_db":
        cur.execute("""UPDATE fuzzy_db SET similarity_rate = ?, reply_text = ?, reply_received = ? WHERE id = ?""",
            (similarity_rate, bot_reply, reply_status, primary_key_value))        
        db.commit()        
    elif data_base_type == "fuzzy_db":
        cur.execute("""UPDATE fuzzy_db SET similarity_rate = ?, reply_text = ?, reply_received = ? WHERE id = ?""",
            (similarity_rate, bot_reply, reply_status, primary_key_value))
        db.commit()



         


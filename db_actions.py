import aiosqlite

class Database:
    def __init__(self):
        self.connection = None
        self.create_table()
        self.create_connection()

    async def create_connection(self):
        # Создание соединения с базой данных
        self.connection = await aiosqlite.connect('database.db')

    async def create_table(self):
        # Создание таблицы в базе данных, если она еще не была создана
        async with aiosqlite.connect('database.db') as conn:
            await conn.execute('''CREATE TABLE IF NOT EXISTS admin_questions
                               (id INTEGER PRIMARY KEY AUTOINCREMENT,
                               user_id INTEGER,
                               user_name TEXT,
                               message_id INTEGER,
                               question TEXT,
                               gpt_answer TEXT DEFAULT NULL,
                               answer TEXT DEFAULT NULL,
                               moder_id INTEGER,
                               moder_name TEXT,
                               chat_type TEXT,
                               supergroup_id INTEGER)''')
            
            await conn.execute("""CREATE TABLE IF NOT EXISTS fuzzy_db (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                message_id INTEGER,
                quarry_date TEXT, 
                question_text TEXT NULL,
                reply_text TEXT NULL,
                similarity_rate INTEGER DEFAULT 0,
                reply_received TEXT NOT NULL DEFAULT 'FALSE'
                )""")
            
    async def create_infromation_about_moder(self):
        async with aiosqlite.connect('database.db') as conn:
            await conn.execute('''CREATE TABLE IF NOT EXISTS moder_information
                                           (id INTEGER PRIMARY KEY AUTOINCREMENT,
                                           moder_id INTEGER,
                                           moder_name TEXT,
                                           role TEXT,
                                           number_of_answered_questions INTEGER)''')
            await conn.commit()
            async with conn.execute('SELECT moder_id FROM moder_information') as cursor:
                check = await cursor.fetchall()
            if len(check) == 0:
                moder_infromation = {'Егор': 869012176,
                            'Александр': 6231172367}
                for moder_name, moder_id in moder_infromation.items():
                    await conn.execute('INSERT INTO moder_information (moder_id, moder_name, role) VALUES (?, ?, ?)', 
                                       (moder_id, moder_name, 'Owner'))
                await conn.commit()
                       
    async def add_question(self, user_id: int, user_name: str, message_id: int, question: str, chat_type: str, supergroup_id: int = None, data_base_type: str = "admin_questions"):
        if self.connection is None:
            await self.create_connection()
        if data_base_type == "admin_questions":    
            async with self.connection.execute('INSERT INTO admin_questions (user_id, user_name, message_id, question, chat_type, supergroup_id) VALUES (?, ?, ?, ?, ?, ?)', 
                                               (user_id, user_name, message_id, question, chat_type, supergroup_id)) as cursor:
                    question_id = cursor.lastrowid
                    await self.connection.commit()
        elif data_base_type == "fuzzy_db":
            async with self.connection.execute(f"INSERT INTO fuzzy_db (question_text, user_id, message_id, quarry_date) VALUES(?, ?, ?, datetime('now', '+3 hours'))", 
                                               (question, user_id, message_id)) as cursor:
                question_id = cursor.lastrowid
                await self.connection.commit()
        return question_id
    
    async def get_unaswered_questions(self):
        if self.connection is None:
            await self.create_connection()
        async with self.connection.execute('SELECT * FROM admin_questions WHERE answer IS NULL') as cursor:
            rows = await cursor.fetchall()
            return rows
        
    async def get_list_of_unaswered_questions(self):
        if self.connection is None:
            await self.create_connection()
        async with self.connection.execute('SELECT * FROM admin_questions WHERE answer IS NULL ORDER BY id ASC') as cursor:
            rows = await cursor.fetchall()
            return rows

    async def update_question_id(self, question_id: int, answer: str, moder_id: int, moder_name: str):
        async with self.connection.execute('''UPDATE admin_questions SET answer = ?, 
                                           moder_id = ?, 
                                           moder_name = ? 
                                           WHERE id = ?''', (answer, moder_id,
                                                             moder_name, question_id)):
            await self.connection.commit()

    async def update_gpt_answer(self, question_id: int, answer: str):
        if self.connection is None:
            await self.create_connection()
        async with self.connection.execute('''UPDATE admin_questions SET gpt_answer = ?
                                        WHERE id = ?''', (answer, question_id)):
            await self.connection.commit()
            
        # Нет смысла траты на эти вопросы токенов
        # else:
        #     if self.connection is None:
        #         await self.create_connection()
        #     async with self.connection.execute('''UPDATE fuzzy_db SET gpt_answer = ?
        #                                     WHERE id = ?''', (answer, question_id)):
        #         await self.connection.commit()

    async def get_user_id(self, question_id):
        if self.connection is None:
            await self.create_connection()
        async with self.connection.execute('SELECT * FROM admin_questions WHERE id = ?', (question_id,)) as cursor:
            rows = await cursor.fetchall()
            result = rows[0][1]
            return result
    
    async def get_message_id(self, question_id):
        if self.connection is None:
            await self.create_connection()
        async with self.connection.execute('SELECT * FROM admin_questions WHERE id = ?', (question_id,)) as cursor:
            rows = await cursor.fetchall()
            result = rows[0][3]
            return result

    async def get_chat_type_and_id(self, question_id):
        if self.connection is None:
            await self.create_connection()
        async with self.connection.execute('SELECT * FROM admin_questions WHERE id = ?', (question_id,)) as cursor:
            rows = await cursor.fetchall()
            chat_type = rows[0][9]
            chat_id = rows[0][10]
            return chat_type, chat_id
        
    async def get_all_questions(self):
        if self.connection is None:
            await self.create_connection()
        async with self.connection.execute('SELECT * FROM admin_questions ORDER BY id ASC') as cursor:
            rows = await cursor.fetchall()
            return rows
        
    async def get_question(self, question_id: int, data_base_type: str = "admin_questions"):
        if data_base_type == "admin_questions":
            async with self.connection.execute('SELECT user_id, question, answer FROM admin_questions WHERE id = ?', (question_id,)) as cursor:
                row = await cursor.fetchone()
                if row is not None:
                    user_id, question, answer = row
                    return {'user_id': user_id, 'question': question, 'answer': answer}
                else:
                    return None
        else:
            async with self.connection.execute('SELECT user_id, question_text, reply_text FROM fuzzy_db WHERE id = ?', (question_id,)) as cursor:
                row = await cursor.fetchone()
                if row is not None:
                    user_id, question, answer = row
                    return {'user_id': user_id, 'question_text': question, 'reply_text': answer}
                else:
                    return None
            
    async def delete_question(self, question_id: int):
        async with self.connection.execute('DELETE FROM admin_questions WHERE id = ?', (question_id,)):
            await self.connection.execute('DELETE FROM sqlite_sequence WHERE name="questions"')
            await self.connection.commit()

    async def clear_questions(self):
        if self.connection is None:
            await self.create_connection()
        async with self.connection.execute('DELETE FROM admin_questions'):
            await self.connection.execute('DELETE FROM sqlite_sequence WHERE name="questions"')
            await self.connection.commit()

    async def get_number_of_unanswered_questions(self):
        if self.connection is None:
            await self.create_connection()
        async with self.connection.execute('SELECT * FROM admin_questions WHERE answer IS NULL') as cursor:
            rows = await cursor.fetchall()
            return len(rows)

    async def get_fuzzy_id(self, user_id: int):
        if self.connection is None:
            await self.create_connection()
        async with self.connection.execute('SELECT question_text FROM fuzzy_db WHERE user_id = ? ORDER BY id DESC LIMIT 1', (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row

    async def update_fuzzy_data(self, primary_key_value: int, bot_reply: str, reply_status: str, similarity_rate = 0):
        if self.connection is None:
            await self.create_connection()

        bot_reply = bot_reply.lower().strip()
        async with self.connection.execute("""UPDATE fuzzy_db SET similarity_rate = ?, reply_text = ?, reply_received = ? WHERE id = ?""",
                (similarity_rate, bot_reply, reply_status, primary_key_value)):
            await self.connection.commit()  

    async def get_moder(self):
        if self.connection is None:
            await self.create_connection()
        async with self.connection.execute('SELECT moder_id, role FROM moder_information') as cursor:
            result = await cursor.fetchall()
            return result
        
    async def add_new_moder(self, moder_id: int, moder_name: str):
        if self.connection is None:
            await self.create_connection()
        async with self.connection.execute('INSERT INTO moder_information (moder_id, moder_name) VALUES (?, ?)', 
                                           (moder_id, moder_name)):
            await self.connection.commit()

    async def delete_moder(self, moder_id: int):
        if self.connection is None:
            await self.create_connection()
        async with self.connection.execute('DELETE FROM moder_information WHERE moder_id = ?', (moder_id,)):
            await self.connection.commit()
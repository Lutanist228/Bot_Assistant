import aiosqlite

from additional_functions import process_connection_to_excel

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
                               quarry_date REAL NULL,
                               gpt_answer TEXT DEFAULT NULL,
                               answer TEXT DEFAULT NULL,
                               moder_answer_date REAL NULL,
                               moder_id INTEGER,
                               moder_name TEXT,
                               chat_type TEXT,
                               supergroup_id INTEGER,
                               question_picture INTEGER)''')
            
            await conn.execute("""CREATE TABLE IF NOT EXISTS fuzzy_db (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                message_id INTEGER,
                quarry_date REAL NULL, 
                question_text TEXT NULL,
                reply_text TEXT NULL,
                similarity_rate INTEGER DEFAULT 0,
                reply_received TEXT NOT NULL DEFAULT 'FALSE'
                )""")
            
            await conn.execute('''CREATE TABLE IF NOT EXISTS checked_ids (
                               id INTEGER PRIMARY KEY AUTOINCREMENT,
                               user_id INTEGER,
                               user_name TEXT)''')
            
            await conn.execute('''CREATE TABLE IF NOT EXISTS suggestions (
                               id INTEGER PRIMARY KEY AUTOINCREMENT,
                               user_id INTEGER,
                               user_name CHAR,
                               suggestion TEXT,
                               picture_id TEXT)''')
            
            await conn.execute('''CREATE TABLE IF NOT EXISTS projects (
                               id INTEGER PRIMARY KEY AUTOINCREMENT,
                               team TEXT,
                               project TEXT,
                               project_tag TEXT)''')
            
            await conn.execute('''CREATE TABLE IF NOT EXISTS analiz (
                               id INTEGER PRIMARY KEY AUTOINCREMENT,
                               user_id INTEGER,
                               user_name TEXT)''')
            
            await conn.execute('''CREATE TABLE IF NOT EXISTS razrabotka (
                               id INTEGER PRIMARY KEY AUTOINCREMENT,
                               user_id INTEGER,
                               user_name TEXT)''')
            
            await conn.execute('''CREATE TABLE IF NOT EXISTS vr (
                               id INTEGER PRIMARY KEY AUTOINCREMENT,
                               user_id INTEGER,
                               user_name TEXT)''')
            
            await conn.execute('''CREATE TABLE IF NOT EXISTS devops (
                               id INTEGER PRIMARY KEY AUTOINCREMENT,
                               user_id INTEGER,
                               user_name TEXT)''')
            
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
                moder_infromation = {'Егор': 869012176} 
                                    #  'Александр': 6231172367}
                for moder_name, moder_id in moder_infromation.items():
                    await conn.execute('INSERT INTO moder_information (moder_id, moder_name, role) VALUES (?, ?, ?)', 
                                       (moder_id, moder_name, 'Owner'))
                await conn.commit()
                       
    async def add_question(self, user_id: int, user_name: str, message_id: int, question: str, chat_type: str, supergroup_id: int = None, photo_id = None, data_base_type: str = "admin_questions"):
        if self.connection is None:
            await self.create_connection()
        if data_base_type == "admin_questions":    
            async with self.connection.execute('INSERT INTO admin_questions (user_id, user_name, message_id, question, chat_type, supergroup_id, quarry_date, question_picture) VALUES (?, ?, ?, ?, ?, ?, datetime(julianday("now", "+3 hours")), ?)', 
                                               (user_id, user_name, message_id, question, chat_type, supergroup_id, photo_id)) as cursor:
                    question_id = cursor.lastrowid
                    await self.connection.commit()
        elif data_base_type == "fuzzy_db":
            async with self.connection.execute("INSERT INTO fuzzy_db (question_text, user_id, message_id, quarry_date) VALUES(?, ?, ?, datetime(julianday('now', '+3 hours')))", 
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
                                           moder_name = ?,
                                           moder_answer_date = datetime(julianday("now", "+3 hours"))
                                           WHERE id = ?''', (answer, moder_id,
                                                             moder_name, question_id)):
            await self.connection.commit()

    async def update_gpt_answer(self, question_id: int, answer: str):
        if self.connection is None:
            await self.create_connection()
        async with self.connection.execute('''UPDATE admin_questions SET gpt_answer = ?
                                        WHERE id = ?''', (answer, question_id)):
            await self.connection.commit()

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
            chat_type = rows[0][11]
            chat_id = rows[0][12]
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
        
    async def add_new_moder(self, moder_id: int, moder_name: str, role: str):
        if self.connection is None:
            await self.create_connection()
        async with self.connection.execute('INSERT INTO moder_information (moder_id, moder_name, role) VALUES (?, ?, ?)', 
                                           (moder_id, moder_name, role)):
            await self.connection.commit()

    async def delete_moder(self, moder_id: int):
        if self.connection is None:
            await self.create_connection()
        async with self.connection.execute('DELETE FROM moder_information WHERE moder_id = ?', (moder_id,)):
            await self.connection.commit()

    async def check_question(self, question_id: int):
        if self.connection is None:
            await self.create_connection()
        async with self.connection.execute('SELECT answer FROM admin_questions WHERE id = ?', (question_id,)) as cursor:
            result = await cursor.fetchone()
            return result
        
    async def check_history(self, user_id: int):
        if self.connection is None:
            await self.create_connection()
        async with self.connection.execute('SELECT * FROM admin_questions WHERE user_id = ? ORDER BY quarry_date', (user_id, )) as cursor:
            result = await cursor.fetchall()
            return result
        
    async def get_ids_for_announcement(self):
        if self.connection is None:
            await self.create_connection()
        async with self.connection.execute('SELECT user_id FROM admin_questions') as cursor:
            result_1 = await cursor.fetchall()
        async with self.connection.execute('SELECT user_id FROM fuzzy_db') as cursor:
            result_2 = await cursor.fetchall()
        return result_1 + result_2
    
    async def add_checked_id(self, user_id: int, user_name: str):
        if self.connection is None:
            await self.create_connection()
        async with self.connection.execute('INSERT INTO checked_ids (user_id, user_name) VALUES (?, ?)', (user_id, user_name)):
            await self.connection.commit()

    async def get_checked_ids(self):
        if self.connection is None:
            await self.create_connection()
        async with self.connection.execute('SELECT user_id FROM checked_ids') as cursor:
            result = await cursor.fetchall()  
            return result
        
    async def add_suggestion(self, user_id: int, user_name: str, suggestion: str, picture_id: str = None):
        if self.connection is None:
            await self.create_connection()
        async with self.connection.execute('INSERT INTO suggestions (user_id, user_name, suggestion, picture_id) VALUES (?, ?, ?, ?)',
                                           (user_id, user_name, suggestion, picture_id)):
            await self.connection.commit()
        
    async def get_project(self, project_tag: str):
        if self.connection is None:
            await self.create_connection()
        async with self.connection.execute('SELECT * FROM projects WHERE project_tag = ?', (project_tag,)) as cursor:
            result = await cursor.fetchall()
            return result
        
    async def add_to_programm(self, user_id: int, user_name: str, program: str):
        if self.connection is None:
            await self.create_connection()
        programs = {'Анализ': 'analiz', 'Разработка': 'razrabotka', 'VR': 'vr', 'DevOps': 'devops'}
        async with self.connection.execute(f'INSERT INTO {programs[program]} (user_id, user_name) VALUES (?, ?)', (user_id, user_name)):
            await self.connection.commit()

    async def start_project_information(self):
        if self.connection is None:
            await self.create_connection()
        result = await process_connection_to_excel(status='start')
        for i in range(len(result[1])):
            async with self.connection.execute(f'''INSERT INTO projects (team, project, project_tag)
                SELECT '{result[0][i]}', '{result[1][i]}', '{result[2][i]}'
                WHERE NOT EXISTS (
                    SELECT 1 FROM projects 
                    WHERE team = '{result[0][i]}' AND project = '{result[1][i]}' AND project_tag = '{result[2][i]}'
                );
                '''):
                await self.connection.commit()

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
            await conn.execute('''CREATE TABLE IF NOT EXISTS questions
                               (id INTEGER PRIMARY KEY AUTOINCREMENT,
                               user_id INTEGER,
                               question TEXT,
                               answer TEXT DEFAULT NULL,
                               moder_id INTEGER,
                               moder_name TEXT)''')
            
    async def add_question(self, user_id: int, question: str):
        if self.connection is None:
            await self.create_connection()
        async with self.connection.execute('INSERT INTO questions (user_id, question) VALUES (?, ?)', (user_id, question)):
            await self.connection.commit()
        
    async def get_unaswered_questions(self):
        if self.connection is None:
            await self.create_connection()
        async with self.connection.execute('SELECT * FROM questions WHERE answer IS NULL') as cursor:
            rows = await cursor.fetchall()
            return rows
        
    async def get_list_of_unaswered_questions(self):
        if self.connection is None:
            await self.create_connection()
        async with self.connection.execute('SELECT * FROM questions WHERE answer IS NULL ORDER BY id ASC') as cursor:
            rows = await cursor.fetchall()
            return rows

    async def update_question_id(self, question_id: int, answer: str, moder_id: int, moder_name: str):
        async with self.connection.execute('''UPDATE questions SET answer = ?, 
                                           moder_id = ?, 
                                           moder_name = ? 
                                           WHERE id = ?''', (answer, moder_id,
                                                             moder_name, question_id)):
            await self.connection.commit()

    async def get_user_id(self, question_id):
        if self.connection is None:
            await self.create_connection()
        async with self.connection.execute('SELECT * FROM questions WHERE id = ?', (question_id,)) as cursor:
            rows = await cursor.fetchall()
            result = rows[0][1]
            return result

    async def get_all_questions(self):
        if self.connection is None:
            await self.create_connection()
        async with self.connection.execute('SELECT * FROM questions ORDER BY id ASC') as cursor:
            rows = await cursor.fetchall()
            return rows
        
    async def get_question(self, question_id: int):
        async with self.connection.execute('SELECT user_id, question, answer FROM questions WHERE id = ?', (question_id,)) as cursor:
            row = await cursor.fetchone()
            if row is not None:
                user_id, question, answer = row
                return {'user_id': user_id, 'question': question, 'answer': answer}
            else:
                return None
            
    async def delete_question(self, question_id: int):
        async with self.connection.execute('DELETE FROM questions WHERE id = ?', (question_id,)):
            await self.connection.execute('DELETE FROM sqlite_sequence WHERE name="questions"')
            await self.connection.commit()

    async def clear_questions(self):
        if self.connection is None:
            await self.create_connection()
        async with self.connection.execute('DELETE FROM questions'):
            await self.connection.execute('DELETE FROM sqlite_sequence WHERE name="questions"')
            await self.connection.commit()

    async def get_number_of_unanswered_questions(self):
        if self.connection is None:
            await self.create_connection()
        async with self.connection.execute('SELECT * FROM questions WHERE answer IS NULL') as cursor:
            rows = await cursor.fetchall()
            return len(rows)
    
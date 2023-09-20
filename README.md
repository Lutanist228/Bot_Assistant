# Bot_Assistant
НЕОБХОДИМО РЕШИТЬ СЛЕДУЮЩИЕ ПРОБЛЕМЫ
1. НАЗНАЧАТЬ кого нибудь с кафедры на "должность" аналитика данных по бд (admin_questions и boltun.txt). Требуется:
   - Каждый 2-ой день 1 раз проверять данные на предмет аномалий вопрос-ответов (в boltun-е), ответы могут быть неправильными, вопросы могут содержать персональные данные. Это необходимо пресекать;  
   - Нужно следить за вопросами и ответами в бд admin_questions, чтобы выделять те вопрос-ответы, которые могут быть обработаны ИСКЛЮЧИТЕЛЬНО GPT (более трудные, узкие и спорные темы),
     или которые подходят только под формат boltun.txt (простые, общие темы);
   - (если есть база в SQL запросах или же есть есть желание таковые изучить) Аналитика данных на основе admin_questions и выявление закономерностей, тенденций по вопросам пользователей (для определения тех. решений); 
3. Устранить спам кнопками (через Middleware);
4. Добавить счетчик времени (после нажатия на кнопку, нагружающую сервер);
5. Добавить атрибуты callback-ов (text) для визуализации поведения кнопок - нажатие;
6. С помощью numpy ускорить алгоритмы;
7. Попробовать унифицировать функции db_actions для снижения их колличества;
8. Добавить в Owner-панель возможность отключить бота для определенной категории юзеров (не баны);
9. Добавить систему банов;
10. Попробовать решить проблему возврата в меню пулла вопросов после нажатия на "Выбрать вопрос" (вопрос не должен удаляться из пулла после его выбора, это баг);
11. Добавить форму для студентов (не срочно), через которую абитуриент записывается на ту или иную программу (прежде, данные попадают в бд, где идет дополнительная обработка, в случае чего);
    

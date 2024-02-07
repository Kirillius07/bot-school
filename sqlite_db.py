import sqlite3 as sq
import datetime
from datetime import datetime as dt

# Функция для установления соединения с базой данных
async def db_connect() -> None:
    global db, cur

    # Подключение к базе данных 'new.db'
    db = sq.connect('new.db')
    cur = db.cursor()
    # Создание таблиц, если они не существуют
    cur.execute("CREATE TABLE IF NOT EXISTS students(student_id INTEGER PRIMARY KEY, \
                Fname TEXT, Lname TEXT, patronymic TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS skip_school(student_id INTEGER, skip_date INTEGER, date_recording INTEGER)")
    cur.execute("CREATE TABLE IF NOT EXISTS parents(parent_id INTEGER PRIMARY KEY, student_id INTEGER)")
    cur.execute("CREATE TABLE IF NOT EXISTS admins(admin_id INTEGER PRIMARY KEY)")
    db.commit()

# Функция для получения идентификатора студента по идентификатору родителя
async def get_student_id(parent_id:int):
    result = cur.execute(f"SELECT student_id FROM parents WHERE parent_id={parent_id}").fetchone()
        
    return result[0]  
  
# Функция для регистрации пропуска ученика в базе данных
async def registration(skip_date, student_id):   
    # Получение текущего времени и даты в формате Unix
    date_recording_unix = round((dt.now() - dt(1970, 1, 1)).total_seconds())    
    skip_date_unix = round((skip_date - dt(1970, 1, 1)).total_seconds())
    # Вставка данных в таблицу skip_school
    cur_skip_school = cur.execute("INSERT INTO skip_school (student_id, skip_date, date_recording) VALUES (?, ?, ?)", (student_id, skip_date_unix, date_recording_unix))
    
    db.commit()

# Функция для проверки, является ли пользователь администратором
def is_admin(admin_id):    
    result = cur.execute(f"SELECT admin_id FROM admins WHERE admin_id={admin_id}").fetchall()    
                    
    return len(list(result))

# Функция для получения данных о прогулах всех студентов
'''
async def data_skip_school():
    data_skip_school = cur.execute("Select students.patronymic, students.Fname, date(skip_date,'unixepoch')  from skip_school 	INNER JOIN students ON 	skip_school.student_id = students.student_id ORDER BY skip_date ASC").fetchall()
    return data_skip_school  # list
'''
# Функция для получения всех пропусков одного ученика
async def the_student_skips(student_id):
    the_skips = cur.execute(f"SELECT students.patronymic, students.Fname, students.Lname, date(skip_school.skip_date,'unixepoch') FROM skip_school INNER JOIN students ON skip_school.student_id= students.student_id WHERE skip_school.student_id = {student_id} ORDER BY skip_date ASC").fetchall()
    return the_skips

# Получение данных о всех учениках
async def information_about_students():
    students = cur.execute("SELECT DISTINCT students.student_id, students.Fname, students.Lname, students.patronymic FROM students INNER JOIN skip_school ON students.student_id = skip_school.student_id  ORDER BY students.patronymic ASC, students.Fname ASC").fetchall()
    
    return students

async def delete_skip(student_id, skip_date): 
    skip_date_unix = round((skip_date - dt(1970, 1, 1)).total_seconds())
    cur.execute(f"DELETE FROM skip_school WHERE student_id = {student_id} AND skip_date = {skip_date_unix}")
    db.commit()
    
async def data_current_skip_school():
    skip_date = dt.now()
    # Установка времени на начало текущего дня
    skip_date = skip_date.replace(hour=0, minute=0, second=0, microsecond=0)    
    skip_date_unix = round((skip_date - dt(1970, 1, 1)).total_seconds())
    data_skip_school = cur.execute(f"select students.patronymic, students.Fname, date(skip_date,'unixepoch')  from skip_school 	INNER JOIN students ON 	skip_school.student_id = students.student_id WHERE skip_school.skip_date >= {skip_date_unix} ORDER BY skip_date ASC").fetchall()

    return data_skip_school  # list

async def today_skip_school():
    skip_date = dt.now()
    # Установка времени на начало текущего дня
    skip_date = skip_date.replace(hour=0, minute=0, second=0, microsecond=0)    
    skip_date_unix = round((skip_date - dt(1970, 1, 1)).total_seconds())
    data_skip_school = cur.execute(f"select students.patronymic, students.Fname, date(skip_date,'unixepoch')  from skip_school 	INNER JOIN students ON 	skip_school.student_id = students.student_id WHERE skip_school.skip_date >= {skip_date_unix} AND skip_school.skip_date < {skip_date_unix} + 86400 ORDER BY skip_date ASC").fetchall()

    return data_skip_school  # list

async def current_dates_skip(student_id):
    the_day = dt.now()
    today = the_day.replace(hour=0, minute=0, second=0, microsecond=0)
    today_unix = round((today - dt(1970, 1, 1)).total_seconds())
    curent_skip_data = cur.execute(f"SELECT date(skip_date,'unixepoch') FROM skip_school WHERE student_id = {student_id} AND skip_date >= {today_unix} ORDER BY skip_date ASC").fetchall()
    return curent_skip_data
    
async def tomorrow_skip_school():
    skip_date = dt.now()
    # Установка времени на начало текущего дня
    skip_date = skip_date.replace(hour=0, minute=0, second=0, microsecond=0)    
    skip_date_unix = round((skip_date - dt(1970, 1, 1)).total_seconds()) +  86400
    data_skip_school = cur.execute(f"select students.patronymic, students.Fname, date(skip_date,'unixepoch')  from skip_school 	INNER JOIN students ON 	skip_school.student_id = students.student_id WHERE skip_school.skip_date >= {skip_date_unix} AND skip_school.skip_date < {skip_date_unix} + 86400 ORDER BY skip_date ASC").fetchall()

    return data_skip_school  # list

# Функция для проверки наличия записи о пропуске на указанную дату для указанного студента
async def there_is_record(skip_date, student_id):
    # Установка времени на начало текущего дня
    result = True
    skip_date = skip_date.replace(hour=0, minute=0, second=0, microsecond=0)    
    skip_date_unix = round((skip_date - dt(1970, 1, 1)).total_seconds())       
    data_skip_school = cur.execute(f"select * from skip_school WHERE student_id = {student_id} AND skip_date = {skip_date_unix}").fetchone()
    if data_skip_school is None:
        result = False    
    return result
    
'''    
    1. сделать проверку на существование ид родителя
'''

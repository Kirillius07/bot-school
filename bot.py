from aiogram import types, executor, Dispatcher, Bot
from aiogram.contrib.fsm_storage.memory import MemoryStorage 
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram_calendar import simple_cal_callback, SimpleCalendar, dialog_cal_callback, DialogCalendar
from aiogram.dispatcher.filters import Text
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup
from keyboards import *
from config import TOKEN_API
import sqlite_db
from openpyxl import Workbook
import datetime
Exel_file = Workbook()
first_Table = Exel_file.active
second_Table = Exel_file.create_sheet("second Table")

#создаем колбэк для хранения данных между вызовами
callback_school = CallbackData( 'filter_students', 'start_date', 'action') 
callback_dates = CallbackData('filter_date', 'students_id', 'delete_date', 'action')
callback_students = CallbackData('filter_students', 'student_id', 'action')
#создаем клавиатуру Запись на дату
start_kb = ReplyKeyboardMarkup(resize_keyboard=True,) #
start_kb.row('Запись на дату') 
start_kb.row('Отменить запись')
#Эта функция создает и возвращает клавиатуру с встроенными кнопками 
#для получения отчетов о прогулах. Кнопки включают в себя опции 
#"отчет о пропусках" и "действующие пропуски".

def date_students_ikb() -> InlineKeyboardMarkup: 
    ikb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton('Пропуски за сегодня', callback_data=callback_school.new('now', 'today_skip'))],
        [InlineKeyboardButton('Пропуски на завтра', callback_data=callback_school.new('now', 'tomorrow_skip'))],
        [InlineKeyboardButton('Действующие пропуски', callback_data=callback_school.new('now', 'current_skip'))],
        [InlineKeyboardButton('Актуальные пропуски.txt', callback_data= callback_school.new('now', 'txt_file'))],
        [InlineKeyboardButton('Актуальные пропуски.csv', callback_data= callback_school.new('now', 'csv_file'))],
        [InlineKeyboardButton('Отчет о всех пропусках', callback_data= callback_school.new('now', 'all_skip'))],
    ])
    return ikb 

bot = Bot(TOKEN_API)
storage = MemoryStorage()
dp = Dispatcher(bot,
                storage=storage)

#Это функция, вызываемая при запуске бота. 
#Она подключается к базе данных SQLite и выводит сообщение об успешном подключении.

async def on_startup(_):
    await sqlite_db.db_connect()
    print('Подключение к БД выполнено успешно')
#
#Обработчик команды /start. 
#В зависимости от того, является ли пользователь администратором,
#отправляет ему различные приветственные сообщения с различными клавишами.
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    admin = sqlite_db.is_admin(message.from_user.id)
    if admin:
            await bot.send_message(chat_id=message.from_user.id,
                           text='Данные об учениках',
                           reply_markup=date_students_ikb()) 
    else:
        await bot.send_message(chat_id=message.from_user.id,
                           text='Добро пожаловать!',
                           reply_markup=start_kb)  

#Обработчик команды 'Запись на дату'         
@dp.message_handler(Text(equals=['Запись на дату'], ignore_case=True))
async def nav_cal_handler(message: types.Message):    
    await bot.send_message(chat_id=message.from_user.id,
                           text='Выберите дату: ',
                           reply_markup=await SimpleCalendar().start_calendar())  


# Обработчик выбора даты из встроенного календаря. 
# Если дата выбрана, он проверяет, есть ли уже запись на эту дату, 
# и либо регистрирует новую запись, либо сообщает, что запись уже существует.
@dp.callback_query_handler(simple_cal_callback.filter())
async def process_simple_calendar(callback_query: CallbackQuery, callback_data: dict):
    selected, date = await SimpleCalendar().process_selection(callback_query, callback_data)
    if selected:     
        student_id = await sqlite_db.get_student_id(callback_query.from_user.id)        
        there_is_record = await sqlite_db.there_is_record(date, student_id)
                
        if there_is_record:
            await callback_query.message.answer(
                f'Вы уже записывались ранее на  {date.strftime("%d/%m/%Y")}',
                reply_markup=start_kb)

        else:            
            await sqlite_db.registration(date, student_id)         
            await callback_query.message.answer(
                f'Вы зафиксировали отгул на  {date.strftime("%d/%m/%Y")}',
                reply_markup=start_kb)       
   
#Обработчики выбора действий с отчетами о прогулах. 
@dp.callback_query_handler(callback_school.filter(action='today_skip'))
async def today_skip(callback_query: CallbackQuery, callback_data: dict):  
    date_skip_school = await sqlite_db.today_skip_school()    
    await show_skip_school(callback_query, date_skip_school, "<b>Пропуски на сегодня:</b>")
    
#Функция, в которой идет запись всех данных об одном ученике в .txt     
async def writing_txt_file_dates(student_skips: list, name_file: str):
    name_file = f'Пропуски {student_skips[0][0]} {student_skips[0][1]} {student_skips[0][2]}.txt'
    #name_file = 'NameFile.txt'
    file = open(name_file,'w', encoding='utf-8')
    for skip in student_skips:
        file.write(skip[3] + "\n")
        
#Вызов функции writing_txt_file_dates, отправка файла Админу         
@dp.callback_query_handler(callback_students.filter(action='student_skips'))
async def cancel_dates(callback_query: CallbackQuery, callback_data: dict):
    student_id = callback_data.get('student_id')
    student_skips = await sqlite_db.the_student_skips(student_id)      
    name_file = f'Пропуски {student_skips[0][0]} {student_skips[0][1]} {student_skips[0][2]}.txt'
    await writing_txt_file_dates(student_skips, name_file)
    await bot.send_document(chat_id=callback_query.message.chat.id, document=types.InputFile(name_file))

    
@dp.callback_query_handler(callback_school.filter(action='all_skip'))
async def delete_date(message: types.Message):    
    students = await sqlite_db.information_about_students()    
    ikb_current_skip_students = InlineKeyboardMarkup()
    for student in students:
        button_with_student = InlineKeyboardButton(f'{student[3]} {student[1]} {student[2]}', callback_data=callback_students.new(student[0], 'student_skips'))
        ikb_current_skip_students.add(button_with_student)
    await bot.send_message(chat_id=message.from_user.id,
                           text='Выберите ученика для получения пропусков:',
                           reply_markup=ikb_current_skip_students)
    
    
@dp.callback_query_handler(callback_school.filter(action='tomorrow_skip'))
async def today_skip(callback_query: CallbackQuery, callback_data: dict):  
    date_skip_school = await sqlite_db.tomorrow_skip_school()    
    await show_skip_school(callback_query, date_skip_school, "<b>Пропуски на завтра:</b>")

#Отлавливаем нажатие родителя, затем удаляем запись из БД
@dp.message_handler(Text(equals=['Отменить запись'], ignore_case=True))
async def delete_date(message: types.Message):
    student_id = await sqlite_db.get_student_id(message.from_user.id)
    skip_dates = await sqlite_db.current_dates_skip(student_id)

    ikb_current_skip_date = InlineKeyboardMarkup()
    for skip_date in skip_dates:
        button_with_date = InlineKeyboardButton(skip_date[0], callback_data=callback_dates.new(student_id, skip_date[0], 'cancel'))
        ikb_current_skip_date.add(button_with_date)
    await bot.send_message(chat_id=message.from_user.id,
                           text='Выберите дату которую хотите отменить:',
                           reply_markup=ikb_current_skip_date)


@dp.callback_query_handler(callback_dates.filter(action='cancel'))
async def cancel_dates(callback_query: CallbackQuery, callback_data: dict):
    date_time_obj = datetime.datetime.strptime(callback_data.get('delete_date'), '%Y-%m-%d')
    student_id = callback_data.get('students_id')
    await sqlite_db.delete_skip(student_id, date_time_obj)
#Функции, которые записывают данные в файлы разных форматов .txt или .csv
async def writing_txt_file(data_skip_school:list):
    file = open('Актуальные пропуски.txt','w', encoding='utf-8')
    date = ''
    for skip in data_skip_school:        
        if skip[2] != date or date == '':
            date = skip[2]
            file.write(date + "\n")            
        file.write(skip[0] + ' ' + skip[1] + "\n")
    
async def writing_csv_file(data_skip_school:list):
    file = open('Актуальные пропуски.csv','w', encoding='utf-8')
    date = ''
    for skip in data_skip_school:        
        if skip[2] != date or date == '':
            date = skip[2]
            file.write(date + "\n")            
        file.write(skip[0] + ';' + skip[1] + "\n")    
#Отлавливаем сообщение учителя, и высылаем ему файл
@dp.callback_query_handler(callback_school.filter(action='txt_file'))
async def generated_txt_file(callback_query: CallbackQuery, callback_data: dict):
    data_skip_school = await sqlite_db.data_current_skip_school()
    if len(data_skip_school) > 0:
        await writing_txt_file(data_skip_school)
        await bot.send_document(chat_id=callback_query.message.chat.id, document=types.InputFile('Актуальные пропуски.txt'))
        await bot.send_message(chat_id=callback_query.message.chat.id,
                               text= 'Ваш файл готов.')
    else:
        await bot.send_message(chat_id=callback_query.message.chat.id,
                               text= 'На данный момент нет запланированных пропусков.')
        
@dp.callback_query_handler(callback_school.filter(action='csv_file'))
async def generated_csv_file(callback_query: CallbackQuery, callback_data: dict):
    data_skip_school = await sqlite_db.data_current_skip_school()
    if len(data_skip_school) > 0:
        await writing_csv_file(data_skip_school)
        await bot.send_document(chat_id=callback_query.message.chat.id, document=types.InputFile('Актуальные пропуски.csv'))
        await bot.send_message(chat_id=callback_query.message.chat.id,
                            text= 'Ваш файл готов.')
    else:
        await bot.send_message(chat_id=callback_query.message.chat.id,
                               text= 'На данный момент нет запланированных пропусков.')
        
                           
#Обработчики выбора действий с отчетами о действующих прогулах. 
# Они вызывают функцию show_skip_school, которая отправляет сообщения 
# с отчетами пользователю.       
@dp.callback_query_handler(callback_school.filter(action='current_skip'))
async def process_current_skip(callback_query: CallbackQuery, callback_data: dict):  
    date_skip_school = await sqlite_db.data_current_skip_school()   
    await show_skip_school(callback_query, date_skip_school, "<b>Актуальные пропуски:</b>")


#отправляет сообщение в телеграм о студентах у которых есть пропуски    
async def show_skip_school(callback: types.CallbackQuery, date_skip_school: list, message_str: str) -> None:
    await bot.send_message(chat_id=callback.message.chat.id,
                           text= message_str,
                           parse_mode="HTML")
    
    date = ''
    for skip in date_skip_school:        
        if skip[2] != date or date == '':
            date = skip[2]
            await bot.send_message(chat_id=callback.message.chat.id,
                               text= '<i>' + date + '</i>',
                                parse_mode="HTML")
            
        await bot.send_message(chat_id=callback.message.chat.id,
                               text = skip[0] + ' ' +skip[1])
  
    
        
if __name__ == '__main__':
    executor.start_polling(dispatcher=dp,
                           skip_updates=True,
                           on_startup=on_startup)

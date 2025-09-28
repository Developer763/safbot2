import telebot
from telebot import types
import os
from collections import defaultdict

TOKEN = os.getenv("8347021575:AAET7hZLnsAuqROs35GD9G08CWhHEM6sVBE")
bot = telebot.TeleBot(TOKEN)

OWNER_ID = int(os.getenv("OWNER_ID", "123456789"))

admin_levels = defaultdict(dict)  # chat_id -> {user_id: level}
prefixes = defaultdict(dict)      # chat_id -> {user_id: prefix}
banned = defaultdict(set)
muted = defaultdict(set)
warns = defaultdict(lambda: defaultdict(int))

# список чатов и счётчик сообщений
chats_list = set()
messages_count = defaultdict(int)  # chat_id -> количество сообщений обработанных ботом

def get_level(chat_id, user_id):
    if user_id == OWNER_ID:
        return 5
    return admin_levels[chat_id].get(user_id, 0)

# сохраняем чаты + считаем сообщения
@bot.message_handler(func=lambda m: True, content_types=['text', 'photo', 'video', 'sticker', 'animation', 'voice'])
def any_message(msg):
    chats_list.add(msg.chat.id)
    messages_count[msg.chat.id] += 1
    if msg.from_user.id in banned[msg.chat.id] or msg.from_user.id in muted[msg.chat.id]:
        try:
            bot.delete_message(msg.chat.id, msg.message_id)
        except:
            pass

# команда /chats только для OWNER в личке
@bot.message_handler(commands=['chats'])
def chats(msg):
    if msg.from_user.id != OWNER_ID or msg.chat.type != 'private':
        return
    if not chats_list:
        return bot.reply_to(msg, "Бот пока ни в одном чате не состоит.")
    kb = types.InlineKeyboardMarkup()
    for cid in chats_list:
        try:
            chat = bot.get_chat(cid)
            name = chat.title if chat.title else chat.first_name
        except:
            name = str(cid)
        kb.add(types.InlineKeyboardButton(text=name, callback_data=f"chatinfo_{cid}"))
    bot.reply_to(msg, "Выберите чат:", reply_markup=kb)

# обработчик нажатия кнопки
@bot.callback_query_handler(func=lambda call: call.data.startswith("chatinfo_"))
def chatinfo(call):
    if call.from_user.id != OWNER_ID:
        return bot.answer_callback_query(call.id, "Нет прав")
    cid = int(call.data.split("_")[1])
    try:
        chat = bot.get_chat(cid)
        name = chat.title if chat.title else chat.first_name
        members = chat.get_members_count() if hasattr(chat, 'get_members_count') else None
    except Exception as e:
        return bot.answer_callback_query(call.id, f"Не могу получить чат: {e}")
    # количество админов
    admins = admin_levels[cid]
    admins_count = len(admins)
    msg_count = messages_count[cid]
    text = f"**Информация о чате**\n" \
           f"Название: {name}\n" \
           f"ID: {cid}\n" \
           f"Участников: {members if members else 'неизвестно'}\n" \
           f"Администраторов (в базе бота): {admins_count}\n" \
           f"Сообщений обработано: {msg_count}"
    bot.answer_callback_query(call.id)
    bot.send_message(call.from_user.id, text, parse_mode='Markdown')

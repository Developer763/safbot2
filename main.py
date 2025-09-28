import telebot
from telebot import types
import os

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

admins = set()
banned = set()
muted = set()
warns = {}
OWNER_ID = int(os.getenv("OWNER_ID", "123456789"))

def is_admin(user_id):
    return user_id in admins or user_id == OWNER_ID

@bot.message_handler(commands=['start'])
def start(msg):
    bot.reply_to(msg, "Привет! Я модерационный бот.")

@bot.message_handler(commands=['add_admin'])
def add_admin(msg):
    if msg.from_user.id != OWNER_ID:
        return bot.reply_to(msg, "Только владелец бота может назначать админов.")
    if not msg.reply_to_message:
        return bot.reply_to(msg, "Ответьте на сообщение пользователя.")
    user_id = msg.reply_to_message.from_user.id
    admins.add(user_id)
    bot.reply_to(msg, f"Пользователь @{msg.reply_to_message.from_user.username} теперь админ.")

@bot.message_handler(commands=['remove_admin'])
def remove_admin(msg):
    if msg.from_user.id != OWNER_ID:
        return bot.reply_to(msg, "Только владелец бота может снимать админов.")
    if not msg.reply_to_message:
        return bot.reply_to(msg, "Ответьте на сообщение пользователя.")
    user_id = msg.reply_to_message.from_user.id
    admins.discard(user_id)
    bot.reply_to(msg, f"Пользователь @{msg.reply_to_message.from_user.username} больше не админ.")

@bot.message_handler(commands=['ban'])
def ban(msg):
    if not is_admin(msg.from_user.id):
        return bot.reply_to(msg, "Нет прав.")
    if not msg.reply_to_message:
        return bot.reply_to(msg, "Ответьте на сообщение пользователя.")
    target_id = msg.reply_to_message.from_user.id
    if is_admin(target_id):
        return bot.reply_to(msg, "Нельзя банить администратора.")
    banned.add(target_id)
    try:
        bot.kick_chat_member(msg.chat.id, target_id)
    except Exception as e:
        print(e)
    bot.reply_to(msg, f"Пользователь @{msg.reply_to_message.from_user.username} забанен.")

@bot.message_handler(commands=['unban'])
def unban(msg):
    if not is_admin(msg.from_user.id):
        return bot.reply_to(msg, "Нет прав.")
    if not msg.reply_to_message:
        return bot.reply_to(msg, "Ответьте на сообщение пользователя.")
    target_id = msg.reply_to_message.from_user.id
    banned.discard(target_id)
    try:
        bot.unban_chat_member(msg.chat.id, target_id)
    except Exception as e:
        print(e)
    bot.reply_to(msg, f"Пользователь @{msg.reply_to_message.from_user.username} разбанен.")

@bot.message_handler(commands=['mute'])
def mute(msg):
    if not is_admin(msg.from_user.id):
        return bot.reply_to(msg, "Нет прав.")
    if not msg.reply_to_message:
        return bot.reply_to(msg, "Ответьте на сообщение пользователя.")
    target_id = msg.reply_to_message.from_user.id
    if is_admin(target_id):
        return bot.reply_to(msg, "Нельзя мьютить администратора.")
    muted.add(target_id)
    try:
        bot.restrict_chat_member(
            msg.chat.id,
            target_id,
            permissions=types.ChatPermissions(can_send_messages=False)
        )
    except Exception as e:
        print(e)
    bot.reply_to(msg, f"Пользователь @{msg.reply_to_message.from_user.username} замьючен.")

@bot.message_handler(commands=['unmute'])
def unmute(msg):
    if not is_admin(msg.from_user.id):
        return bot.reply_to(msg, "Нет прав.")
    if not msg.reply_to_message:
        return bot.reply_to(msg, "Ответьте на сообщение пользователя.")
    target_id = msg.reply_to_message.from_user.id
    muted.discard(target_id)
    try:
        bot.restrict_chat_member(
            msg.chat.id,
            target_id,
            permissions=types.ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_change_info=True,
                can_invite_users=True,
                can_pin_messages=True
            )
        )
    except Exception as e:
        print(e)
    bot.reply_to(msg, f"Пользователь @{msg.reply_to_message.from_user.username} размьючен.")

@bot.message_handler(commands=['warn'])
def warn(msg):
    if not is_admin(msg.from_user.id):
        return bot.reply_to(msg, "Нет прав.")
    if not msg.reply_to_message:
        return bot.reply_to(msg, "Ответьте на сообщение пользователя.")
    target_id = msg.reply_to_message.from_user.id
    if is_admin(target_id):
        return bot.reply_to(msg, "Нельзя выдавать предупреждения администратору.")
    warns[target_id] = warns.get(target_id, 0) + 1
    bot.reply_to(msg, f"Пользователь @{msg.reply_to_message.from_user.username} получил предупреждение ({warns[target_id]}).")

@bot.message_handler(func=lambda m: True)
def check_user(msg):
    if msg.from_user.id in banned or msg.from_user.id in muted:
        try:
            bot.delete_message(msg.chat.id, msg.message_id)
        except Exception as e:
            print(e)

if __name__ == "__main__":
    bot.infinity_polling()

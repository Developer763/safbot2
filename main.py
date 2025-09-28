import telebot
from telebot import types
import os

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# словарь: id -> уровень админа
admin_levels = {}  # например {123456: 5}
OWNER_ID = int(os.getenv("OWNER_ID", "123456789"))

# начальные разрешения команд: команда -> минимальный уровень
permissions = {
    'add_admin': 5,
    'remove_admin': 5,
    'ban': 2,
    'unban': 2,
    'mute': 2,
    'unmute': 2,
    'warn': 1,
    'setperm': 5
}

banned = set()
muted = set()
warns = {}

def get_level(user_id):
    if user_id == OWNER_ID:
        return 5
    return admin_levels.get(user_id, 0)

def check_perm(user_id, command):
    return get_level(user_id) >= permissions.get(command, 0)

@bot.message_handler(commands=['start'])
def start(msg):
    bot.reply_to(msg, "Привет! Я модерационный бот с уровнями администрации.")

@bot.message_handler(commands=['add_admin'])
def add_admin(msg):
    if not check_perm(msg.from_user.id, 'add_admin'):
        return bot.reply_to(msg, "Нет прав.")
    if not msg.reply_to_message:
        return bot.reply_to(msg, "Ответьте на сообщение пользователя.")
    try:
        level = int(msg.text.split()[1])
    except:
        return bot.reply_to(msg, "Укажите уровень (1–5): /add_admin <уровень> (ответом на сообщение)")
    if level < 1 or level > 5:
        return bot.reply_to(msg, "Уровень должен быть 1–5.")
    user_id = msg.reply_to_message.from_user.id
    admin_levels[user_id] = level
    bot.reply_to(msg, f"Пользователь @{msg.reply_to_message.from_user.username} назначен админом уровня {level}.")

@bot.message_handler(commands=['remove_admin'])
def remove_admin(msg):
    if not check_perm(msg.from_user.id, 'remove_admin'):
        return bot.reply_to(msg, "Нет прав.")
    if not msg.reply_to_message:
        return bot.reply_to(msg, "Ответьте на сообщение пользователя.")
    user_id = msg.reply_to_message.from_user.id
    admin_levels.pop(user_id, None)
    bot.reply_to(msg, f"Пользователь @{msg.reply_to_message.from_user.username} больше не админ.")

@bot.message_handler(commands=['setperm'])
def setperm(msg):
    if not check_perm(msg.from_user.id, 'setperm'):
        return bot.reply_to(msg, "Нет прав.")
    parts = msg.text.split()
    if len(parts) != 3:
        return bot.reply_to(msg, "Использование: /setperm <команда> <уровень>")
    command = parts[1].lower()
    try:
        level = int(parts[2])
    except:
        return bot.reply_to(msg, "Уровень должен быть числом 0–5.")
    if level < 0 or level > 5:
        return bot.reply_to(msg, "Уровень должен быть 0–5.")
    permissions[command] = level
    bot.reply_to(msg, f"Команда /{command} теперь доступна с уровня {level}.")

@bot.message_handler(commands=['ban'])
def ban(msg):
    if not check_perm(msg.from_user.id, 'ban'):
        return bot.reply_to(msg, "Нет прав.")
    if not msg.reply_to_message:
        return bot.reply_to(msg, "Ответьте на сообщение пользователя.")
    target_id = msg.reply_to_message.from_user.id
    if get_level(target_id) >= get_level(msg.from_user.id):
        return bot.reply_to(msg, "Нельзя банить администратора с таким же или выше уровнем.")
    banned.add(target_id)
    try:
        bot.kick_chat_member(msg.chat.id, target_id)
    except Exception as e:
        print(e)
    bot.reply_to(msg, f"Пользователь @{msg.reply_to_message.from_user.username} забанен.")

@bot.message_handler(commands=['unban'])
def unban(msg):
    if not check_perm(msg.from_user.id, 'unban'):
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
    if not check_perm(msg.from_user.id, 'mute'):
        return bot.reply_to(msg, "Нет прав.")
    if not msg.reply_to_message:
        return bot.reply_to(msg, "Ответьте на сообщение пользователя.")
    target_id = msg.reply_to_message.from_user.id
    if get_level(target_id) >= get_level(msg.from_user.id):
        return bot.reply_to(msg, "Нельзя мьютить администратора с таким же или выше уровнем.")
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
    if not check_perm(msg.from_user.id, 'unmute'):
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
    if not check_perm(msg.from_user.id, 'warn'):
        return bot.reply_to(msg, "Нет прав.")
    if not msg.reply_to_message:
        return bot.reply_to(msg, "Ответьте на сообщение пользователя.")
    target_id = msg.reply_to_message.from_user.id
    if get_level(target_id) >= get_level(msg.from_user.id):
        return bot.reply_to(msg, "Нельзя предупреждать администратора с таким же или выше уровнем.")
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

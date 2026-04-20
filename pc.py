import os
import psutil
from wakeonlan import send_magic_packet
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "8089393760:AAFCTCKWePv3Ihc34AroLHr0BUmouC2Mwvo"
USER_ID = 1073348110

PC_IP = "192.168.0.107"
PC_MAC = "9C:6B:00:4C:FA:B3"
BROADCAST_IP = "192.168.0.255"

BASE_DIR = r"C:\Users\Kwizixi\Desktop"
last_action = "Нема дій"


# ---------------- STATUS ----------------

def is_online():
    return os.system(f"ping -n 1 -w 700 {PC_IP} > nul") == 0


def stats():
    return (
        psutil.cpu_percent(),
        psutil.virtual_memory().percent,
        psutil.disk_usage("C:\\").percent
    )


# ---------------- MENU ----------------

def menu():
    status = "🟢 Онлайн" if is_online() else "🔴 Офлайн"
    cpu, ram, disk = stats()

    text = f"""
🖥 CONTROL PANEL

📡 Статус: {status}
🔥 CPU: {cpu}%
🧠 RAM: {ram}%
💾 Disk: {disk}%

🧾 Остання дія: {last_action}
"""

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Оновити", callback_data="refresh")],

        [InlineKeyboardButton("⚡ Увімкнути ПК", callback_data="wake")],
        [InlineKeyboardButton("⛔ Вимкнути ПК", callback_data="shutdown")],
        [InlineKeyboardButton("🔁 Перезавантажити ПК", callback_data="restart")],

        [InlineKeyboardButton("🎮 Steam", callback_data="steam")],
        [InlineKeyboardButton("📋 Процеси", callback_data="list")],
        [InlineKeyboardButton("📁 Файли", callback_data="files")]
    ])

    return text, kb


# ---------------- PROCESSES ----------------

def get_processes():
    return list(set([
        p.info['name']
        for p in psutil.process_iter(['name'])
        if p.info['name']
    ]))[:12]


def kill_process(name):
    for p in psutil.process_iter():
        try:
            if p.name().lower() == name.lower():
                p.kill()
        except:
            pass


def process_keyboard():
    buttons = [[InlineKeyboardButton(f"❌ {p}", callback_data=f"kill|{p}")] for p in get_processes()]
    buttons.append([InlineKeyboardButton("⬅️ Назад", callback_data="back")])
    return InlineKeyboardMarkup(buttons)


# ---------------- FILES ----------------

def file_keyboard(path):
    buttons = []

    parent = os.path.dirname(path)
    buttons.append([InlineKeyboardButton("⬅️ Назад", callback_data=f"cd|{parent}")])

    try:
        for i in os.listdir(path):
            full = os.path.join(path, i)
            if os.path.isdir(full):
                buttons.append([InlineKeyboardButton("📁 " + i, callback_data=f"cd|{full}")])
            else:
                buttons.append([InlineKeyboardButton("📄 " + i, callback_data=f"file|{full}")])
    except:
        pass

    buttons.append([InlineKeyboardButton("🏠 Додому", callback_data=f"cd|{BASE_DIR}")])

    return InlineKeyboardMarkup(buttons)


# ---------------- START ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last_action

    if update.effective_user.id != USER_ID:
        return

    last_action = "Панель відкрита"

    text, kb = menu()
    await update.message.reply_text(text, reply_markup=kb)


# ---------------- BUTTONS ----------------

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last_action

    q = update.callback_query

    if q.from_user.id != USER_ID:
        await q.answer("Нема доступу")
        return

    await q.answer()
    d = q.data

    # 🔄 refresh
    if d == "refresh":
        text, kb = menu()
        await q.edit_message_text(text, reply_markup=kb)

    # ⚡ wake
    elif d == "wake":
        send_magic_packet(PC_MAC, ip_address=BROADCAST_IP)
        last_action = "ПК увімкнено"
        text, kb = menu()
        await q.edit_message_text(text, reply_markup=kb)

    # ⛔ shutdown
    elif d == "shutdown":
        os.system("shutdown /s /t 0")
        last_action = "ПК вимкнено"
        text, kb = menu()
        await q.edit_message_text(text, reply_markup=kb)

    # 🔁 restart
    elif d == "restart":
        os.system("shutdown /r /t 0")
        last_action = "ПК перезавантажено"
        text, kb = menu()
        await q.edit_message_text(text, reply_markup=kb)

    # 🎮 steam
    elif d == "steam":
        os.system("start steam://open/main")
        last_action = "Steam запущено"
        text, kb = menu()
        await q.edit_message_text(text, reply_markup=kb)

    # 📋 processes
    elif d == "list":
        last_action = "Процеси"
        await q.edit_message_text("📋 Процеси:", reply_markup=process_keyboard())

    elif d.startswith("kill|"):
        name = d.split("|")[1]
        kill_process(name)
        last_action = f"Закрито {name}"
        await q.edit_message_text("📋 Процеси:", reply_markup=process_keyboard())

    # 📁 files
    elif d == "files":
        last_action = "Файли"
        await q.edit_message_text("📁 Файли:", reply_markup=file_keyboard(BASE_DIR))

    elif d.startswith("cd|"):
        path = d.split("|", 1)[1]
        await q.edit_message_text(f"📁 {path}", reply_markup=file_keyboard(path))

    elif d.startswith("file|"):
        path = d.split("|", 1)[1]
        try:
            await q.message.reply_document(open(path, "rb"))
        except:
            await q.message.reply_text("❌ Не вдалося відкрити файл")

    # ⬅️ back
    elif d == "back":
        text, kb = menu()
        await q.edit_message_text(text, reply_markup=kb)


# ---------------- RUN ----------------

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))

print("🟢 CONTROL PANEL RUNNING...")
app.run_polling()

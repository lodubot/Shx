import os
import subprocess
import re
import time
import json
import psutil
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "8993593935:AAGwkSpz6g8VWeJAdj4ZSW1NaJGJYwVwsbQ"
MAX_USERS = 40
DATA_FILE = "vps_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def get_sshx_link(chat_id):
    log = f"/tmp/sshx_{chat_id}.log"
    subprocess.run(f"pkill -f 'sshx_{chat_id}' || true", shell=True)
    time.sleep(1)
    subprocess.run(f"nohup sshx > {log} 2>&1 &", shell=True)
    time.sleep(5)
    try:
        with open(log) as f:
            content = f.read()
        clean = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', content)
        match = re.search(r'https://sshx\.io/[^\s]+', clean)
        return match.group(0) if match else None
    except:
        return None

def get_server_stats():
    cpu = psutil.cpu_percent(interval=1)
    cores = psutil.cpu_count()
    load = os.getloadavg()
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    uptime = time.time() - psutil.boot_time()
    d, h, m = int(uptime//86400), int((uptime%86400)//3600), int((uptime%3600)//60)
    return {
        "cpu": cpu, "cores": cores, "load": load,
        "ram_used": ram.used/1024**2, "ram_total": ram.total/1024**2, "ram_pct": ram.percent,
        "disk_used": disk.used/1024**3, "disk_total": disk.total/1024**3, "disk_pct": disk.percent,
        "uptime": f"{d}d {h}h {m}m"
    }

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🖥️ VE VPS Manager\n\n"
        "/deploy — VPS deploy karo\n"
        "/link — Sshx link lo\n"
        "/mystatus — Apna status\n"
        "/serverstatus — Server status\n"
        "/delete — VPS delete karo"
    )

async def deploy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    data = load_data()

    if chat_id in data:
        await update.message.reply_text("⚠️ VPS pehle se hai! /link use karo.")
        return

    if len(data) >= MAX_USERS:
        await update.message.reply_text("❌ Limit Over!\nServer full hai. Good Luck Next Time! 🍀")
        return

    await update.message.reply_text("⏳ VPS deploy ho raha hai...")

    # User folder banao
    user_dir = f"/tmp/vps_{chat_id}"
    os.makedirs(user_dir, exist_ok=True)

    data[chat_id] = {"dir": user_dir, "status": "running"}
    save_data(data)

    await update.message.reply_text(
        "✅ VPS Successfully Deployed!\n\n"
        f"🖥️ ID: vps_{chat_id}\n"
        "💾 RAM: 8GB\n"
        "⚙️ CPU: 5 cores\n"
        "💿 Disk: 60GB\n\n"
        "🔗 /link se sshx link lo"
    )

async def get_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    data = load_data()

    if chat_id not in data:
        await update.message.reply_text("❌ Pehle /deploy karein!")
        return

    await update.message.reply_text("⏳ Link fetch ho rahi hai...")
    link = get_sshx_link(chat_id)

    if link:
        data[chat_id]["link"] = link
        save_data(data)
        await update.message.reply_text(f"🔗 Aapki Sshx Link:\n{link}")
    else:
        await update.message.reply_text("❌ Link nahi mili. Dobara /link try karein.")

async def my_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    data = load_data()

    if chat_id not in data:
        await update.message.reply_text("❌ Koi VPS nahi. /deploy karein.")
        return

    await update.message.reply_text(
        f"📊 Aapka VPS Status\n\n"
        f"🖥️ ID: vps_{chat_id}\n"
        f"📡 Status: 🟢 Running\n"
        f"💾 RAM: 8GB\n"
        f"⚙️ CPU: 5 cores\n"
        f"💿 Disk: 60GB"
    )

async def server_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = get_server_stats()
    data = load_data()
    await update.message.reply_text(
        f"🖥️ VPS Status\n\n"
        f"CPU: {s['cpu']}% ({s['cores']} cores)\n"
        f"Load avg: {s['load'][0]:.2f}, {s['load'][1]:.2f}, {s['load'][2]:.2f}\n"
        f"RAM: {s['ram_used']:.1f}MB / {s['ram_total']:.1f}MB ({s['ram_pct']}%)\n"
        f"Disk: {s['disk_used']:.1f}GB / {s['disk_total']:.1f}GB ({s['disk_pct']}%)\n"
        f"Uptime: {s['uptime']}\n\n"
        f"👥 Active Users: {len(data)}/{MAX_USERS}\n\n"
        f"👑 Bot by @YourUsername"
    )

async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    data = load_data()

    if chat_id not in data:
        await update.message.reply_text("❌ Koi VPS nahi mila.")
        return

    subprocess.run(f"pkill -f 'sshx_{chat_id}' || true", shell=True)
    subprocess.run(f"rm -rf /tmp/vps_{chat_id}", shell=True)
    del data[chat_id]
    save_data(data)
    await update.message.reply_text("✅ VPS delete ho gaya.")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("deploy", deploy))
    app.add_handler(CommandHandler("link", get_link))
    app.add_handler(CommandHandler("mystatus", my_status))
    app.add_handler(CommandHandler("serverstatus", server_status))
    app.add_handler(CommandHandler("delete", delete))
    app.run_polling()

if __name__ == "__main__":
    main()

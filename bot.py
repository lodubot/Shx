import os
import subprocess
import re
import time
import json
import psutil
import asyncio
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "8993593935:AAGwkSpz6g8VWeJAdj4ZSW1NaJGJYwVwsbQ"
MAX_USERS = 40
DATA_FILE = "vps_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def container_name(chat_id):
    return f"vps_user_{chat_id}"

def is_container_running(chat_id):
    result = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Running}}", container_name(chat_id)],
        capture_output=True, text=True
    )
    return result.stdout.strip() == "true"

def is_sshx_running(chat_id):
    """Container ke andar sshx process chal rahi hai ya nahi"""
    result = subprocess.run(
        ["docker", "exec", container_name(chat_id), "pgrep", "sshx"],
        capture_output=True, text=True
    )
    return result.returncode == 0

def get_container_stats(chat_id):
    result = subprocess.run(
        ["docker", "stats", "--no-stream", "--format",
         "{{.CPUPerc}}|{{.MemUsage}}|{{.BlockIO}}",
         container_name(chat_id)],
        capture_output=True, text=True
    )
    if result.returncode == 0 and result.stdout.strip():
        parts = result.stdout.strip().split("|")
        if len(parts) == 3:
            return {"cpu": parts[0], "mem": parts[1], "disk_io": parts[2]}
    return None

def get_server_stats():
    cpu = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count()
    load = os.getloadavg()
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    uptime_seconds = time.time() - psutil.boot_time()
    days = int(uptime_seconds // 86400)
    hours = int((uptime_seconds % 86400) // 3600)
    mins = int((uptime_seconds % 3600) // 60)
    return {
        "cpu_percent": cpu, "cpu_cores": cpu_count, "load": load,
        "ram_used": ram.used / (1024**2), "ram_total": ram.total / (1024**2),
        "ram_percent": ram.percent,
        "disk_used": disk.used / (1024**3), "disk_total": disk.total / (1024**3),
        "disk_percent": disk.percent,
        "uptime": f"{days}d {hours}h {mins}m"
    }

def create_container(chat_id):
    name = container_name(chat_id)
    cmd = [
        "docker", "run", "-d",
        "--name", name,
        "--memory=8g",
        "--cpus=5",
        "--restart", "unless-stopped",
        "ubuntu:22.04",
        "sleep", "infinity"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0

def get_sshx_link(chat_id):
    name = container_name(chat_id)

    # Purani sshx kill + log clear
    subprocess.run(
        ["docker", "exec", name, "bash", "-c", "pkill sshx || true && rm -f /sshx.log"],
        capture_output=True
    )
    time.sleep(1)

    # Nayi sshx start
    subprocess.run(
        ["docker", "exec", name, "bash", "-c",
         "curl -sSf https://sshx.io/get | sh -s -- -q && nohup sshx > /sshx.log 2>&1 &"],
        capture_output=True
    )
    time.sleep(5)

    result = subprocess.run(
        ["docker", "exec", name, "cat", "/sshx.log"],
        capture_output=True, text=True
    )
    clean = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', result.stdout)
    match = re.search(r'https://sshx\.io/[^\s]+', clean)
    return match.group(0) if match else None

# ── Watchdog ──────────────────────────────────────────

async def watchdog(bot: Bot):
    """Har 10 min mein sshx check karta hai — expire ho to auto new link"""
    while True:
        await asyncio.sleep(600)  # 10 minutes
        data = load_data()

        for chat_id in list(data.keys()):
            try:
                if not is_container_running(chat_id):
                    continue

                # sshx band hai?
                if not is_sshx_running(chat_id):
                    new_link = get_sshx_link(chat_id)

                    if new_link:
                        data[chat_id]["last_link"] = new_link
                        save_data(data)
                        await bot.send_message(
                            chat_id=int(chat_id),
                            text=(
                                "⚠️ Aapki Sshx link expire ho gayi thi!\n\n"
                                "✅ New link ready hai — aapka data safe hai, koi loss nahi:\n\n"
                                f"🔗 {new_link}"
                            )
                        )
            except Exception:
                continue

# ── Commands ──────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🖥️ VE VPS Manager\n\n"
        "/deploy — Naya VPS deploy karo\n"
        "/link — Sshx link lo\n"
        "/mystatus — Apna VPS status\n"
        "/serverstatus — Server ka overall status\n"
        "/delete — VPS delete karo"
    )

async def deploy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    data = load_data()

    if chat_id in data:
        await update.message.reply_text("⚠️ Aapka VPS pehle se exist karta hai! /link se link lo.")
        return

    if len(data) >= MAX_USERS:
        await update.message.reply_text(
            "❌ Limit Over!\n\nServer ke saare slots full ho gaye.\nGood Luck Next Time! 🍀"
        )
        return

    await update.message.reply_text("⏳ VPS deploy ho raha hai...")

    if not create_container(chat_id):
        await update.message.reply_text("❌ Deploy mein error. Dobara try karein.")
        return

    data[chat_id] = {"container": container_name(chat_id), "status": "running"}
    save_data(data)

    await update.message.reply_text(
        "✅ VPS Successfully Deployed!\n\n"
        f"🖥️ Container: vps_user_{chat_id}\n"
        "💾 RAM: 8GB\n⚙️ CPU: 5 cores\n💿 Disk: 60GB\n\n"
        "🔗 /link se sshx link lo"
    )

async def get_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    data = load_data()

    if chat_id not in data:
        await update.message.reply_text("❌ Pehle /deploy karein!")
        return

    if not is_container_running(chat_id):
        await update.message.reply_text("❌ VPS band hai.")
        return

    await update.message.reply_text("⏳ Link fetch ho rahi hai...")
    link = get_sshx_link(chat_id)

    if link:
        data[chat_id]["last_link"] = link
        save_data(data)
        await update.message.reply_text(f"🔗 Aapki Sshx Link:\n{link}")
    else:
        await update.message.reply_text("❌ Link nahi mili. Dobara /link try karein.")

async def my_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    data = load_data()

    if chat_id not in data:
        await update.message.reply_text("❌ Koi VPS nahi mila. /deploy karein.")
        return

    running = is_container_running(chat_id)
    sshx_ok = is_sshx_running(chat_id) if running else False
    stats = get_container_stats(chat_id) if running else None

    msg = (
        f"📊 Aapka VPS Status\n\n"
        f"📡 VPS: {'🟢 Running' if running else '🔴 Stopped'}\n"
        f"🔗 Sshx: {'🟢 Active' if sshx_ok else '🔴 Inactive'}\n"
        f"💾 RAM: 8GB\n⚙️ CPU: 5 cores\n💿 Disk: 60GB\n"
    )

    if stats:
        msg += f"\n📈 Live Usage:\n  CPU: {stats['cpu']}\n  RAM: {stats['mem']}\n  I/O: {stats['disk_io']}\n"

    await update.message.reply_text(msg)

async def server_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = get_server_stats()
    data = load_data()

    msg = (
        f"🖥️ VPS Status\n\n"
        f"CPU: {s['cpu_percent']}% ({s['cpu_cores']} cores)\n"
        f"Load avg: {s['load'][0]:.2f}, {s['load'][1]:.2f}, {s['load'][2]:.2f}\n"
        f"RAM: {s['ram_used']:.1f}MB / {s['ram_total']:.1f}MB ({s['ram_percent']}%)\n"
        f"Disk: {s['disk_used']:.1f}GB / {s['disk_total']:.1f}GB ({s['disk_percent']}%)\n"
        f"Uptime: {s['uptime']}\n\n"
        f"👥 Active Users: {len(data)}/{MAX_USERS}\n\n"
        f"👑 Bot by @YourUsername"
    )
    await update.message.reply_text(msg)

async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    data = load_data()

    if chat_id not in data:
        await update.message.reply_text("❌ Koi VPS nahi mila.")
        return

    subprocess.run(["docker", "stop", container_name(chat_id)], capture_output=True)
    subprocess.run(["docker", "rm", container_name(chat_id)], capture_output=True)
    del data[chat_id]
    save_data(data)
    await update.message.reply_text("✅ VPS delete ho gaya.")

# ── Main ──────────────────────────────────────────────

async def post_init(app):
    asyncio.create_task(watchdog(app.bot))

def main():
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("deploy", deploy))
    app.add_handler(CommandHandler("link", get_link))
    app.add_handler(CommandHandler("mystatus", my_status))
    app.add_handler(CommandHandler("serverstatus", server_status))
    app.add_handler(CommandHandler("delete", delete))
    app.run_polling()

if __name__ == "__main__":
    main()

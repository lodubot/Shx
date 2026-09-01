import os
import subprocess
import re
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "8993593935:AAGwkSpz6g8VWeJAdj4ZSW1NaJGJYwVwsbQ"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_dir = os.path.abspath(f"user_data_{chat_id}")
    os.makedirs(user_dir, exist_ok=True)
    
    await update.message.reply_text(
        f"Aapka personal terminal folder taiyar hai!\n\n"
        f"🔗 Termius/Termux SSH link ke liye: `/link`\n"
        f"❌ Terminal delete karne ke liye: `/deletevps`"
    )

async def get_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_dir = os.path.abspath(f"user_data_{chat_id}")
    os.makedirs(user_dir, exist_ok=True)
    
    await update.message.reply_text("Tmate SSH session start ho raha hai, 5 seconds wait karein...")
    
    try:
        socket_path = os.path.join(user_dir, "tmate.sock")
        
        # Agar pehle se socket chal raha ho toh use band karein
        subprocess.run(f"tmate -S {socket_path} kill-session", shell=True)
        
        # Naya tmate session background (detached mode) mein start karein
        start_cmd = f"cd {user_dir} && tmate -S {socket_path} new-session -d"
        subprocess.run(start_cmd, shell=True)
        
        # Tmate ko cloud par connect hone ke liye 5 seconds ka time dein
        time.sleep(5)
        
        # Tmate se SSH connection string nikalna
        res = subprocess.run(f"tmate -S {socket_path} display -p '#{tmate_ssh}'", shell=True, capture_output=True, text=True)
        ssh_command = res.stdout.strip()
        
        # Agar pehli baar mein na mile toh read-only link check karein
        if not ssh_command or "no session" in ssh_command.lower():
            res2 = subprocess.run(f"tmate -S {socket_path} display -p '#{tmate_ssh_ro}'", shell=True, capture_output=True, text=True)
            ssh_command = res2.stdout.strip()

        if not ssh_command or len(ssh_command) < 10:
            ssh_command = "Connection string nahi mili. Dobara /link try karein."
        
        await update.message.reply_text(
            f"💻 **Termux / Termius ke liye SSH Command:**\n\n`{ssh_command}`\n\n"
            f"Isko copy karke apne Termux ya Termius app mein paste karein."
        )
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def delete_vps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_dir = os.path.abspath(f"user_data_{chat_id}")
    socket_path = os.path.join(user_dir, "tmate.sock")
    
    try:
        subprocess.run(f"tmate -S {socket_path} kill-session", shell=True)
        await update.message.reply_text("❌ Aapka tmate session terminate kar diya gaya hai.")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("link", get_link))
    app.add_handler(CommandHandler("deletevps", delete_vps))
    app.run_polling()

if __name__ == "__main__":
    main()

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
    
    await update.message.reply_text("Tmate SSH session start ho raha hai, 8 seconds wait karein...")
    
    try:
        log_file = f"tmate_{chat_id}.log"
        log_path = os.path.join(user_dir, log_file)
        
        if os.path.exists(log_path):
            os.remove(log_path)
            
        subprocess.run(f"pkill -f 'tmate.*user_data_{chat_id}'", shell=True)
        
        # Tmate start karna with nohup
        cmd = f"cd {user_dir} && nohup tmate > {log_file} 2>&1 &"
        subprocess.run(cmd, shell=True)
        
        # Connection establish hone ke liye 8 seconds ka wait
        time.sleep(8)
        
        ssh_command = "SSH connection string nahi mili. Dobara /link try karein."
        
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                clean_content = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', content)
                
                # Tmate ki ssh command dhoondhna
                match = re.search(r'ssh\s+[^\s]+@[^\s]+', clean_content)
                if match:
                    ssh_command = match.group(0)
        
        await update.message.reply_text(
            f"💻 **Termux / Termius ke liye SSH Command:**\n\n`{ssh_command}`\n\n"
            f"Isko copy karke apne Termux ya Termius app mein paste karein."
        )
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def delete_vps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_dir = os.path.abspath(f"user_data_{chat_id}")
    
    try:
        subprocess.run(f"pkill -f 'tmate.*user_data_{chat_id}'", shell=True)
        log_file = f"tmate_{chat_id}.log"
        log_path = os.path.join(user_dir, log_file)
        if os.path.exists(log_path):
            os.remove(log_path)
            
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

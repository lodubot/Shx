import os
import subprocess
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "8993593935:AAGwkSpz6g8VWeJAdj4ZSW1NaJGJYwVwsbQ"

# Dictionary to store user processes/links
user_links = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_dir = os.path.abspath(f"user_data_{chat_id}")
    os.makedirs(user_dir, exist_ok=True)
    
    await update.message.reply_text(
        f"Aapka folder ban gaya hai!\n"
        f"🔗 Sshx link generate karne ke liye `/link` command bhejein."
    )

async def get_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_dir = os.path.abspath(f"user_data_{chat_id}")
    
    await update.message.reply_text("Sshx link ban rahi hai, 3-4 seconds wait karein...")
    
    try:
        # Sshx ko background mein run karke output log file mein save karna
        log_file = f"sshx_{chat_id}.log"
        cmd = f"cd {user_dir} && nohup sshx > {log_file} 2>&1 &"
        subprocess.run(cmd, shell=True)
        
        # 4 second wait karein taaki link generate ho kar log file mein aa jaye
        import time
        time.sleep(4)
        
        # Log file se link read karna
        log_path = os.path.join(user_dir, log_file)
        link = "Link nahi mili. Dobara /link try karein."
        
        if os.path.exists(log_path):
            with open(log_path, "r") as f:
                content = f.read()
                for line in content.splitlines():
                    if "https://sshx.io/" in line:
                        link = line.strip()
                        break
        
        await update.message.reply_text(f"🔗 **Aapki Sshx Link:**\n{link}")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("link", get_link))
    app.run_polling()

if __name__ == "__main__":
    main()

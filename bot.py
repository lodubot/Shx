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
        f"🔗 Link lene ke liye: `/link`\n"
        f"❌ Terminal/Link delete karne ke liye: `/deletevps`"
    )

async def get_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_dir = os.path.abspath(f"user_data_{chat_id}")
    os.makedirs(user_dir, exist_ok=True)
    
    await update.message.reply_text("Sshx link fetch ki ja rahi hai, 3 seconds wait karein...")
    
    try:
        log_file = f"sshx_{chat_id}.log"
        log_path = os.path.join(user_dir, log_file)
        
        if os.path.exists(log_path):
            os.remove(log_path)
            
        # Sshx ko background mein run karein
        cmd = f"cd {user_dir} && nohup sshx > {log_file} 2>&1 &"
        subprocess.run(cmd, shell=True)
        
        time.sleep(3)
        
        link = "Link nahi mili. Dobara /link try karein."
        
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                clean_content = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', content)
                match = re.search(r'https://sshx\.io/[^\s]+', clean_content)
                if match:
                    link = match.group(0)
        
        await update.message.reply_text(f"🔗 **Aapki Sshx Link:**\n{link}")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

# /deletevps command - Sshx process aur link band karne ke liye
async def delete_vps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_dir = os.path.abspath(f"user_data_{chat_id}")
    
    try:
        # Us user ke folder se chal rahe 'sshx' process ko dhoondh kar band karna
        subprocess.run(f"pkill -f 'sshx.*user_data_{chat_id}'", shell=True)
        # Ek aam tarika: us user ke directory wale sabhi sshx processes kill karna
        subprocess.run(f"killall sshx", shell=True) # (Agar sabhi ka alag process ho toh pkill behtar hai)
        
        # Log file delete karna
        log_file = f"sshx_{chat_id}.log"
        log_path = os.path.join(user_dir, log_file)
        if os.path.exists(log_path):
            os.remove(log_path)
            
        await update.message.reply_text("❌ Aapka terminal session aur sshx link successfully delete/terminate kar di gayi hai.")
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

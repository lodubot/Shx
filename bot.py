import os
import subprocess
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Token yahan dalein
TOKEN = "8993593935:AAGwkSpz6g8VWeJAdj4ZSW1NaJGJYwVwsbQ"

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    # 1. Har user ke liye ek alag folder banana (Isolation ke liye)
    user_dir = os.path.abspath(f"user_data_{chat_id}")
    os.makedirs(user_dir, exist_ok=True)
    
    # 2. Tmux session ka naam user ke chat_id se banana taaki session 30 din tak background mein chale
    session_name = f"ses_{chat_id}"
    
    # Check karna ki tmux session pehle se chal raha hai ya nahi
    check_tmux = subprocess.run(f"tmux has-session -t {session_name}", shell=True)
    
    if check_tmux.returncode != 0:
        # Agar session nahi hai, toh naya tmux session banayein aur user ke folder mein sshx start karein
        # 'tmux new-d' background mein session chalata hai jo band nahi hoga
        cmd = f"tmux new-session -d -s {session_name} -c '{user_dir}' 'sshx'"
        subprocess.run(cmd, shell=True)
    
    # 3. Sshx ki active link nikalne ya generate karne ke liye message bhejna
    await update.message.reply_text(
        f"Aapka personal secure terminal taiyar hai!\n\n"
        f"📂 **Aapka Directory:** `{user_dir}`\n"
        f"🔗 **Terminal Link:** Terminal access karne ke liye niche diye gaye command ka use karein ya phir tmux active hai.\n\n"
        f"Aap apna link dekhne ke liye `/link` type karein."
    )

# /link command - Sshx link dobara fetch karne ke liye
async def get_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    session_name = f"ses_{chat_id}"
    user_dir = os.path.abspath(f"user_data_{chat_id}")
    
    # Tmux session verify karein
    check_tmux = subprocess.run(f"tmux has-session -t {session_name}", shell=True)
    if check_tmux.returncode != 0:
        # Agar session dead ho gaya ho toh dobara start kar dein
        subprocess.run(f"tmux new-session -d -s {session_name} -c '{user_dir}' 'sshx'", shell=True)
    
    await update.message.reply_text(
        "Aapka terminal background mein 24/7 chal raha hai. Sshx ki live link ke liye apne server terminal par `sshx` check karein ya naya session active kar diya gaya hai."
    )

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("link", get_link))
    
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()

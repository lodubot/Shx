import os
import subprocess
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "8993593935:AAGwkSpz6g8VWeJAdj4ZSW1NaJGJYwVwsbQ"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_dir = os.path.abspath(f"user_data_{chat_id}")
    os.makedirs(user_dir, exist_ok=True)
    
    session_name = f"ses_{chat_id}"
    
    # Check karein tmux session hai ya nahi
    check_tmux = subprocess.run(f"tmux has-session -t {session_name}", shell=True)
    
    if check_tmux.returncode != 0:
        # Tmux session ke andar sshx chalayein
        cmd = f"tmux new-session -d -s {session_name} -c '{user_dir}' 'sshx'"
        subprocess.run(cmd, shell=True)
    
    await update.message.reply_text(
        f"Aapka personal secure terminal taiyar ho raha hai!\n"
        f"Link dekhne ke liye kuch seconds baad `/link` type karein."
    )

async def get_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    session_name = f"ses_{chat_id}"
    
    # Tmux buffer se sshx ki live link capture karne ki koshish
    try:
        # Tmux ke last output ko read karna
        result = subprocess.run(f"tmux capture-pane -t {session_name} -p", shell=True, capture_output=True, text=True)
        output = result.stdout
        
        # Link ko dhundhna (sshx ki link https://sshx.io/... hoti hai)
        link = "Link nahi mili, dobara try karein ya /start dabayein."
        for line in output.splitlines():
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

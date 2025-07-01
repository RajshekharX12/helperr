async def notify_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    notifications_enabled[user_id] = False
    await update.message.reply_text("🔕 Auto notifications OFF.")

def periodic_checker(application):
    while True:
        logging.info("[AUTO CHECK] Triggered")
        for user_id, nums in tracked_numbers.items():
            if not notifications_enabled.get(user_id, True):
                continue
            msg = "🔔 Auto Check:\n"
            for num in nums:
                result = check_fragment_number(num)
                msg += f"{num} → {result}\n"
            try:
                application.bot.send_message(chat_id=user_id, text=msg)
            except Exception as e:
                logging.warning(f"[ERROR] Failed to notify {user_id}: {e}")
        time.sleep(3 * 60 * 60)

def main():
    from dotenv import load_dotenv
    import os
    load_dotenv()
    TOKEN = os.getenv("BOT_TOKEN")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setnumbers", set_numbers))
    app.add_handler(CommandHandler("removenum", remove_number))
    app.add_handler(CommandHandler("checknum", check_now))
    app.add_handler(CommandHandler("check1", check_single))
    app.add_handler(CommandHandler("notifyon", notify_on))
    app.add_handler(CommandHandler("notifyoff", notify_off))

    thread = Thread(target=periodic_checker, args=(app,), daemon=True)
    thread.start()

    app.run_polling()

if name == 'main':
    main()

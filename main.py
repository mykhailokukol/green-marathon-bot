from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from bot.base import start
from bot.config import settings


def main():
    app = ApplicationBuilder().token(settings.TG_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))

    app.run_polling()


if __name__ == "__main__":
    main()

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from bot.base import (
    start,
    cancel,
    choose_city,
    type_name,
    type_email,
    delivery_question,
    frequency_question,
    finish,
    send_notification,
    send_last_notification,
)
from bot.base import (
    CHOOSE_CITY,
    TYPE_NAME,
    TYPE_EMAIL,
    DELIVERY_QUESTION,
    FREQUENCY_QUESTION,
    FINISH,
)
from bot.config import settings


def main():
    app = ApplicationBuilder().token(settings.TG_TOKEN).build()

    # Handlers
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSE_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_city)],
            TYPE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, type_name)],
            TYPE_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, type_email)],
            DELIVERY_QUESTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, delivery_question)
            ],
            FREQUENCY_QUESTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, frequency_question)
            ],
            FINISH: [MessageHandler(filters.TEXT & ~filters.COMMAND, finish)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )
    app.add_handler(conv_handler)

    app.add_handler(CommandHandler("send", send_notification))
    app.add_handler(CommandHandler("last", send_last_notification))

    app.run_polling()


if __name__ == "__main__":
    main()

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
    ad_agreement,
    finish,
    notification_choose_city,
    notification_send,
    send_last_notification,
)
from bot.base import (
    CHOOSE_CITY,
    TYPE_NAME,
    TYPE_EMAIL,
    DELIVERY_QUESTION,
    AD_AGREEMENT,
    FINISH,
    NOTIFICATION_SEND,
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
            AD_AGREEMENT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ad_agreement)
            ],
            FINISH: [MessageHandler(filters.TEXT & ~filters.COMMAND, finish)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )
    app.add_handler(conv_handler)

    moderator_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("send", notification_choose_city)],
        states={
            NOTIFICATION_SEND: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, notification_send)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
        ],
        allow_reentry=True,
    )
    app.add_handler(moderator_conv_handler)

    app.add_handler(CommandHandler("last", send_last_notification))

    # Do run
    app.run_polling()


if __name__ == "__main__":
    main()

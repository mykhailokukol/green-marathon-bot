import datetime
import logging
import secrets

from telegram import (
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.ext import ContextTypes, ConversationHandler

from bot.config import settings
from bot.db import USERS_COLLECTION, CITIES_COLLECTION, GIFTS_COLLECTION
from bot.services import set_random_number

# Logging
formatter = logging.Formatter("%(levelname)s | %(name)s | %(asctime)s | %(message)s")
info_handler = logging.StreamHandler()
info_handler.setLevel(logging.INFO)
info_handler.setFormatter(formatter)
warn_handler = logging.FileHandler("logs/warn.log", mode="a", encoding="utf-8")
warn_handler.setLevel(logging.WARN)
warn_handler.setFormatter(formatter)
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
log.addHandler(info_handler)
log.addHandler(warn_handler)

# Steps
CHOOSE_CITY, TYPE_NAME, TYPE_EMAIL, DELIVERY_QUESTION, FREQUENCY_QUESTION, FINISH = (
    range(6)
)

SUPER_GIFT = "«Колонка умная SberBoom Mini с голосовым ассистентом Салют»"


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    # Log data
    log.warn(f"User [{update.message.from_user.id}] pressed /start")

    # Save user data
    user_exists = USERS_COLLECTION.find({"user_id": update.message.from_user.id})
    user_exists = await user_exists.to_list(length=None)

    if user_exists:
        await update.message.reply_text(
            "Вы уже зарегестрированы",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END
    else:
        # Welcome message + ask for confidential data
        markup = ReplyKeyboardMarkup(
            [
                [
                    "Да",
                    "Нет",
                ]
            ]
        )
        await update.message.reply_text(
            "Здравствуйте! Это чат-бот СберМаркета. Чтобы получить гарантированный приз и стать участником главного розыгрыша, вам нужно заполнить мини-анкету.\n\nВы согласны на обработку персональных данных и получение сообщений от СберМаркета?",
            reply_markup=markup,
        )

    # Next step
    return CHOOSE_CITY


async def choose_city(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    private_data_acception = update.message.text.lower()
    if private_data_acception == "нет":
        await update.message.reply_text(
            "Ой! Чтобы получить гарантированный подарок и участвовать в главном розыгрыше, нужно согласиться на обработку персональных данных.\nДля этого введите /start",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END

    # City chooser dialog
    cities_cursor = CITIES_COLLECTION.find({})
    cities = await cities_cursor.to_list(length=None)
    markup = ReplyKeyboardMarkup(
        [[InlineKeyboardButton(city["name"])] for city in cities]
    )
    await update.message.reply_text(
        "Отлично! Давайте познакомимся. Из какого Вы города? Выберите нужный из списка ниже.",
        reply_markup=markup,
    )

    # Next step
    return TYPE_NAME


async def type_name(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    context.user_data["city"] = update.message.text

    await update.message.reply_text(
        "Как вас зовут? Введите свои ФИО в поле ниже.",
        reply_markup=ReplyKeyboardRemove(),
    )

    # Next step
    return TYPE_EMAIL


async def type_email(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    context.user_data["name"] = update.message.text

    await update.message.reply_text(
        "Укажите, пожалуйста, ваш email.",
        reply_markup=ReplyKeyboardRemove(),
    )

    # Next step
    return DELIVERY_QUESTION


async def delivery_question(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    context.user_data["email"] = update.message.text

    markup = ReplyKeyboardMarkup(
        [
            ["Заказываю еду"],
            ["Заказываю продукты"],
            ["И то и другое"],
            ["Нет"],
        ]
    )
    await update.message.reply_text(
        "Вы заказываете доставку готовой еды и продуктов?",
        reply_markup=markup,
    )

    # Next step
    return FREQUENCY_QUESTION


async def frequency_question(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    context.user_data["delivery"] = update.message.text

    markup = ReplyKeyboardMarkup(
        [
            ["Несколько раз в неделю"],
            ["Несколько раз в месяц"],
            ["Несколько раз в год"],
        ]
    )
    await update.message.reply_text(
        "Как часто вы заказываете еду онлайн?",
        reply_markup=markup,
    )

    # Next step
    return FINISH


async def finish(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    context.user_data["frequency"] = update.message.text

    # Give 1 random gift from DB
    # gifts_cursor = GIFTS_COLLECTION.find({})
    # gifts_cursor = GIFTS_COLLECTION.find({"count": {"$gt": 0}})
    # gifts = await gifts_cursor.to_list(length=None)
    # if not gifts:
    #     await update.message.reply_text(
    #         "Все подарки закончились",
    #         reply_markup=ReplyKeyboardRemove(),
    #     )
    # else:
    #     gift = random.choice(gifts)
    #     await update.message.reply_text(
    #         f"Спасибо за прохождение анкеты, ваш подарок: {gift['name']}",
    #         reply_markup=ReplyKeyboardRemove(),
    #     )

    # Save to DB
    user_data = {
        "datetime_joined": datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
        "user_id": update.message.from_user.id,
        "private_data_access": True,
        "fullname": context.user_data["name"],
        "email": context.user_data["email"],
        "city": context.user_data["city"],
        "delivery_method": context.user_data["delivery"],
        "delivery_frequency": context.user_data["frequency"],
    }
    await USERS_COLLECTION.insert_one(user_data)

    # Super giveaway
    number = await set_random_number(USERS_COLLECTION)
    text = f"Спасибо, что заполнили анкету! Теперь вы можете забрать свой подарок на стойке СберМаркета.\n\nТакже вы становитесь участником нашего большого розыгрыша. Ваш уникальный номер – {number}. Уже вечером, в хх:00 мы определим, кто же получит главный приз. Не пропустите!"
    await update.message.reply_text(
        text=text,
        reply_markup=ReplyKeyboardRemove(),
    )

    # End
    return ConversationHandler.END


async def cancel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """No description needed"""
    await update.message.reply_text(
        "Прекращаем последнюю операцию.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


async def send_notification(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if int(update.message.from_user.id) == int(settings.MODERATOR_ID):
        cities_cursor = CITIES_COLLECTION.find({})
        cities = await cities_cursor.to_list(length=None)

        for city in cities:
            users_cursor = USERS_COLLECTION.find({"city": city["name"]})
            users = await users_cursor.to_list(length=None)
            try:
                winner = secrets.choice(users)
            except IndexError:
                log.warn(f"No participants for city: {city['name']}")
                continue

            await USERS_COLLECTION.update_one(
                {"user_id": winner["user_id"]},
                {"$set": {"won_city_prize": True}},
            )

            await context.bot.send_message(
                chat_id=winner["user_id"],
                text=f"Поздравляем, Вы выиграли {SUPER_GIFT}!\nПолучите его на стенде до 15:00",
            )

        await update.message.reply_text(
            "Рассылка отправлена и получена пользователями.",
            reply_markup=ReplyKeyboardRemove(),
        )

        log.warn("Notifications sent.")


async def send_last_notification(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if int(update.message.from_user.id) == int(settings.MODERATOR_ID):
        users_cursor = USERS_COLLECTION.find({})
        users = await users_cursor.to_list(length=None)

        for user in users:
            await context.bot.send_message(
                chat_id=user["user_id"],
                text="В конце дня уведомление текст еще текст и прочий текст",
            )

        await update.message.reply_text(
            "Рассылка отправлена и получена пользователями.",
            reply_markup=ReplyKeyboardRemove(),
        )

        log.warn("Last notifications sent.")

import datetime
import logging
import random

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.ext import ContextTypes, ConversationHandler, CallbackContext

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


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    # Welcome message + ask for confidential data
    markup = ReplyKeyboardMarkup(
        [
            InlineKeyboardButton("Разрешить"),
            InlineKeyboardButton("Не разрешать"),
        ]
    )
    await update.message.reply_text(
        "Приветственное сообщение\nСогласие о предоставлении персональных данных и на получение рассылок",
        reply_markup=markup,
    )

    # Log data
    log.warn(f"User [{update.message.from_user.id}] pressed /start")

    # Save user data
    # TODO: Move to the start of the next step ?
    user_exists = USERS_COLLECTION.find({"user_id": update.message.from_user.id})
    user_exists = await user_exists.to_list(length=None)

    if user_exists:
        # TODO: Negotiate with customer
        await update.message.reply_text("Вы уже принимаете участие")
        return ConversationHandler.END
    else:
        user_data = {
            "datetime_joined": datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
            "user_id": update.message.from_user.id,
        }
        await USERS_COLLECTION.insert_one(user_data)

    # Next step
    return CHOOSE_CITY


async def choose_city(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    private_data_acception = update.message.text.lower()
    if private_data_acception == "не разрешать":
        await update.message.reply_text(
            "Если хотите получить подарок, необходимо заполнить анкету. Если передумаете, /start"
        )
        return ConversationHandler.END

    # City chooser dialog
    markup = ReplyKeyboardMarkup(
        [
            InlineKeyboardButton(city["name"])
            for city in CITIES_COLLECTION.find({}).to_list(length=None)
        ]
    )
    await update.message.reply_text(
        "Выберите город: ",
        reply_markup=markup,
    )

    # Next step
    return TYPE_NAME


async def type_name(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    context.user_data["city"] = update.message.text

    await update.message.reply_text("Введите ФИО: ")

    # Next step
    return TYPE_EMAIL


async def type_email(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    context.user_data["name"] = update.message.text

    await update.message.reply_text("Введите почту: ")

    # Next step
    return DELIVERY_QUESTION


async def delivery_question(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    context.user_data["email"] = update.message.text

    markup = ReplyKeyboardMarkup(
        [
            InlineKeyboardButton("Готовую еду"),
            InlineKeyboardButton("Продукты"),
            InlineKeyboardButton("Заказываю и то, и другое"),
        ]
    )
    await update.message.reply_text(
        "Заказываете готовую еду или продукты для готовки?",
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
            InlineKeyboardButton("Несколько раз в неделю"),
            InlineKeyboardButton("Несколько раз в месяц"),
            InlineKeyboardButton("Несколько раз в год"),
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
    gifts = await GIFTS_COLLECTION.find({"count": {"$gt": 0}}).to_list()
    if not gifts:
        await update.message.reply_text("Все подарки закончились")
    else:
        gift = random.choice(gifts)
        await update.message.reply_text(
            f"Спасибо за прохождение анкеты, ваш подарок: {gift}"
        )

    # Super giveaway
    super_gift = "..."
    number = await set_random_number(USERS_COLLECTION)
    text = f"Поздравляем! Вы становитесь участником розыгрыша главного приза {super_gift}, ваш номер {number}.\nС правилами розыгрыша можете ознакомиться в описании бота. В случае выигрыша Вы получите уведомление в боте с такого-то по такое-то время, за ним необходимо будет прийти на стенд и показать сообщение промоутеру."
    await update.message.reply_text(text=text)

    # End
    return ConversationHandler.END

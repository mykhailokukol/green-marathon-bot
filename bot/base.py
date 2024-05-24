import re
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
from telegram.constants import ParseMode

from bot.config import settings
from bot.db import USERS_COLLECTION, CITIES_COLLECTION
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
CHOOSE_CITY, TYPE_NAME, TYPE_EMAIL, DELIVERY_QUESTION, FINISH = range(5)
NOTIFICATION_SEND = 5

SUPER_GIFT = "«Колонка умная SberBoom Mini с голосовым ассистентом Салют»"


async def validate(field: str, value: str):
    match field:
        case "start":
            return value.lower() in ["да", "нет"]
        case "city":
            cities_cursor = CITIES_COLLECTION.find({})
            cities = await cities_cursor.to_list(length=None)
            return value in [city["name"] for city in cities]
        case "name":
            return len(value.split(" ")) == 3
        case "email":
            return bool(
                re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", value)
            )
        case "delivery":
            return value in [
                "Заказываю еду",
                "Заказываю продукты",
                "И то и другое",
                "Нет",
            ]


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
        welcome_message_file_path = "media/Согласие_на_получение_рекламы_акции.pdf"
        welcome_message = (
            # "<b>Согласие на получение рекламы</b>"
            # "\n\nЯ, субъект персональных данных, предоставляю ООО «Инстамарт Сервис» («<b>Оператор</b>»)"
            # "(место нахождения: 115035, г. Москва, ул. Садовническая, д. 9А, этаж 5, помещ. I, ком. 1)"
            # "согласие на обработку персональных данных."
            # "\n\n<b>Цели обработки персональных данных:</b> на направление мне Оператором новостных и рекламных сообщений,"
            # "в том числе, о проводимых акциях, мероприятиях, специальных предложениях Оператора и его партнеров,"
            # "любым способом, в том числе, посредством электронной почты, сетей электросвязи, SMS-сообщений,"
            # "push-сообщений, сообщений в мессенджерах с официальных аккаунтов СберМаркета,"
            # "а также с использованием прочих каналов коммуникации, предполагающих прямой контакт со мной."
            # "\n\n<b>Перечень обрабатываемых персональных данных:</b> фамилия, имя, отчество;"
            # "телефонные номера, адреса электронной почты."
            # "\n\n<b>Способы и средства обработки персональных данных:</b> любые действия (операции),"
            # "допустимые законодательством, совершаемые как с использованием средств автоматизации,"
            # "так и без использования таких средств или смешанным образом, включая сбор, запись, систематизацию,"
            # "накопление, хранение, уточнение (обновление, изменение), извлечение, использование,"
            # "передачу (предоставление, доступ, включая трансграничную), блокирование, удаление, уничтожение."
            # "\n\n<b>Передача и поручение обработки персональных данных:</b> обработка осуществляется Оператором,"
            # "а также третьими лицами, которые привлечены Оператором к обработке,"
            # "или которым переданы персональные данные (или предоставлен доступ к ним) в указанных целях в соответствии"
            # "с законодательством. Перечень таких лиц доступен по ссылке: https://sbermarket.ru/sp/data-processors-marketing "
            # "\n\n<b>Срок обработки персональных данных и способ отзыва согласия:</b> согласие действует"
            # "в течение 5 (пяти) лет с даты предоставления согласия. "
            # "Согласие может быть отозвано путем направления заявления по адресу dpo@sbermarket.ru."
            # "\n\nПри этом Оператор вправе продолжить обработку персональных данных"
            # "при наличии иного законного основания."
            "Здравствуйте! Это чат-бот СберМаркета. Чтобы получить гарантированный приз и стать участником главного розыгрыша, вам нужно заполнить мини-анкету."
            "\n\nВы согласны на обработку персональных данных и получение сообщений от СберМаркета?"
        )
        with open(welcome_message_file_path, "rb") as file:
            await update.message.reply_document(
                caption=welcome_message,
                reply_markup=markup,
                document=file,
                # parse_mode=ParseMode.HTML,
            )

    # Next step
    return CHOOSE_CITY


async def choose_city(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    private_data_acception = update.message.text.lower()

    if not await validate("start", private_data_acception):
        await update.message.reply_text(
            "❌ Ошибка: Выберите значение из перечисленных ниже.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return await start(update, context)

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

    if not await validate("city", context.user_data["city"]):
        await update.message.reply_text(
            "❌ Ошибка: Выберите значение из перечисленных ниже.",
            reply_markup=ReplyKeyboardRemove(),
        )
        # City chooser dialog
        cities_cursor = CITIES_COLLECTION.find({})
        cities = await cities_cursor.to_list(length=None)
        markup = ReplyKeyboardMarkup(
            [[InlineKeyboardButton(city["name"])] for city in cities]
        )
        await update.message.reply_text(
            "Из какого Вы города? Выберите нужный из списка ниже.",
            reply_markup=markup,
        )
        return TYPE_NAME

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
    if not await validate("name", context.user_data["name"]):
        await update.message.reply_text(
            "❌ Ошибка: Введите полные фамилию, имя и отчество.",
            reply_markup=ReplyKeyboardRemove(),
        )
        await update.message.reply_text(
            "Как вас зовут? Введите свои ФИО в поле ниже.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return TYPE_EMAIL

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
    if not await validate("email", context.user_data["email"]):
        await update.message.reply_text(
            "❌ Ошибка: Введите корректный email.",
            reply_markup=ReplyKeyboardRemove(),
        )

        return DELIVERY_QUESTION

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
    return FINISH


# async def frequency_question(
#     update: Update,
#     context: ContextTypes.DEFAULT_TYPE,
# ) -> int:
#     context.user_data["delivery"] = update.message.text

#     markup = ReplyKeyboardMarkup(
#         [
#             ["Несколько раз в неделю"],
#             ["Несколько раз в месяц"],
#             ["Несколько раз в год"],
#         ]
#     )
#     await update.message.reply_text(
#         "Как часто вы заказываете еду онлайн?",
#         reply_markup=markup,
#     )

#     # Next step
#     return FINISH


async def finish(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    context.user_data["delivery"] = update.message.text

    if not await validate("delivery", context.user_data["delivery"]):
        await update.message.reply_text(
            "❌ Ошибка: Выберите значение из перечисленных ниже.",
            reply_markup=ReplyKeyboardRemove(),
        )
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

        return FINISH

    # Save to DB
    user_data = {
        "datetime_joined": datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
        "user_id": update.message.from_user.id,
        "private_data_access": True,
        "fullname": context.user_data["name"],
        "email": context.user_data["email"],
        "city": context.user_data["city"],
        "delivery_method": context.user_data["delivery"],
        "won_city_prize": False,
        # "delivery_frequency": context.user_data["frequency"],
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


async def notification_choose_city(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    if int(update.message.from_user.id) != int(settings.MODERATOR_ID):
        return

    cities_cursor = CITIES_COLLECTION.find({})
    cities = await cities_cursor.to_list(length=None)

    markup = ReplyKeyboardMarkup([[city["name"]] for city in cities])

    await update.message.reply_text(
        "Выберите город победителя: ",
        reply_markup=markup,
    )

    # Next step
    return NOTIFICATION_SEND


async def notification_send(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    city_name = update.message.text
    winner = None

    users_cursor = USERS_COLLECTION.find({"city": city_name, "won_city_prize": False})
    users = await users_cursor.to_list(length=None)
    try:
        winner = secrets.choice(users)
    except IndexError:
        log.warn(f"No participants for city: {city_name}")

    if winner:
        await USERS_COLLECTION.update_one(
            {"user_id": winner["user_id"]},
            {"$set": {"won_city_prize": True}},
        )

        await context.bot.send_message(
            chat_id=winner["user_id"],
            text=f"Поздравляем, Вы выиграли {SUPER_GIFT}!\nПолучите его на стенде до 15:00",
        )

        await update.message.reply_text(
            f"Сообщение отправлено победителю [{winner['user_id']}].",
            reply_markup=ReplyKeyboardRemove(),
        )
    else:
        await update.message.reply_text(
            "В городе нет или не осталось участников.",
            reply_markup=ReplyKeyboardRemove(),
        )

    return ConversationHandler.END


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


# DRY is for weak people.

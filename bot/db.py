import motor.motor_asyncio

from bot.config import settings


# Client
mongodb_client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_CLIENT_URL)
db = mongodb_client["green-marathon"]

# Collections
USERS_COLLECTION = db["users"]
CITIES_COLLECTION = db["cities"]
GIFTS_COLLECTION = db["gifts"]
PROMOCODES_COLLECTION = db["promocodes"]

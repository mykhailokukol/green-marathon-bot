import random


async def set_random_number(collection) -> int:
    number = random.randint(10000, 99999)
    number_exists = await collection.find_one({"number": number})
    if number_exists:
        await set_random_number(collection)
    return number


async def get_available_promocode(collection) -> str:
    promocode = await collection.find_one({"available": True})
    if promocode:
        await collection.update_one(
            {"name": promocode["name"]},
            {"$set": {"available": False}},
        )
        return promocode["name"]
    return "[Промокоды закончились]"

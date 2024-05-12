import random


async def set_random_number(collection) -> int:
    number = random.randint(10000, 99999)
    number_exists = await collection.find_one({"number": number})
    if number_exists:
        await set_random_number(collection)
    return number

import motor.motor_asyncio


# Create a Database Connection
client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://127.0.0.1:27017")
# client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://127.0.0.1:27017")
database = client["dm-project"]
collection = database["collection_social_media_api"]  # ✅ Correct collection name

import pandas as pd
from fastapi import FastAPI, UploadFile, File
import motor.motor_asyncio
import io

app = FastAPI()

# ✅ Correct MongoDB Connection & Collection Reference
client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://127.0.0.1:27017")
db = client["dm-project"]  # Ensure this matches your database name
collection = db["collection_social_media_api"]  # Correctly reference your collection

@app.post("/reload-csv/")
async def reload_csv(file: UploadFile = File(...)):
    try:
        # Read CSV file into a pandas DataFrame
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode("utf-8")))

        # Convert DataFrame to a list of dictionaries
        data = df.to_dict(orient="records")

        # ✅ Clear existing data in collection before inserting new records
        await collection.delete_many({})

        # ✅ Insert new data
        if data:
            await collection.insert_many(data)

        return {"message": "CSV data successfully reloaded!", "rows_inserted": len(data)}

    except Exception as e:
        return {"error": str(e)}



from fastapi import FastAPI
from modules.social_media.router import social_media_router
import motor.motor_asyncio

# Initialize FastAPI app
app = FastAPI(title="Hashtag Virality & Engagement Analysis")

# Register the router
app.include_router(social_media_router)

# Database connection
client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://127.0.0.1:27017")
database = client["dm-project"]

# Run the FastAPI server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)

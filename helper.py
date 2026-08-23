import os
import re
from datetime import datetime, timezone, date

import numpy as np
import pandas as pd
import requests
from fastapi import HTTPException
import httpx
from config.db_connection import database
from config.paths import file_path
from config.tokens import BEARER_TOKEN
from utils.main_router import main_router

social_media_router = main_router
collection_social_media_api = database["collection_social_media_api"]
collection_social_media_csv = database["social_media_csv_data"]
collection_social_media_filtered_csv = database["social_media_filtered_csv_data"]

# API tokens (loaded from environment variables — see .env.example)
APIFY_TOKEN = os.getenv("APIFY_TOKEN")
ENSEMBLE_TOKEN = os.getenv("ENSEMBLE_TOKEN")


# Headers with authentication
headers = {
    "Authorization": f"Bearer {BEARER_TOKEN}",
    "Content-Type": "application/json"
}



# Asynchronous route to fetch data
async def fetch_api_data(keyword):
    url = f"https://ensembledata.com/apis/tt/hashtag/recent-posts?name={keyword}&days=90&remap_output=true&max_cursor=100&token={ENSEMBLE_TOKEN}"
    # url = f"https://api.apify.com/v2/acts/apify~instagram-hashtag-scraper/runs/last/dataset/items?token={APIFY_TOKEN}"  # External API URL
    # try:
    #     # Use httpx.AsyncClient to make a request
    #     async with httpx.AsyncClient() as client:
    #         response = await client.get(url)
    #         print("response", response)
    #         response.raise_for_status()  # Raise exception for HTTP errors
    #         print("data", response.json())
    #     return response.json()  # Return the JSON response
    # except httpx.RequestError as e:
    #     # Handle connection errors
    #     raise HTTPException(status_code=500, detail=f"Request error: {e}")
    # except httpx.HTTPStatusError as e:
    #     # Handle HTTP errors
    #     raise HTTPException(status_code=response.status_code, detail=f"HTTP error: {e}")

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {url}: {e}")
        return None


#
def fetch_instagram_api_data():
    url = f"https://api.apify.com/v2/acts/apify~instagram-scraper/runs/last/dataset/items?token={APIFY_TOKEN}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {url}: {e}")
        return None


async def loadCSV():
    # Read CSV data
    data_one_csv = file_path + "/modules/social_media/data_one.csv"  
    df = pd.read_csv(data_one_csv)

    # Replace NaN with None
    df = df.replace({np.nan: None})

    # Extract hashtags and calculate engagement
    df["Extracted_Hashtags"] = df["Status text"].apply(extract_hashtags)
    df["Engagement_Score"] = df["like_count"] + df["retweet_count"] + df["reply_count"]

    # Convert Date1 column to datetime format
    df["Date1"] = pd.to_datetime(df["Date1"], errors="coerce")

    # Convert DataFrame to dictionary format for MongoDB
    data = df[["Date1", "Extracted_Hashtags", "Engagement_Score"]].to_dict(orient="records")

    # Get existing data
    existing_data = await collection_social_media_csv.find({}, {"Date1": 1}).to_list(None)
    existing_dates = set(item["Date1"] for item in existing_data)

    # Filter out duplicates before inserting
    unique_data = [item for item in data if item["Date1"] not in existing_dates]

    if unique_data:
        result = await collection_social_media_csv.insert_many(unique_data)  # ✅ Added `await`
        return {"message": "Inserted data", "inserted_count": len(result.inserted_ids)}

    return {"message": "No unique data to insert"}


async def loadFilteredCSV():
    # Read CSV data
    data_one_csv = file_path + "/modules/social_media/data_one.csv"
    df = pd.read_csv(data_one_csv)

    # Replace NaN with None
    df = df.replace({np.nan: None})

    # Extract hashtags and calculate engagement
    df["Extracted_Hashtags"] = df["Status text"].apply(extract_hashtags)
    df["Engagement_Score"] = df["like_count"] + df["retweet_count"] + df["reply_count"]

    # Convert Date1 column to datetime format
    df["Date1"] = str(pd.to_datetime(df["Date1"], errors="coerce"))

    # Convert DataFrame to dictionary format for MongoDB
    data = df[["Date1", "Extracted_Hashtags", "Engagement_Score"]].to_dict(orient="records")

    # Get existing data
    existing_data = await collection_social_media_filtered_csv.find({}, {"Date1": 1}).to_list(None)
    existing_dates = set(item["Date1"] for item in existing_data)

    # Filter out duplicates before inserting
    unique_data = [item for item in data if item["Date1"] not in existing_dates]

    if unique_data:
        result = await collection_social_media_filtered_csv.insert_many(unique_data)  # ✅ Added `await`
        return {"message": "Inserted data", "inserted_count": len(result.inserted_ids)}

    return {"message": "No unique data to insert"}


async def loadFilteredAPI():
    data = fetch_instagram_api_data()
    existing_data = await collection_social_media_api.find({}, {"id": 1}).to_list(None)
    existing_item = set(user["id"] for user in existing_data)
    return existing_item

    # Filter out duplicates before inserting
    unique_data = [item for item in data if item["id"] not in existing_item]

    if unique_data:
        result = collection_social_media_api.insert_many(unique_data)
        print("result", result)
        return {"message": "Inserted data"}

    return {"message": "No unique data to insert"}



# Function to extract hashtags
def extract_hashtags(text):
    return re.findall(r"#\w+", text)  # Extracts words starting with #


# Function to extract hashtags from text
def extract_hashtag(text):
    return re.findall(r"#\w+", text) if isinstance(text, str) else []

# Get data from database for Data Quality and Visualization
async def get_data_from_mongodb():
    try:
        data = []
        async for item in await collection_social_media_api.find():
            item['_id'] = str(item['_id'])
            data.append(item)
        return data
    except Exception as e:
        raise ValueError(f"Error retrieving data from MongoDB: {e}")


def convert_date(date_input):  # More descriptive argument name
    """Converts a date input (string or date object) to the desired format."""

    if isinstance(date_input, str):  # Check if it's a string
        try:
            date_obj = datetime.strptime(date_input, "%Y-%m-%d").date()  # Parse string to date object
        except ValueError:
            return "Invalid date format (string)"  # Specific error message
    elif isinstance(date_input, date):  # Check if it's a date object
        date_obj = date_input  # Already a date object, no need to parse
    else:
        return "Invalid date input type"  # Handle other input types

    target_date = datetime(2021, 9, 15, 0, 0, 0, 0, tzinfo=timezone.utc)
    formatted_date = target_date.isoformat().replace("Z", "+00:00")

    return formatted_date

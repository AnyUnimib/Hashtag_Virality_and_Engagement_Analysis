import pandas as pd # type: ignore
from fastapi import BackgroundTasks, Query, HTTPException  # type: ignore
import re
from collections import Counter

from pymongo import ASCENDING, DESCENDING
from pandas_profiling import ProfileReport

from config.db_connection import database
from modules.social_media.helper import fetch_api_data, loadCSV, extract_hashtags, fetch_instagram_api_data, loadAPI, \
    loadFilteredCSV, get_data_from_mongodb, loadFilteredAPI, convert_date
from utils.main_router import main_router
from utils.responses import getResponse, getPaginatedResponse, deleteResponse, createResponse

# Call the Main router
social_media_router = main_router
collection_social_media_api = database["collection_social_media_api"]
collection_social_media_csv = database["social_media_csv_data"]
collection_social_media_filtered_csv = database["social_media_filtered_csv_data"]

# Retrieve data from external source
@social_media_router.get('/get-api-data', tags=['Fetch-External-Data'])
async def getApiData():
    # response = await fetch_api_data(request)     # Call fetching data function
    response = fetch_instagram_api_data()
    # return getResponse(data=response)
    return response

# Save the external data into database
@social_media_router.post('/save-api-data', tags=['API-Data'])
async def saveApiData():
    # get_data = await fetch_api_data(request)     # Fetch data from external source
    get_data = fetch_instagram_api_data()
    response = await collection_social_media_api.insert_many(get_data)     # Merge and Insert the two data into database
    return {
        "message": "Data Inserted"      # Return response
    }

# Save the loaded csv data in background process
@social_media_router.post("/save-csv-data", tags=['CSV-Data'])
async def saveCSVData(background_tasks: BackgroundTasks):
   background_tasks.add_task(loadCSV)
   return {"message": "Data saved in the background"}

# Save the loaded csv data in background process
@social_media_router.post("/save-filtered-csv-data", tags=['CSV-Data'])
async def saveFilteredCSVData(background_tasks: BackgroundTasks):
   background_tasks.add_task(loadFilteredCSV)
   return {"message": "Data saved in the background"}

@social_media_router.post("/make-integration", tags=['Data-Integration'])
async def saveFilteredAPIData(background_tasks: BackgroundTasks, page: int = 0, per_page: int = 200):
    processed_data = []
    background_tasks.add_task(loadFilteredCSV)
    # for post in collection_social_media_api.find().skip(page).limit(per_page):
    async for post in collection_social_media_api.find().skip(page).limit(per_page):
        # post['_id'] = str(post['_id'])
        extracted_hashtags = []
        total_engagement = 0
        latest_date = None

        # Loop through the latestComments array
        for comment in post.get('latestComments', []):
            comment['id'] = str(comment['id'])
            comment['Date1'] = post.get('latestComments', [])[0]['timestamp']
            # Extract hashtags from the comment text
            hashtags = re.findall(r"#\w+", comment.get('text', ''))
            print("extracted_hashtags.extend(hashtags)", extracted_hashtags.extend(hashtags))
            extracted_hashtags.extend(hashtags)

            # Sum repliesCount and likesCount
            total_engagement += comment.get('repliesCount', 0) + comment.get('likesCount', 0)

            # Capture the latest timestamp
            timestamp = comment.get('timestamp')
            if timestamp:
                # comment_date = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ").date()
                latest_date = post.get('latestComments', [])[0]['timestamp']

        # Prepare the response data
        response = {
            "_id": post.get('_id', 'unknown_id'),
            "Date1": latest_date,
            "Extracted_Hashtags": list(set(extracted_hashtags)),  # Remove duplicate hashtags
            "Engagement_Score": total_engagement + len(extracted_hashtags)
        }

        processed_data.append(response)
        return response
        # Get existing data
    existing_data = await collection_social_media_filtered_csv.find({}, {"_id": 1}).to_list(None)
    existing_dates = set(item["_id"] for item in existing_data)

    # Filter out duplicates before inserting
    unique_data = [item for item in processed_data if item["_id"] not in existing_dates]

    if unique_data:

        result = await collection_social_media_filtered_csv.insert_many(unique_data)  # ✅ Added `await`
        return {"message": "Inserted data",
                # "inserted_count": len(result.inserted_ids)
                }

# Retrive saved api data from our db
@social_media_router.get('/get-saved-api-data', tags=['API-Data'])
async def getSavedApiData(page: int = 0, per_page: int = 10):
    data = []
    async for item in collection_social_media_api.find().skip(page).limit(per_page):
        item['_id'] = str(item['_id'])
        data.append(item)
    return getPaginatedResponse(data=data, page=page, per_page=per_page)

# Retrive saved csv data from our db
@social_media_router.get('/get-saved-csv-data', tags=['CSV-Data'])
async def getSavedCSVData(page: int = 0, per_page: int = 10):
    data = []
    async for item in collection_social_media_csv.find().skip(page).limit(per_page):
        item['_id'] = str(item['_id'])
        item["hashtags"] = extract_hashtags(item.get("Status text", ""))
        data.append(item)
    return getPaginatedResponse(data=data, page=page, per_page=per_page)

# Retrive saved csv data from our db
@social_media_router.get('/get-integrated-data', tags=['Data-Integration'])
async def getIntegratedData(page: int = 0, per_page: int = 10):
    data = []
    async for item in collection_social_media_filtered_csv.find().skip(page).limit(per_page):
        item['_id'] = str(item['_id'])
        data.append(item)
    return getPaginatedResponse(data=data, page=page, per_page=per_page)

# Delete all CSV data
@social_media_router.delete("/delete-all-api-data/", tags=['API-Data'])
async def deleteAllAPIData():
    result = await collection_social_media_api.delete_many({})
    return deleteResponse(deleted_length=result.deleted_count)

# Delete all CSV data
@social_media_router.delete("/delete-all-csv-data/", tags=['CSV-Data'])
async def deleteAllCSVData():
    result = await collection_social_media_csv.delete_many({})
    return deleteResponse(deleted_length=result.deleted_count)


# Get all extracted hashtags from api -> inside latestComments arrays
@social_media_router.get("/api-hashtags/", tags=['API-Hashtags'])
async def get_api_hashtags():
    posts = await collection_social_media_api.find({}, {"latestComments": 1}).to_list(None)  # Fetch all content fields

    hashtags = []
    for post in posts:
        for latestComment in post['latestComments']:
         hashtags.extend(extract_hashtags(latestComment.get("text", "")))  # Extract hashtags

    unique_hashtags = list(set(hashtags))  # Remove duplicates
    return getResponse(data=unique_hashtags)


# Get all extracted hashtags from csv
@social_media_router.get("/csv-hashtags/", tags=['CSV-Hashtags'])
async def get_hashtags():
    posts = await collection_social_media_csv.find({}, {"Status text": 1}).to_list(None)  # Fetch all content fields

    hashtags = []
    for post in posts:
        hashtags.extend(extract_hashtags(post.get("Status text", "")))  # Extract hashtags

    unique_hashtags = list(set(hashtags))  # Remove duplicates
    return getResponse(data=unique_hashtags)


# Count the hashtags from api
@social_media_router.get("/api-hashtags/count/", tags=['API-Hashtags'])
async def get_api_hashtag_counts():
    posts = await collection_social_media_api.find({}, {"latestComments": 1}).to_list(None)

    all_hashtags = []
    for post in posts:
        for latestComment in post['latestComments']:
         all_hashtags.extend(extract_hashtags(latestComment.get("text", "")))  # Extract hashtags
    hashtag_counts = dict(Counter(all_hashtags))  # Count occurrences
    return getResponse(data=hashtag_counts)

# Count the hashtags from csv
@social_media_router.get("/csv-hashtags/count/", tags=['CSV-Hashtags'])
async def get_hashtag_counts():
    posts = await collection_social_media_csv.find({}, {"Status text": 1}).to_list(None)

    all_hashtags = []
    for post in posts:
        all_hashtags.extend(extract_hashtags(post.get("Status text", "")))

    hashtag_counts = dict(Counter(all_hashtags))  # Count occurrences
    return getResponse(data=hashtag_counts)


# Sort the hashtags from csv
@social_media_router.get("/api-hashtags/sorted/", tags=['API-Hashtags'])
async def get_sorted_api_hashtags(order: str = Query("desc", enum=["asc", "desc"])):
    # Fetch all posts
    posts = await collection_social_media_api.find({}, {"latestComments": 1}).to_list(None)

    # Extract hashtags
    all_hashtags = []
    for post in posts:
        for latestComment in post['latestComments']:
         all_hashtags.extend(extract_hashtags(latestComment.get("text", "")))  # Extract hashtags

    # Count occurrences
    hashtag_counts = Counter(all_hashtags)

    # Sort hashtags based on order param
    sorted_hashtags = sorted(hashtag_counts.items(), key=lambda x: x[1], reverse=(order == "desc"))

    # ✅ Convert to list of dictionaries
    formatted_result = [{"hashtag": tag, "count": count} for tag, count in sorted_hashtags]
    return getResponse(data=formatted_result)

# Sort the hashtags from csv
@social_media_router.get("/csv-hashtags/sorted/", tags=['CSV-Hashtags'])
async def get_sorted_csv_hashtags(order: str = Query("desc", enum=["asc", "desc"])):
    # Fetch all posts
    posts = await collection_social_media_csv.find({}, {"Status text": 1}).to_list(None)
    # Extract hashtags
    all_hashtags = []
    for post in posts:
        all_hashtags.extend(extract_hashtags(post.get("Status text", "")))

    # Count occurrences
    hashtag_counts = Counter(all_hashtags)

    # Sort hashtags based on order param
    sorted_hashtags = sorted(hashtag_counts.items(), key=lambda x: x[1], reverse=(order == "desc"))

    # ✅ Convert to list of dictionaries
    formatted_result = [{"hashtag": tag, "count": count} for tag, count in sorted_hashtags]
    return getResponse(data=formatted_result)



# Sort hashtag based on likes
@social_media_router.get("/csv-hashtags-likes/sorted/", tags=['CSV-Hashtags'])
async def get_sorted_csv_hashtags_likes(
        sort_field: str = Query("like_count", description="Field to sort by like_count, retweet_count, reply_count"),
        sort_order: str = Query("desc", description="Sort order: 'asc' for ascending, 'desc' for descending"),
        page: int = 0, per_page: int = 100
):
    # Validate sort_order
    if sort_field not in ["like_count", "retweet_count", "reply_count", "quote_count"]:
        raise HTTPException(status_code=400, detail="Invalid sort order. Use 'like_count', 'retweet_count', 'reply_count', 'quote_count'.")

    # Determine the sort direction
    sort_direction = ASCENDING if sort_order == "asc" else DESCENDING

    # Retrieve and sort items from the collection
    cursor =  collection_social_media_csv.find().sort(sort_field, sort_direction)

    data = await cursor.to_list(length=per_page)  # Adjust the length as needed
    for item in data:
        item["_id"] = str(item['_id'])

    return getResponse(data=data)


# Industry Mapping (Manually Categorized)
industry_mapping = {
    "tourism": ["#MPTourism", "#Rajasthan", "#DekhoApnaDesh", "#IncredibleIndia",
                "#HeartOfIndia", "#GujaratTourism", "#UPNahiDekhaTohIndiaNahiDekha",
                "#RajasthanTourism", "#OdishaTourism", "#KeralaTourism"],
    "sports": ["#FIFAWorldCup", "#CricketWorldCup", "#Olympics", "#NBAFinals", "#SuperBowl"],
    "technology": ["#AI", "#MachineLearning", "#BigData", "#TechTrends", "#CloudComputing"],
    "fashion": ["#FashionWeek", "#OOTD", "#StyleInspo", "#DesignerWear", "#LuxuryFashion",],
    "entertainment": ["#Netflix", "#Bollywood", "#Hollywood", "#Marvel", "#GameOfThrones"]
}
# API Endpoint: Industry-wise Hashtag Engagement
@social_media_router.get("/industry-analysis", tags=["Industry Analysis"])
async def industry_analysis():
    industry_engagement = {key: 0 for key in industry_mapping.keys()}

    # Loop through stored hashtag data in MongoDB
    async for doc in collection_social_media_csv.find({}, {"Status text": 1, "like_count": 1, "retweet_count": 1,
        hashtags = extract_hashtags(doc.get("Status text", ""))
        engagement = doc.get("like_count", 0) + doc.get("retweet_count", 0) + doc.get("reply_count", 0)

        for industry, industry_hashtags in industry_mapping.items():
            if any(tag in hashtags for tag in industry_hashtags):
                industry_engagement[industry] += engagement

    return {"industry_engagement": industry_engagement}



# # API Endpoint: Hashtag Engagement Over Time
# @social_media_router.get("/engagement-over-time", tags=["Trend Analysis"])
# async def engagement_over_time():
#     pipeline = [
#         {"$group": {"_id": "$Date1",
#                     "total_engagement": {"$sum": {"$add": ["$like_count", "$retweet_count", "$reply_count"]}}}},
#         {"$sort": {"_id": 1}}
#     ]
#     engagement_trends = await collection_social_media_filtered_csv.aggregate(pipeline).to_list(None)
#
#     return {"engagement_trends": engagement_trends}

@social_media_router.get("/engagement-over-time/", tags=["Trend Analysis"])
async def engagement_over_time_updated(order: str = Query("desc", enum=["asc", "desc"]), per_page: int = 100):
    # Determine the sort order
    sort_order = ASCENDING if order == "asc" else DESCENDING
    cursor = collection_social_media_filtered_csv.find().sort("Date1", sort_order)
    data = await cursor.to_list(length=per_page)   # Adjust the length as needed
    for item in data:
        item["_id"] = str(item['_id'])
    filtered_data = [entry for entry in data if entry["Extracted_Hashtags"]]
    return {"engagement_trends": filtered_data}




@social_media_router.post("/report")
async def generate_profile(background_tasks: BackgroundTasks):
    # data = {'col1': [1, 2, 3], 'col2': ['a', 'b', 'c']}
    data = []
    async for item in collection_social_media_filtered_csv.find({}, {"Extracted_Hashtags": 0}).skip(0).limit(100):
        item['_id'] = str(item['_id'])
        data.append(item)
    # return data
    df = pd.DataFrame(data)

    profile = ProfileReport(df)
    profile.to_file("report.html")
    return {"message": "Report Generated"}


@social_media_router.post("/check_data_quality")
async def check_data_quality():
    try:
        fields_to_check = ["_id", "Extracted_Hashtags", "Engagement_Score", "Date1"]  # List of fields
        missing_fields = []

        for field in fields_to_check:
            missing_count = await collection_social_media_filtered_csv.count_documents({field: {"$exists": False}}) # await the async function
            if missing_count > 0:
                missing_fields.append(field)

        if missing_fields:
            return {"status": "failed", "message": f"Documents are missing the following fields: {', '.join(missing_fields)}"}
        else:
            return {"status": "passed", "message": "All documents have the required fields."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data quality check failed: {e}")



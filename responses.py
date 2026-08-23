# Api Response Messages
getResponseMessage = "Data get successfully"
createResponseMessage = "Data created successfully"
deleteAllResponseMessage = "Data deleted successfully"


# A GET request message
def getResponse(data):
    return {
        "message": getResponseMessage,
        "data": data
    }

# A POST request message
def createResponse(data, id):
    data["_id"] = id
    return {
        "message": createResponseMessage,
        "data": data,
    }

# A DELETE request message
def deleteResponse(deleted_length):
    return {
        "message":  f"{deleted_length} {deleteAllResponseMessage}"
    }


# A GET paginated request message
def getPaginatedResponse(data, page, per_page):
    return {
        "message": getResponseMessage,
        "data": data,
        "paginate": {
            "page": page,
            "per_page": per_page,
            # "next_page": f"http://localhost:8000/get-saved-api-data?page={page+1}&per_page=10",
            # "perv_page": f"http://localhost:8000/get-saved-api-data?page={ page - 1 if page > 0 else 0}&per_page=10"
        }
    }

def helper(data) -> str:
    print("helper_data", data)
    return str(data["_id"])


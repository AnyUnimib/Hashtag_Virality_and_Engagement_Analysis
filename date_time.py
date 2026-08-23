from datetime import datetime

# Current DateTime
now = datetime.utcnow()


currentDateCreate = {
    "created_at": now,
    "updated_at": now
}

currentDateUpdate = {
    "updated_at": now
}
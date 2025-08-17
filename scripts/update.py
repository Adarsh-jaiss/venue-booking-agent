import json
from pymongo import MongoClient

# Mongo connection
client = MongoClient("mongodb+srv://telo:WijJYNtGInFpICSY@telo.fl0eew2.mongodb.net/")  # change if needed
db = client["telo"]
collection = db["venues"]

# Load input.json
with open("mongo_venues.json", "r") as f:
    venues = json.load(f)

# Iterate and update
for venue in venues:
    business_name = venue.get("businessName")
    profile_image = venue.get("profileImage")
    cover_images = venue.get("coverImages")

    if not business_name:
        print("Skipping entry without businessName:", venue)
        continue

    update_fields = {}
    if profile_image:
        update_fields["profileImage"] = profile_image
    if cover_images:
        update_fields["coverImages"] = cover_images

    if update_fields:
        result = collection.update_one(
            {"businessName": business_name},
            {"$set": update_fields}
        )
        if result.matched_count > 0:
            print(f"✅ Updated: {business_name}")
        else:
            print(f"⚠️ No match found for: {business_name}")

from flask import Flask, jsonify, request, abort
from flask_cors import CORS
import os
import cloudinary
import cloudinary.uploader
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # enable CORS for all domains

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key=os.environ.get('CLOUDINARY_API_KEY'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET')
)

# Connect to MongoDB Atlas
client = MongoClient(os.environ.get('MONGO_URI'))
db = client['videosDB']
videos_collection = db['videos']

# Sample in-memory fallback videos (for dev only)
videos_db = {
    "default": {
        "id": "default",
        "title": "Sample Video Title",
        "description": "This is a sample description for the video. Enjoy watching!",
        "src": "https://web-frontend-one-omega.vercel.app/videos/sample-video.mp4",
        "isEmbed": False,
        "thumbnail": "https://web-frontend-one-omega.vercel.app/images/sample-thumb.jpg",
        "likes": 1234,
        "dislikes": 56,
        "views": 1234567,
    }
}

@app.route('/api/videos/<video_id>', methods=['GET'])
def get_video(video_id):
    try:
        video = videos_collection.find_one({"_id": ObjectId(video_id)})
        if not video:
            return abort(404, description="Video not found")
        video['id'] = str(video['_id'])
        del video['_id']
        return jsonify(video)
    except:
        # fallback to in-memory for demo
        video = videos_db.get(video_id)
        if not video:
            return abort(404, description="Video not found")
        return jsonify(video)


@app.route('/api/videos/suggested', methods=['GET'])
def suggested_videos():
    suggested = []
    for vid in videos_collection.find():
        suggested.append({
            "id": str(vid["_id"]),
            "title": vid["title"],
            "thumbnail": vid.get("thumbnail", ""),
            "views": vid.get("views", 0),
        })
    return jsonify(suggested)


@app.route('/api/videos/<video_id>/reaction', methods=['POST'])
def update_reaction(video_id):
    data = request.get_json()
    if not data or 'type' not in data or 'remove' not in data:
        return abort(400, description="Invalid request")

    reaction_type = data['type']  # 'like' or 'dislike'
    remove = data['remove']  # boolean

    if reaction_type not in ('like', 'dislike'):
        return abort(400, description="Invalid reaction type")

    field = 'likes' if reaction_type == 'like' else 'dislikes'
    change = -1 if remove else 1

    result = videos_collection.update_one(
        {"_id": ObjectId(video_id)},
        {"$inc": {field: change}}
    )

    if result.matched_count == 0:
        return abort(404, description="Video not found")

    updated = videos_collection.find_one({"_id": ObjectId(video_id)})
    return jsonify({
        "likes": updated.get("likes", 0),
        "dislikes": updated.get("dislikes", 0)
    })


@app.route('/api/upload', methods=['POST'])
def upload_video():
    title = request.form.get('title')
    description = request.form.get('description')
    video_file = request.files.get('video')

    if not all([title, description, video_file]):
        return abort(400, description='Missing fields')

    upload_result = cloudinary.uploader.upload_large(
        video_file,
        resource_type='video'
    )

    video_data = {
        "title": title,
        "description": description,
        "src": upload_result['secure_url'],
        "isEmbed": False,
        "thumbnail": "",
        "likes": 0,
        "dislikes": 0,
        "views": 0
    }

    result = videos_collection.insert_one(video_data)
    video_data['id'] = str(result.inserted_id)

    return jsonify(video_data)


@app.route('/api/videos', methods=['GET'])
def get_all_videos():
    videos = []
    for vid in videos_collection.find():
        videos.append({
            "id": str(vid["_id"]),
            "title": vid["title"],
            "description": vid["description"],
            "src": vid["src"],
            "thumbnail": vid.get("thumbnail", ""),
            "likes": vid.get("likes", 0),
            "dislikes": vid.get("dislikes", 0),
            "views": vid.get("views", 0)
        })
    return jsonify(videos)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
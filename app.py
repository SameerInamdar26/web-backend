from flask import Flask, jsonify, request, abort
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)  # enable CORS for all domains

# In-memory "database" for demo purposes
videos_db = {
    "default": {
        "id": "default",
        "title": "Sample Video Title",
        "description": "This is a sample description for the video. Enjoy watching!",
        "src": "/videos/sample-video.mp4",
        "isEmbed": False,
        "thumbnail": "/images/sample-thumb.jpg",
        "likes": 1234,
        "dislikes": 56,
        "views": 1234567,
    },
    "embedded": {
        "id": "embedded",
        "title": "Embedded Video Example",
        "description": "Example of a YouTube embedded video.",
        "src": "https://www.youtube.com/embed/dQw4w9WgXcQ",
        "isEmbed": True,
        "thumbnail": "/images/sample-thumb2.jpg",
        "likes": 2345,
        "dislikes": 34,
        "views": 987654,
    },
    "default2": {
        "id": "default2",
        "title": "Another Cool Video",
        "description": "Check out this cool video!",
        "src": "/videos/another-video.mp4",
        "isEmbed": False,
        "thumbnail": "/images/sample-thumb3.jpg",
        "likes": 3456,
        "dislikes": 78,
        "views": 2345678,
    },
}

# Helper to get suggested videos with limited fields
def get_suggested_videos():
    suggested = []
    for vid in videos_db.values():
        suggested.append({
            "id": vid["id"],
            "title": vid["title"],
            "thumbnail": vid["thumbnail"],
            "views": vid["views"],
        })
    return suggested


@app.route('/api/videos/<video_id>', methods=['GET'])
def get_video(video_id):
    video = videos_db.get(video_id)
    if not video:
        return abort(404, description="Video not found")
    return jsonify(video)


@app.route('/api/videos/suggested', methods=['GET'])
def suggested_videos():
    return jsonify(get_suggested_videos())


@app.route('/api/videos/<video_id>/reaction', methods=['POST'])
def update_reaction(video_id):
    video = videos_db.get(video_id)
    if not video:
        return abort(404, description="Video not found")

    data = request.get_json()
    if not data or 'type' not in data or 'remove' not in data:
        return abort(400, description="Invalid request")

    reaction_type = data['type']  # 'like' or 'dislike'
    remove = data['remove']  # boolean

    if reaction_type not in ('like', 'dislike'):
        return abort(400, description="Invalid reaction type")

    # Update counts based on reaction
    if reaction_type == 'like':
        if remove and video['likes'] > 0:
            video['likes'] -= 1
        elif not remove:
            video['likes'] += 1
            # If previously disliked, decrease dislikes by 1 (handled client side)
    else:  # dislike
        if remove and video['dislikes'] > 0:
            video['dislikes'] -= 1
        elif not remove:
            video['dislikes'] += 1
            # If previously liked, decrease likes by 1 (handled client side)

    return jsonify({
        "likes": video['likes'],
        "dislikes": video['dislikes']
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

 

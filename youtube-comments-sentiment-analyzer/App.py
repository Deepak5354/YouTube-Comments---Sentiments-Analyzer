from flask import Flask, request, jsonify
from googleapiclient.discovery import build
from flask_cors import CORS
from textblob import TextBlob
from googletrans import Translator
import re

app = Flask(__name__)
CORS(app)  # Enable CORS

YOUTUBE_API_KEY = 'AIzaSyBz-Gd9zmDoe_sgsFlSEBlaGOl1EscaEwk'  # Replace with your YouTube API key

def fetch_comments_page(youtube, video_id, page_token=None):
    request = youtube.commentThreads().list(
        part='snippet',
        videoId=video_id,
        textFormat='plainText',
        maxResults=100,
        pageToken=page_token
    )
    response = request.execute()
    return response

def get_all_comments(youtube, video_id):
    comments = []
    page_token = None
    while True:
        response = fetch_comments_page(youtube, video_id, page_token)
        for item in response['items']:
            comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
            author = item['snippet']['topLevelComment']['snippet']['authorDisplayName']
            comments.append({'comment': comment, 'author': author})
        page_token = response.get('nextPageToken')
        if not page_token:
            break
    return comments

def get_comments(video_id):
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    comments = get_all_comments(youtube, video_id)
    return comments

def extract_video_id(url):
    # Regular expression to extract video ID from URL
    video_id_match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', url)
    if video_id_match:
        return video_id_match.group(1)
    return None

def analyze_sentiment(comment):
    translator = Translator()
    translated_comment = translator.translate(comment, dest='en')
    analysis = TextBlob(translated_comment.text)
    if analysis.sentiment.polarity > 0:
        return 'Positive'
    elif analysis.sentiment.polarity == 0:
        return 'Neutral'
    else:
        return 'Negative'

def analyze_comments(comments):
    for comment in comments:
        sentiment = analyze_sentiment(comment['comment'])
        comment['sentiment'] = sentiment
    return comments

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.json
        url = data.get('url')
        video_id = extract_video_id(url)
        if not video_id:
            return jsonify({'error': 'Invalid YouTube URL'}), 400

        comments = get_comments(video_id)
        analyzed_comments = analyze_comments(comments)

        return jsonify({'comments': analyzed_comments})
    except Exception as e:
        print(f"Error: {e}")  # Log the error
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Run the Flask app directly when the Python file is executed
    app.run(host='0.0.0.0', port=5000, debug=True)
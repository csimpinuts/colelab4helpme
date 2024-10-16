from flask import Flask, request, redirect, url_for
import os
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')

def get_current_playback(access_token):
    playback_url = 'https://api.spotify.com/v1/me/player/currently-playing'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    playback_response = requests.get(playback_url, headers=headers)

    if playback_response.status_code == 200:
        current_playback = playback_response.json()
        if current_playback and 'item' in current_playback:
            song_name = current_playback['item']['name']
            artist_name = current_playback['item']['artists'][0]['name']
            album_name = current_playback['item']['album']['name']
            album_cover = current_playback['item']['album']['images'][0]['url']
            return {
                "song_name": song_name,
                "artist_name": artist_name,
                "album_name": album_name,
                "album_cover": album_cover
            }
    return None

@app.route('/')
def index():
    # Spotify login
    auth_url = (
        f"https://accounts.spotify.com/authorize?client_id={CLIENT_ID}"
        f"&response_type=code&redirect_uri={REDIRECT_URI}"
        f"&scope=user-read-playback-state,user-modify-playback-state,user-top-read"
    )
    return redirect(auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    token_url = 'https://accounts.spotify.com/api/token'
    token_data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    
    response = requests.post(token_url, data=token_data)
    if response.status_code != 200:
        return f"""<a href="/top?access_token={access_token}&time_range=1mo">View Top Songs and Artists (Last Month)</a>
            <br>
            <a href="/top?access_token={access_token}&time_range=6mo">View Top Songs and Artists (Last 6 Months)</a>
            <br>
            <a href="/top?access_token={access_token}&time_range=12mo">View Top Songs and Artists (All Time)</a>"""
    
    access_token = response.json().get('access_token')

    # Use the access token to get the user's playback state
    playback_url = 'https://api.spotify.com/v1/me/player/currently-playing'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    playback_response = requests.get(playback_url, headers=headers)

    # Print the raw response for debugging
    print("Playback response status code:", playback_response.status_code)
    print("Playback response content:", playback_response.text)

    if playback_response.status_code == 200:
        current_playback = playback_response.json()

        # Check if there's currently playing content
        if 'item' in current_playback:
            song_name = current_playback['item']['name']
            artist_name = current_playback['item']['artists'][0]['name']
            album_name = current_playback['item']['album']['name']
            album_cover = current_playback['item']['album']['images'][0]['url']

            return f"""
            <h1>Now Playing</h1>
            <p>Song: {song_name}</p>
            <p>Artist: {artist_name}</p>
            <p>Album: {album_name}</p>
            <img src="{album_cover}" alt="Album Cover" style="width:200px;height:auto;">
            <br>
            <a href="/play/{current_playback['item']['id']}?access_token={access_token}">Play this track again</a>
            <br>
            <a href="/top?access_token={access_token}&time_range=1mo">View Top Songs and Artists (Last Month)</a>
            <br>
            <a href="/top?access_token={access_token}&time_range=6mo">View Top Songs and Artists (Last 6 Months)</a>
            <br>
            <a href="/top?access_token={access_token}&time_range=12mo">View Top Songs and Artists (All Time)</a>
            """
        else:
            return "<h1>No song is currently playing.</h1>"
    else:
        return f"""<a href="/top?access_token={access_token}&time_range=1mo">View Top Songs and Artists (Last Month)</a>
            <br>
            <a href="/top?access_token={access_token}&time_range=6mo">View Top Songs and Artists (Last 6 Months)</a>
            <br>
            <a href="/top?access_token={access_token}&time_range=12mo">View Top Songs and Artists (All Time)</a>"""

@app.route('/top')
def top_tracks_artists():
    access_token = request.args.get('access_token')
    time_range = request.args.get('time_range', 'short_term')  # Default to 'short_term'

    # Set the appropriate time range based on user selection
    time_ranges = {
        '1mo': 'short_term',  # Last 4 weeks
        '6mo': 'medium_term',  # Last 6 months
        '12mo': 'long_term'  # All time
    }

    selected_time_range = time_ranges.get(time_range, 'short_term')

    # Fetch top tracks
    top_tracks_url = f'https://api.spotify.com/v1/me/top/tracks?time_range={selected_time_range}&limit=10'
    top_tracks_headers = {
        'Authorization': f'Bearer {access_token}'
    }
    top_tracks_response = requests.get(top_tracks_url, headers=top_tracks_headers)

    # Fetch top artists
    top_artists_url = f'https://api.spotify.com/v1/me/top/artists?time_range={selected_time_range}&limit=10'
    top_artists_response = requests.get(top_artists_url, headers=top_tracks_headers)

    if top_tracks_response.status_code == 200 and top_artists_response.status_code == 200:
        top_tracks = top_tracks_response.json()['items']
        top_artists = top_artists_response.json()['items']

        # Generate HTML for displaying top tracks and artists
        track_html = '''
        <h2>Top Tracks</h2>
        <ol id="track-list">
        '''
        for track in top_tracks:
            track_html += (
                f"<li>{track['name']} by {', '.join([artist['name'] for artist in track['artists']])} "
                f"<button class='play-button' data-track-id='{track['id']}' data-access-token='{access_token}'>Play</button></li>"
            )
        track_html += '</ol>'

        artist_html = '<h2>Top Artists</h2><ol>'
        for artist in top_artists:
            artist_html += f"<li>{artist['name']}</li>"
        artist_html += '</ol>'

        # Include JavaScript for playback
        track_html += '''
        <script>
        document.querySelectorAll('.play-button').forEach(button => {
            button.addEventListener('click', function() {
                const trackId = this.getAttribute('data-track-id');
                const accessToken = this.getAttribute('data-access-token');

                fetch(`/play/${trackId}?access_token=${accessToken}`, {
                    method: 'GET'
                })
                .then(response => response.text())
                .then(data => {
                    console.log(data);  // You can log or handle the response as needed
                })
                .catch(error => console.error('Error:', error));
            });
        });
        </script>
        '''

        return track_html + artist_html
    else:
        return f"Error retrieving top tracks or artists: {top_tracks_response.json().get('error_description')}"


@app.route('/play/<track_id>')
def play_track(track_id):
    access_token = request.args.get('access_token')  # Retrieve the access token properly

    play_url = 'https://api.spotify.com/v1/me/player/play'
    headers = {
        'Authorization': f'Bearer {access_token}',  # Use the stored access token
        'Content-Type': 'application/json'
    }
    data = {
        'uris': [f'spotify:track:{track_id}']  # Track ID to play
    }
    play_response = requests.put(play_url, headers=headers, json=data)

    if play_response.status_code == 204:
        return 'Playback started!'
    else:
        return f"Error: {play_response.json().get('error_description')}"

if __name__ == '__main__':
    app.run(port=8888)

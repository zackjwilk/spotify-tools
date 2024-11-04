# EDIT THESE
factors = {
    "energy": 3,
    "danceability": None,
    "valence": None,
    "loudness": None,
    "acousticness": None,
    "instrumentalness": None,
    "speechiness": None,
    "liveness": None,
    "mode": None,
    "time_signature": None, # PROBABLY DOESN'T WORK, SPOTIFY'S API IS BEING WEIRD
    "key": None,
    }
# ^ Spotify audio features
# None = ignore
# 1 = low
# 2 = neutral
# 3 = high
# time signature -> 3-7; 3 = 3/4, 4 = 4/4, etc.
# key -> Pitch Class notation: 0 = C, 1 = C#, 2 = D, etc.
# mode -> 0 = minor, 1 = major

ranges = {
    "energy": [[0, 0.4], [0.4, 0.7], [0.7, 1.1]],
    "danceability": [[0, 0.4], [0.4, 0.7], [0.7, 1.1]],
    "valence": [[0, 0.4], [0.4, 0.6], [0.6, 1.1]],
    "loudness": [[-60, -30], [-30, -16], [-16, 1]],
    "acousticness": [[0, 0.4], [0.4, 0.7], [0.7, 1.1]],
    "instrumentalness": [[0, 0.3], [0.3, 0.7], [0.7, 1.1]],
    "speechiness": [[0, 0.3], [0.3, 0.7], [0.7, 1.1]],
    "liveness": [[0, 0.4], [0.4, 0.8], [0.8, 1.1]]
    }

adjectives = {
    "energy": ["lazy", "medium energy", "energetic"],
    "danceability": ["undanceable", "potentially danceable", "danceable"],
    "valence": ["sad", "neutral", "jubilant"],
    "loudness": ["quiet", "moderate volume", "loud"],
    "acousticness": ["probably not acoustic", "potentially acoustic", "acoustic"],
    "instrumentalness": ["vocal", "kinda instrumental", "instrumental"],
    "speechiness": ["no talking", "speechy", "spoken word"],
    "liveness": ["studio", "potentially live", "live"],
    "mode": ["major", "minor"], # order reversed cause adjective is retrieved using index factors[key]-1
    #"time_signature": ["3/4", "4/4", "5/4", "6/4", "7/4"],
    "key": ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    }

import json
import math
import requests
import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

print("Welcome to Spotify Subplaylist Maker!\n")

# Load environment variables from .env
load_dotenv()

# CONSTANTS
CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
REDIRECT_URI = "https://myshetland.co.uk/shetland-ponies-in-sweaters/"
SCOPE = "playlist-read-private user-library-read playlist-modify-private playlist-modify-public"

# Get authorization
auth_url = f"https://accounts.spotify.com/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}&scope={SCOPE}"
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    page.goto(auth_url)
    page.wait_for_url(f"{REDIRECT_URI}*")
    auth_code = page.url.split("code=")[-1]
    
    browser.close()

token_url = "https://accounts.spotify.com/api/token"

body = {
    "grant_type": "authorization_code",
    "code": auth_code,
    "redirect_uri": REDIRECT_URI,
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET
}

# Get access token
response = requests.post(token_url, data=body)
token_info = response.json()
access_token = token_info["access_token"]
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

# Get User ID and name of playlist from user
user_id = input("Spotify User ID: ")
P_or_L = input("(P)laylist or (L)iked Songs? ").upper()
while not P_or_L in "PL":
    P_or_L = input("Enter either \"P\" or \"L\": ").upper()

playlist_link = ""
if P_or_L == "P":
    playlist_link = input("Playlist link: ")

def get_playlist():
    """
    Returns playlist given by playlist_link
    """
    playlist_id = playlist_link.split("/")[-1].split("?")[0]
    playlist_url = f"https://api.spotify.com/v1/playlists/{playlist_id}"
    
    response = requests.get(playlist_url, headers=headers)

    if response.status_code == 200:
        playlist = response.json()
        return playlist
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return None

def get_playlist_tracks(playlist_id):
    """
    playlist_id is a base-62 Spotify playlist ID

    Returns each track on playlist with ID playlist_id
    """
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"

    tracks = []
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        tracks.extend(data["items"])

        while data["next"]:
            response = requests.get(data["next"], headers=headers)
            if response.status_code == 200:       
                data = response.json()
                tracks.extend(data["items"])
            else:
                print(f"Error fetching next page: {response.status_code}, {response.json()}")
                break

        return tracks
    else:
        print(f"Error: {response.status_code}, {response.json()}")
        return None

def get_liked_songs():
    """
    Returns each track in user's Liked Songs
    """
    url = "https://api.spotify.com/v1/me/tracks"

    liked_songs = []
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        liked_songs.extend(data["items"])

        while data["next"]:
            response = requests.get(data["next"], headers=headers)
            if response.status_code == 200:
                data = response.json()
                liked_songs.extend(data["items"])
            else:
                print(f"Error fetching next page: {response.status_code}, {response.json()}")
                break

        return liked_songs
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return None

def create_playlist(name):
    """
    name is a string
    
    Creates a playlist on Spotify account of ID user_id with name name
    """
    url = f"https://api.spotify.com/v1/users/{user_id}/playlists"
    desc_format = "Liked Songs"
    if P_or_L == "P":
        desc_format = get_playlist()["name"]
    body = {
        "name": name,
        "description": f"Subplaylist of {desc_format} created with subplaylist_maker.py!",
        "public": False
    }

    response = requests.post(url, headers=headers, json=body)

    if response.status_code == 201:
        playlist_info = response.json()
        print(f"New playlist created successfully; Playlist ID: {playlist_info['id']}")
        return playlist_info["id"]
    else:
        print(f"Error creating playlist: {response.json()}")
        return None

def add_tracks(playlist_id, track_uris):
    """
    playlist_id is a base-62 Spotify playlist ID
    track_uris is a list of Spotify track URIs

    Adds track of URI of each item in track_uris to playlist of ID playlist_id
    """
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    
    response = requests.post(url, headers=headers, json={"uris": track_uris})
    
    if response.status_code == 201:
        print("Tracks added successfully")
    else:
        print(f"Error adding tracks: {response.json()}")

def get_audio_features(track_ids):
    """
    track_ids is a list of Spotify track IDs

    Returns list of Spotify audio features of each track in track_ids
    """
    url = f"https://api.spotify.com/v1/audio-features"

    params = {
        "ids": ','.join(track_ids)  # Join track IDs into a comma-separated string
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()["audio_features"]
    else:
        print(f"Error: {response.status_code}, {response.json()}")
        return None

playlist = get_playlist()

if ((P_or_L == "P" and playlist) or P_or_L == "L"):
    tracks_info = None
    if P_or_L == "P":
        print("Playlist located successfully")
        tracks_info = get_playlist_tracks(playlist["id"])
    else:
        print("Local Files located successfully")
        tracks_info = get_liked_songs()
    
    track_ids = []
    track_uris = []
    
    # Create lists of IDs and URIs of each track in playlist
    for item in tracks_info:
        track = item["track"]                 
        track_ids.append(track["id"])
        track_uris.append(track["uri"])
    
    audio_features = get_audio_features(track_ids)
    new_track_uris = []
    
    # Generate playlist name
    new_playlist_name = ""
    for key in factors.keys():
        if factors[key] is not None and not key in ["time_signature", "key"]:
            new_playlist_name += adjectives[key][factors[key]-1] + " "
         
    new_playlist_name += "tunes"
    
    if factors["time_signature"]:
        new_playlist_name += " in " + str(factors["time_signature"]) + "/4"
        if factors["key"] is not None:
            new_playlist_name += ", " + adjectives["key"][factors["key"]]
    elif factors["key"] is not None:
        new_playlist_name += " in " + adjectives["key"][factors["key"]]
    
    # Add track uris to list based on chosen factors
    if audio_features:
        i = 0
        good = True # made false if doesn't meet requirements
        for feature in audio_features:
            if feature:
                for key in factors.keys():
                    if factors[key] is not None:
                        if key in ["mode", "time_signature", "key"]:
                            if feature[key] != factors[key]:
                                good = False
                        else:
                            val = feature[key]
                            good2 = False
                            for j in range(3):
                                Range = ranges[key][j]
                                if ((val >= Range[0] and val < Range[1]) and (factors[key] == j+1)):
                                    good2 = True
                                    break
                            if not good2:
                                good = False
                
                if good:
                    new_track_uris.append(track_uris[i])
                good = True
                i += 1
    
    # Create new playlist and add appropriate tracks
    if new_track_uris: 
        new_playlist_id = create_playlist(new_playlist_name)
        add_tracks(new_playlist_id, new_track_uris)
        print("Done")
    else:
        print("No tracks found based on chosen factors; could not create playlist.")
else:
    print("Playlist not found")

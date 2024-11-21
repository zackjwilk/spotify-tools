# EDIT THESE
sequence_basis = "energy"
# ^ Spotify audio feature (energy, danceability, valence, tempo, loudness,
# key, acousticness, instrumentalness, speechiness, liveness, time_signature,
# duration_ms, mode)
# TIME_SIGNATURE PROBABLY DOESN'T WORK, SPOTIFY'S API IS BEING WEIRD
sequence_mode = "symmetrical"
# ^ symmetrical, increasing, or decreasing

import json
import math
import requests
import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

print("Welcome to Spotify Playlist Sequencer!\n")

# Load environment variables from .env
load_dotenv()

# CONSTANTS
CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
REDIRECT_URI = "https://zackjwilk.github.io/"
SCOPE = "playlist-read-private playlist-modify-private playlist-modify-public"

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
playlist_name = input("Playlist name: ")

def get_user_playlists():
    """
    Returns all playlists of user with ID user_id
    """
    url = f"https://api.spotify.com/v1/users/{user_id}/playlists"

    playlists = []
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        playlists.extend(data["items"])

        while data["next"]:
            response = requests.get(data["next"], headers=headers)
            if response.status_code == 200:
                data = response.json()
                playlists.extend(data["items"])
            else:
                print(f"Error fetching next page: {response.status_code}, {response.json()}")
        
        return playlists
    else:
        print(f"Error: {response.status_code}, {response.json()}")
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

def create_playlist(playlist_name):
    """
    playlist_name is a string
    
    Creates a playlist on Spotify account of ID user_id with name playlist_name
    """
    url = f"https://api.spotify.com/v1/users/{user_id}/playlists"
    body = {
        "name": "[SORTED] " + playlist_name,
        "description": f"Sorted version of \"{playlist_name}\" created with spotify-playlist-sequencer! Sorted {sequence_mode}ly by {sequence_basis}.",
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

def symmetric_sort(lst, ids, uris):
    """
    lst is a list of values from 0-1 (Spotify track sequence basis values)
    ids is a list of Spotify track IDs
    uris is a list of Spotify track URIs

    Reorders lst so the values start from the minimum value, increase up to the
    maximum value, and decrease back down to the smallest value still available,
    creating the most symmetrical possible list. Each change in order is then also
    made to ids and uris.
    """
    sorted_lst = [0]*len(lst)
    sorted_ids = [0]*len(lst)
    sorted_uris = [0]*len(lst)
    
    middle = math.floor(len(lst)/2)
    
    sorted_lst[middle] = max(lst)
    sorted_ids[middle] = ids[lst.index(max(lst))]
    sorted_uris[middle] = uris[lst.index(max(lst))]

    ind = lst.index(max(lst))
    del lst[ind]
    del ids[ind]
    del uris[ind]

    for i in range(middle):
        sorted_lst[i] = min(lst)
        sorted_ids[i] = ids[lst.index(min(lst))]
        sorted_uris[i] = uris[lst.index(min(lst))]

        ind = lst.index(min(lst))
        del lst[ind]
        del ids[ind]
        del uris[ind]
        
        if sorted_lst[-i-1] == 0:
            sorted_lst[-i-1] = min(lst)
            sorted_ids[-i-1] = ids[lst.index(min(lst))]
            sorted_uris[-i-1] = uris[lst.index(min(lst))]

            ind = lst.index(min(lst))
            del lst[ind]
            del ids[ind]
            del uris[ind]
    
    return [sorted_ids, sorted_uris]

def increasing_sort(lst, ids, uris):
    """
    lst is a list of values from 0-1 (Spotify track sequence basis values)
    ids is a list of Spotify track IDs
    uris is a list of Spotify track URIs

    Reorders lst so the values are in ascending order. Each change in order
    is then also made to ids and uris.
    """
    for i in range(len(lst)):
        for j in range(i + 1, len(lst)):
            if lst[i] > lst[j]:
                lst[i], lst[j] = lst[j], lst[i]
                ids[i], ids[j] = ids[j], ids[i]
                uris[i], uris[j] = uris[j], uris[i]
    
    return [ids, uris]

def get_values(playlist_id):
    string = ""
    tracks_info = get_playlist_tracks(playlist_id)
    for item in tracks_info:
        track = item["track"]
        value = get_audio_features([track["id"]])[0][sequence_basis]
        string += track["name"] + " - " + str(value) + "\n"
    return string

playlists_info = get_user_playlists()

playlist = None
if playlists_info:
    # Get playlist
    for pl in playlists_info:
        if pl["name"] == playlist_name:
            playlist = pl
            break

if playlist:
    print("Playlist located successfully")
    playlist_id = playlist["id"]
    tracks_info = get_playlist_tracks(playlist_id)
    track_ids = []
    track_uris = []

    before_and_after = [get_values(playlist_id)]

    # Create lists of IDs and URIs of each track in playlist
    for item in tracks_info:
        track = item["track"]
        track_ids.append(track["id"])
        track_uris.append(track["uri"])
    
    audio_features = get_audio_features(track_ids)
    values = []

    # Add sequence basis of each track to list
    if audio_features:
        for feature in audio_features:
            if feature:
                if feature[sequence_basis]:
                    values.append(feature[sequence_basis])
                else:
                    print("Invalid sequence basis")

    # Apply selected sort method to IDs and URIs of tracks
    if sequence_mode == "symmetrical":
        sorted_stuff = symmetric_sort(values, track_ids, track_uris)
        print(f"Track IDs and URIs sequenced symetrically by {sequence_basis} successfully")
    elif sequence_mode == "increasing":
        sorted_stuff = increasing_sort(values, track_ids, track_uris)
        print(f"Track IDs and URIs sequenced in ascending order by {sequence_basis} successfully")
    elif sequence_mode == "decreasing":
        sorted_stuff = increasing_sort(values, track_ids, track_uris)
        sorted_stuff[0].reverse()
        sorted_stuff[1].reverse()
        print(f"Track IDs and URIs sequenced in descending order by {sequence_basis} successfully")
    else:
        print("Invalid sequence mode")
        
    sorted_ids = sorted_stuff[0]
    sorted_uris = sorted_stuff[1]

    # Create new playlist and add tracks in new sorted sequence
    new_playlist_id = create_playlist(playlist_name)
    add_tracks(new_playlist_id, sorted_uris)
    before_and_after.append(get_values(new_playlist_id))
    print("Done")
    print(f"\nBefore:\n{before_and_after[0]}\nAfter:\n{before_and_after[1]}")
else:
    print("Playlist not found")

# spotify-helper
---
## Installation
Clone the repository:

`git clone https://github.com/zackjwilk/spotify-helper.git`

Install dependencies with pip:

`pip install -r spotify-helper/requirements.txt`

## Features
---
### Local Files Automator
---
Spotify Local Files Automator is a Python script that takes user input of a song title and artist name and/or link to song on SoundCloud and rips the song from SoundCloud, downloads it, adds metadata (title, artist, cover image), and places it in the user's specified Spotify local files folder so they can listen to it on Spotify (useful for unreleased songs or songs that are otherwise not typicaly available on Spotify).

SoundCloud got rid of its API allowing downloads of songs, so the program listens for responses containing "mp3", downloads these splices of a song, and pieces them together to combat this.

NOTE: When downloading these mp3 snippets, some of them lead and end with short bits of silence. To combat this and make the final export more smooth, the program tries to detect these bits of silence on each splice and get rid of it, but this could result in sonic artifacts if there is intended silence in the song. To turn this feature off, there is a toggleable boolean variable at the top of the script called trim. 

#### Usage
Set `songs` folder as your local files folder on Spotify and run `local_files_automator.py`!

---
### Playlist Sequencer
---
Spotify Playlist Sequencer is a Python script that takes user input of their Spotify User ID and name of one of their playlists and creates a clone of said playlist in a more comprehensible sequence. The tracks in the new playlist can be sequenced in symmetrical (increasing until a maximum and then decreasing back down until the end of the playlist), ascending, or descending order based on a selected audio feature (energy, danceability, tempo, etc.).

#### Usage
Edit the `.env` file and replace your_client_id and your_client_secret with your own Spotify application Client ID and Client Secret. Then, edit the sequence_basis and sequence_mode variables in `playlist_sequencer.py` to your liking.

Run `playlist_sequencer.py`, provide authorization with your Spotify credentials, and enter your Spotify username and the name of your desired playlist!

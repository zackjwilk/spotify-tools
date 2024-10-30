# EDIT THESE
trim = True
# ^ Trim silence from beginning and ends of snippets in an attempt to make final export
# smoother (may result in sonic artifacts if a portion of the song is meant to be silent)

from playwright.sync_api import sync_playwright
from pydub import AudioSegment
import eyed3
import requests
import shutil
import os

path = os.path.abspath(os.getcwd())

# Prompt user to input song title and artist name and generate SoundCloud query
title = input("Title: ")
artist = input("Artist: ")
link = input("Link (enter nothing if no link): ").lower()
query = artist + " " + title
query.replace(" ", "%20")
url = "https://soundcloud.com/search?q=" + query
should_log = False
if link:
    url = link
    should_log = True # mp3 responses are collected instantly with direct link
    # rather than after play button is pressed

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()

    mp3_urls = []
    song_splices = []

    def capture(response):
        """
        response is a webpage response

        Adds response url to mp3_urls if it contains an mp3 file and play button has been pressed
        """
        global mp3_urls
        if should_log and response.status == 200:
            if ".mp3" in response.url:
                mp3_urls += [response.url]
                print("Captured MP3 URL")

    # Go to SoundCloud search results page for query
    page.on("response", capture)
    page.goto(url)

    # Press play button and start listening to responses
    page.click("//a[@title='Play']")
    should_log = True
    
    page.wait_for_timeout(5000)

    # Individually download each mp3 file
    i=0
    for mp3 in mp3_urls:
        response = requests.get(mp3_urls[i])
        if i > 0:
            with open(title+str(i)+".mp3", "wb") as file:
                file.write(response.content)
                song_splices += [title+str(i)+".mp3"]  
            print("MP3 file downloaded successfully")
        i+=1
    
    def detect_leading_silence(sound, silence_threshold=-50.0, chunk_size=5):
        """
        sound is a pydub.AudioSegment
        silence_threshold is a dB quantity
        chunk_size is a ms quantity

        Checks audio chunk by chunk and returns audio with silence trimmed from ends.
        """
        trim_ms = 0

        assert chunk_size > 0 # avoid infinite loop
        while sound[trim_ms:trim_ms+chunk_size].dBFS < silence_threshold and trim_ms < len(sound):
            trim_ms += chunk_size

        return trim_ms

    # Combine mp3 files together
    song = AudioSegment.silent()
    for splice in song_splices:
        print("Adding snippet " + splice)
        splice = AudioSegment.from_mp3(path+"\\"+splice)
        if trim:
            start_trim = detect_leading_silence(splice)
            end_trim = detect_leading_silence(splice.reverse())
            duration = len(splice)    
            splice = splice[start_trim:duration-end_trim]
        song += splice
    
    # Get cover image
    cover = page.eval_on_selector("span[class^='sc-artwork']", "element => window.getComputedStyle(element).backgroundImage")
    cover_url = cover.replace('url("', '').replace('")', '').strip()

    def download_image(image_url):
        """
        image_url is a url leading to an image file

        Downloads image file as "cover.jpg"
        """
        response = requests.get(image_url)
        if response.status_code == 200:
            with open("cover.jpg", "wb") as file:
                file.write(response.content)
            print("Cover image downloaded successfully")

    download_image(cover_url)
    
    # Export final song and add metadata
    song.export(title+".mp3", format="mp3")
    print("Final track exported successfully")
    
    file = eyed3.load(path+"\\"+title+".mp3")
    file.initTag(version=(2, 3, 0))
    
    file.tag.title = title
    file.tag.artist = artist
    file.tag.images.set(3, open("cover.jpg", "rb").read(), "image/jpeg", u"cover")
    file.tag.save()

    print("Metadata added successfully")

    # Move to songs folder
    shutil.move(path+"\\"+title+".mp3", path+"\\songs\\"+title+".mp3")

    # Delete excess snippets of song
    for snip in os.listdir():
        if snip.startswith(title) and snip != title+".mp3":
            os.remove(snip)

    # Delete cover image
    os.remove("cover.jpg")

    browser.close()

    print("Done")

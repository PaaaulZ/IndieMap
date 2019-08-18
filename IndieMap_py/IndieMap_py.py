
import json
import requests
import re
import os
import csv
from bs4 import BeautifulSoup
from geopy.geocoders import Nominatim
import mysql.connector
import time
import logging
import sys

# --- START GLOBALS ---

spotify_api_key = ''
genius_api_key = ''
spotify_playlist_id = ''
dbhost = ''
dbuser = ''
dbpass = ''
dbase = ''
bypass_arg = ''
log_level = ''
songs_list = []
mydb = None

artists_to_ignore = ['chiazzetta','kaufman','management','rovere','nuvola','esposito','meli','the jab'] # Those artists are on Spotify but not on Genius so it will find something wrong.

# --- END GLOBALS ---

def search_for_new_artists():

    # --- REQUIRES SPOTIFY API KEY ---
    # Searches on the specified Spotify playlist for new artists and returns the updated list

    artists_list = load_artists_list()


    r = requests.get(f"https://api.spotify.com/v1/playlists/{spotify_playlist_id}/tracks", headers={"Accept":"application/json","Content-Type":"application/json","Authorization":"Bearer " + spotify_api_key})
    if r.status_code == 401:
        logging.critical("[Spotify] [searchForNewArtists] Access denied. Wrong/expired API key?")
        exit()

    if r.status_code != 200:
        logging.critical(f"[Spotify] [searchForNewArtists] Unable to get tracks from playlist {r.status_code}")
        exit()

    tracks_json = json.loads(r.text)
    tracks = tracks_json["items"]

    for i in range(len(tracks)):
        # Iterate through all the tracks in the playlist
        artists_tmp = tracks[i]["track"]["artists"]
        for j in range(len(artists_tmp)):

            artist_name_tmp = artists_tmp[j]["name"].rstrip().lower()

            if artist_name_tmp in artists_to_ignore:
                # HACK: Those artists are not on genius, it will find something wrong. NOTE: Using lowercase so we don't have to mess around with case-sensitive
                continue

            # Iterate through all the artists in the playlist
            
            if not artist_name_tmp in artists_list:
                # If it's new add it to the list of valid artists.
                logging.info("[Spotify] [searchForNewArtists] Found artist " + artist_name_tmp) 
                artist_id_tmp = fetch_artist_id(artist_name_tmp,"GENIUS")

                if artist_id_tmp is None:
                    logging.error(f"[Spotify] [searchForNewArtists]Skipped {artist_name_tmp} because I can't find the id on Genius. If you find it add it manually to the database")
                else:
                    artists_list.append(artist_name_tmp)

                    insert_cursor = mydb.cursor(buffered=True)
                    sql = "INSERT INTO artists (artist_id,artist_name) VALUES (%s, %s)"
                    val = (artist_id_tmp,artist_name_tmp)

                    insert_cursor.execute(sql,val)

        mydb.commit()

    return artists_list

def fetch_artist_id(name,where):
    # REQUIRES GENIUS API IF WHERE = 'GENIUS'
    # Gets the artist ID by searching the name of the artists and selecting the best match

    # HACK: Ugly code to fix those artists, Spotify calls it Carl Brave x Franco 126 but genius calls it Carl Brave x Franco126
    # TODO: Genius.com returns only 5 results when you search so i'll never find franco126. Need to find a better way

    if name == "carl brave x franco 126":
        logging.debug(f"[Genius] [fetchartist_id] switched {name} with hardcoded name")
        name = "carl Brave x franco126"
    elif name == 'ketra':
        logging.debug(f"[Genius] [fetchartist_id] switched {name} with hardcoded name")
        name = "takagi & ketra"
    elif name == "coma_cose":
        logging.debug(f"[Genius] [fetchartist_id] switched {name} with hardcoded name")
        name = 'coma cose'
    elif name == 'franco126':
        logging.debug(f"[Genius] [fetchartist_id] returned hardcoded ID for {name}")
        return 607653

    if where == 'GENIUS':

        r = requests.get(f"https://api.genius.com/search?q={name}", headers={"Accept":"application/json","Content-Type":"application/json","Authorization":"Bearer " + genius_api_key})

        search_json = json.loads(r.text)
        if search_json["meta"]["status"] != 200:
            error_code = search_json["meta"]["status"]
            logging.critical(f"[Genius] [fetchartist_id] Unable to fetch artist id for {name} ({error_code})")
            exit()
        hits = search_json["response"]["hits"]
        for i in range(len(hits)):
            primary_artist_name = hits[i]["result"]["primary_artist"]["name"].lower().rstrip()
            primary_artist_id = hits[i]["result"]["primary_artist"]["id"]
            if primary_artist_name == name.lower().rstrip():
                logging.debug(f"[Genius] [fetchartist_id] {name} => {primary_artist_id}")
                return primary_artist_id
            else:
                logging.debug(f"[Genius] [fetchartist_id] {primary_artist_name} does not match exactly with {name}. I'll continue and hope to find a perfect match!.")
    else:

        my_cursor = mydb.cursor()
        my_cursor.execute(f"SELECT artist_id FROM artists WHERE artist_name = '{name}' LIMIT 1")

        for res in my_cursor:
            # TODO: Useless for loop, remove!
            logging.debug(f"[Genius] [fetchartist_id] {name} => {res[0]} CACHE")
            return res[0]
        else:
            logging.debug(f"[Genius] [fetchartist_id] {name} NOT FOUND IN CACHE")
            return None


def fetch_songs(artist_id,artist,page_number):
    # REQUIRES GENIUS API KEY
    # Iterates through every artist and starts downloading songs

    if artist_id is None:
        logging.error(f"[Genius] [fetchSongs] Skipped {artist} because artist_id is None")
        return
    
    r = requests.get(f"https://api.genius.com/artists/{str(artist_id)}/songs/?page=" + str(page_number), headers={"Accept":"application/json","Content-Type":"application/json","Authorization":"Bearer " + genius_api_key})
    if r.status_code != 200:
        logging.critical(f"[Genius] [fetchSongs] Unable to get songs by {artist} ({r.status_code})")
        exit()

    songs_json = json.loads(r.text)
    songs = songs_json["response"]["songs"]
    next_page = songs_json["response"]["next_page"]

    # Empty "temporary" table

    for i in range(len(songs)):

        # DEBUG
        song_title_tmp = songs[i]["title"]
        song_id_tmp = songs[i]["id"]
        logging.info(f"[Genius] [fetchSongs] Found {song_title_tmp} on page {str(page_number)}")

        insert_cursor = mydb.cursor(buffered=True)

        sql = "INSERT INTO lastfetch (song_id,song_artist_id,song_name) VALUES (%s, %s, %s)"
        val = (song_id_tmp,artist_id,song_title_tmp)

        try:
            insert_cursor.execute(sql,val)
        except Exception as e:
            exception_code = e.args[0]
            if not exception_code == 1062:
                logging.warning(f"[Genius] [fetchSongs] Skipped {song_title_tmp} because is already present")
                continue
            

    if next_page is not None:
        # If after that for loop you find another page go for it.
        mydb.commit()
        fetch_songs(artist_id,artist,next_page)
    return

def start_fetching_songs(artists_list):
    # Iterate through the artists list and start downloading songs

    for i in range(len(artists_list)):
        artist = artists_list[i].rstrip()
        artist_id = fetch_artist_id(artist,"LOCAL")
        if artist_id == -1:
            continue
        logging.debug(f"[CODE] [startFetchingSongs] Fetching songs by {artist} ({artist_id})")
        fetch_songs(artist_id,artist,1)

    return

def get_lyrics_for_stored_songs():
    # REQUIRES GENIUS API KEY
    # Gets lyrics from the stored songs obtained with fetchSongs() and checks for cities names in the lyrics.

    todays_date = time.strftime('%Y-%m-%d %H-%M-%S')

    song_list_cursor = mydb.cursor(buffered=True)
    song_list_cursor.execute("SELECT * FROM lastfetch WHERE song_id NOT IN (SELECT song_id FROM alreadydone)")

    insert_cursor = mydb.cursor(buffered=True)

    for song in song_list_cursor:
        song_id_tmp = song[0]
        song_title_tmp = song[2]

        logging.info(f"[Genius] [getLyricsForStoredSongs] Searching for cities in {song_title_tmp}")
        r = requests.get(f"https://api.genius.com/songs/{song_id_tmp}", headers={"Accept":"application/json","Content-Type":"application/json","Authorization":"Bearer " + genius_api_key})

        if r.status_code != 200:
            logging.critical(f"[Genius] [getLyricsForStoredSongs] Unable to fetch lyrics for {song_title_tmp} ({song_id_tmp}) ({r.status_code})")
            exit()

        lyrics_json = json.loads(r.text)
        # "Generate" song lyrics URL
        song_lyrics_path = lyrics_json["response"]["song"]["path"]
        artist_id_tmp = lyrics_json["response"]["song"]["primary_artist"]["id"]
        lyrics_url = f"https://genius.com{song_lyrics_path}"
        rL = requests.get(lyrics_url)
        # Parse lyrics from html result
        soup = BeautifulSoup(rL.text, 'html.parser')
        div_tags = soup.find_all('div',{"class":"lyrics"})
        lyrics = ""
        for div_content in div_tags:
            lyrics += div_content.text
        # Got the lyrics, search for cities.

        f_city = open("cities.txt","r")
        cities = f_city.readlines() # Complete city list. Too much memory used if big city list
        for j in range(len(cities)):
            city_tmp = cities[j].rstrip()
            try:
                # I don't want to bother with case-sensitive so I just lowercase everything.
                index = lyrics.lower().index(city_tmp.lower())
                # If I found something the index var will return the index of the first letter, by doing this I get the full city name
                index_end = index + lyrics[index:].index(' ')
                first_char = lyrics[index][0] # The first character of the word that looks like a city
                full_word = lyrics[index:index_end].lower().rstrip() # The word that looks like a city
                if first_char.isupper() and full_word == city_tmp.lower():
                    lyrics_line_tmp = get_city_line(lyrics,"\n",full_word)
                    logging.info(f"[CODE] [getLyricsForStoredSongs] Found {full_word} in {song_title_tmp}!")
                    sql = "INSERT INTO songslocations (song_id, song_artist_id, song_city, song_latitude, song_longitude, song_lyricsUrl, song_lyricsLine, song_added, song_title) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                    val = (song_id_tmp,artist_id_tmp,full_word,-1,-1,lyrics_url,lyrics_line_tmp,todays_date,song_title_tmp)

                    try:
                        insert_cursor.execute(sql,val)
                    except Exception as e:
                        exception_code = e.args[0]
                        if not exception_code == 1062:
                            logging.warning(f"[Genius] [fetchSongs] Skipped {song_title_tmp} because is already present")
                            continue


            except ValueError:
                index = -1

    already_done_cursor = mydb.cursor(buffered=True)
    already_done_cursor.execute("INSERT INTO alreadydone (song_id) SELECT song_id FROM songslocations WHERE song_id NOT IN (SELECT song_id FROM alreadydone)")

    mydb.commit()
    
    return

def update_coordinates():

    # Finds coordinates for songs that do not have them.
    # Searches for the city coordinates with Nominatim.


    songs_cursor = mydb.cursor(buffered = True)
    songs_cursor.execute("SELECT * FROM `songslocations` WHERE song_latitude = -1 and song_longitude = -1 GROUP BY song_city ORDER BY song_city ASC")
    update_cursor = mydb.cursor(buffered = True)

    geolocator = Nominatim(user_agent = "IndieMap by PaaaulZ")

    for songs in songs_cursor:
        song_lyricsUrl = songs[5]
        song_city = songs[2]

        cached_city = search_locations_cache(song_city)

        if cached_city is None:
            cached_latitude = cached_city['song_latitude']
            cached_longitude = cached_city['song_longitude']
            update_cursor.execute(f"UPDATE songslocations SET song_latitude = {cached_latitude},song_longitude = {cached_longitude} WHERE song_city = '{song_city}'")
            logging.info(f"[CODE] [updateCoordinates] Found ({cached_latitude},{cached_longitude}) for {song_lyricsUrl} CACHE")
        else:
            location = geolocator.geocode(song_city)
            if location is None:
                logging.error(f"[Nominatim] [updateCoordinates] Can't find coordinates for {song_lyricsUrl}")
                continue
            else:
                update_cursor.execute(f"UPDATE songslocations SET song_latitude = {location.latitude},song_longitude = {location.longitude} WHERE song_city = '{song_city}'")
                logging.info(f"[Nominatim] [updateCoordinates] Found ({location.latitude},{location.longitude}) for {song_lyricsUrl} and updated every instance found!")

    mydb.commit()
        
        
 
    return

def get_city_line(string, first, last):
    # TODO: Fix this function

    lf_found = []

    try:

        string = string.lower().rstrip()
        last = last.lower().rstrip()

        row_before = 0
        row_after = len(string)

        # Search for \n closest to the city name

        for i in range(string.index(last)):
            tmp_1 = string[i]
            tmp_2 = string[i+1]
            if string[i] == '\n':
                # ok is a line feed, add it to the list
                if i <= string.index(last):
                    row_before = i
                else:
                    row_after = i
                lf_found.append(i)

        start = row_before
        end = row_after

        out_string = re.sub('[^a-zA-Z0-9 \n\.\'èéòòìàù]', '', string[start:end])
    except ValueError:
        out_string = ""
    return out_string.capitalize()

def load_artists_list():

    my_cursor = mydb.cursor()
    my_cursor.execute("SELECT * FROM artists WHERE 1")

    list = []

    for res in my_cursor:
        list.append(res[1])
 
    return list

def clear_temporary_tables():
    truncate_cursor = mydb.cursor()
    truncate_cursor.execute("TRUNCATE lastfetch")
    return

def search_locations_cache(city_name):

    my_cursor = mydb.cursor()
    my_cursor.execute(f"SELECT song_latitude,song_longitude FROM songslocations WHERE song_city = '{city_name.lower()}' LIMIT 1")

    for res in my_cursor:
        # TODO: Useless for loop, remove!
        return {'song_latitude':res[0],'song_longitude':res[1]}
    else:
        return None

def main():

    if len(sys.argv) == 1 and bypass_arg == '':

        logging.info("--------------------- RUNNING IN NORMAL MODE ---------------")
        clear_temporary_tables()
        artists_list = search_for_new_artists()
        start_fetching_songs(artists_list)
        get_lyrics_for_stored_songs()
        update_coordinates()
        logging.info("--------------------- DONE ---------------")

    else:

        if bypass_arg != '':
            logging.warning("YOU ARE BYPASSING sys.argv (bypassArg is set config.json)! Set bypassArg = '' to use sys.argv.")
            arg = bypass_arg
        else:
            arg = sys.argv[1]

        if arg == '-w':
            # Running in "wait for approval mode", I'll just fill the final table but leave the locations to -1. You can manually check the cities, remove wrong results and run again the script with -a to finalize.

            logging.info("--------------------- RUNNING IN WAIT FOR APPROVAL MODE ---------------")
            clear_temporary_tables()
            artists_list = search_for_new_artists()
            start_fetching_songs(artists_list)
            get_lyrics_for_stored_songs()
            logging.info("--------------------- DONE ---------------")

        elif arg == '-a':

            logging.info("--------------------- RUNNING IN APPROVAL MODE ---------------")
            update_coordinates()
            logging.info("--------------------- DONE ---------------")
        elif arg == '-xd':
            insertTitlesForgotten()



    return
 
if __name__ == "__main__":
    # Load configuration file with various API keys
    try:
        with open('config.json', 'r') as f:
            datastore = json.load(f)
            spotify_api_key = datastore["spotifyApiKey"]
            genius_api_key = datastore["geniusApiKey"]
            spotify_playlist_id = datastore["spotifyPlaylistID"]
            dbhost = datastore['dbhost']
            dbuser = datastore['dbuser']
            dbpass = datastore['dbpass']
            dbase = datastore['dbase']
            bypass_arg = datastore['bypassArg']
            log_level = datastore['logLevel']
    except IOError:
            print("config.json not found, create your own by following the README on https://github.com/PaaaulZ/IndieMap")
            exit()

    fh = logging.FileHandler('indiemap.log')
    if log_level == '' or log_level == 0:
        logging.basicConfig(format='%(asctime)s - [%(levelname)s]: %(message)s', level=logging.ERROR)
    elif log_level == 1:
        logging.basicConfig(format='%(asctime)s - [%(levelname)s]: %(message)s', level=logging.WARNING)
    else:
        logging.basicConfig(format='%(asctime)s - [%(levelname)s]: %(message)s', level=logging.DEBUG)
    log = logging.getLogger()
    log.addHandler(fh)


    mydb = mysql.connector.connect(host=dbhost,user=dbuser,passwd=dbpass,database=dbase)
    main()

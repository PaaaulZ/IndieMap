
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

spotifyApiKey = ''
geniusApiKey = ''
spotifyPlaylistID = ''
dbhost = ''
dbuser = ''
dbpass = ''
dbase = ''
bypassArg = ''
logLevel = ''
songsList = []
mydb = None

artistsToIgnore = ['chiazzetta','kaufman','management','rovere','nuvola','esposito','meli','the jab'] # Those artists are on Spotify but not on Genius so it will find something wrong.

# --- END GLOBALS ---

def searchForNewArtists():

    # --- REQUIRES SPOTIFY API KEY ---
    # Searches on the specified Spotify playlist for new artists and returns the updated list

    artistsList = loadArtistsList()


    r = requests.get(f"https://api.spotify.com/v1/playlists/{spotifyPlaylistID}/tracks", headers={"Accept":"application/json","Content-Type":"application/json","Authorization":"Bearer " + spotifyApiKey})
    if r.status_code == 401:
        logging.critical("[Spotify] [searchForNewArtists] Access denied. Wrong/expired API key?")
        exit()

    if r.status_code != 200:
        logging.critical(f"[Spotify] [searchForNewArtists] Unable to get tracks from playlist {r.status_code}")
        exit()

    tracksJson = json.loads(r.text)
    tracks = tracksJson["items"]

    for i in range(len(tracks)):
        # Iterate through all the tracks in the playlist
        artistsTMP = tracks[i]["track"]["artists"]
        for j in range(len(artistsTMP)):

            artistNameTMP = artistsTMP[j]["name"].rstrip().lower()

            if artistNameTMP in artistsToIgnore:
                # HACK: Those artists are not on genius, it will find something wrong. NOTE: Using lowercase so we don't have to mess around with case-sensitive
                continue

            # Iterate through all the artists in the playlist
            
            if not artistNameTMP in artistsList:
                # If it's new add it to the list of valid artists.
                logging.info("[Spotify] [searchForNewArtists] Found artist " + artistNameTMP) 
                artistIdTMP = fetchArtistID(artistNameTMP,"GENIUS")

                if artistIdTMP is None:
                    logging.error(f"[Spotify] [searchForNewArtists]Skipped {artistNameTMP} because I can't find the id on Genius. If you find it add it manually to the database")
                else:
                    artistsList.append(artistNameTMP)

                    insertCursor = mydb.cursor(buffered=True)
                    sql = "INSERT INTO artists (artist_id,artist_name) VALUES (%s, %s)"
                    val = (artistIdTMP,artistNameTMP)

                    insertCursor.execute(sql,val)

        mydb.commit()

    return artistsList

def fetchArtistID(name,where):
    # REQUIRES GENIUS API IF WHERE = 'GENIUS'
    # Gets the artist ID by searching the name of the artists and selecting the best match

    # HACK: Ugly code to fix those artists, Spotify calls it Carl Brave x Franco 126 but genius calls it Carl Brave x Franco126
    # TODO: Genius.com returns only 5 results when you search so i'll never find franco126. Need to find a better way

    if name == "carl brave x franco 126":
        logging.debug(f"[Genius] [fetchArtistID] switched {name} with hardcoded name")
        name = "carl Brave x franco126"
    elif name == 'ketra':
        logging.debug(f"[Genius] [fetchArtistID] switched {name} with hardcoded name")
        name = "takagi & ketra"
    elif name == "coma_cose":
        logging.debug(f"[Genius] [fetchArtistID] switched {name} with hardcoded name")
        name = 'coma cose'
    elif name == 'franco126':
        logging.debug(f"[Genius] [fetchArtistID] returned hardcoded ID for {name}")
        return 607653

    if where == 'GENIUS':

        r = requests.get(f"https://api.genius.com/search?q={name}", headers={"Accept":"application/json","Content-Type":"application/json","Authorization":"Bearer " + geniusApiKey})

        searchJson = json.loads(r.text)
        if searchJson["meta"]["status"] != 200:
            errorCode = searchJson["meta"]["status"]
            logging.critical(f"[Genius] [fetchArtistID] Unable to fetch artist id for {name} ({errorCode})")
            exit()
        hits = searchJson["response"]["hits"]
        for i in range(len(hits)):
            primaryArtistName = hits[i]["result"]["primary_artist"]["name"].lower().rstrip()
            primaryArtistID = hits[i]["result"]["primary_artist"]["id"]
            if primaryArtistName == name.lower().rstrip():
                logging.debug(f"[Genius] [fetchArtistID] {name} => {primaryArtistID}")
                return primaryArtistID
            else:
                logging.debug(f"[Genius] [fetchArtistID] {primaryArtistName} does not match exactly with {name}. I'll continue and hope to find a perfect match!.")
    else:

        mycursor = mydb.cursor()
        mycursor.execute(f"SELECT artist_id FROM artists WHERE artist_name = '{name}'")

        for res in mycursor:
            # TODO: Useless for loop, remove!
            logging.debug(f"[Genius] [fetchArtistID] {name} => {res[0]} CACHE")
            return res[0]
        else:
            logging.debug(f"[Genius] [fetchArtistID] {name} NOT FOUND IN CACHE")
            return None


def fetchSongs(artistID,artist,pageNumber):
    # REQUIRES GENIUS API KEY
    # Iterates through every artist and starts downloading songs

    if artistID is None:
        logging.error(f"[Genius] [fetchSongs] Skipped {artist} because artistID is None")
        return
    
    r = requests.get(f"https://api.genius.com/artists/{str(artistID)}/songs/?page=" + str(pageNumber), headers={"Accept":"application/json","Content-Type":"application/json","Authorization":"Bearer " + geniusApiKey})
    if r.status_code != 200:
        logging.critical(f"[Genius] [fetchSongs] Unable to get songs by {artist} ({r.status_code})")
        exit()

    songsJson = json.loads(r.text)
    songs = songsJson["response"]["songs"]
    nextPage = songsJson["response"]["next_page"]

    # Empty "temporary" table

    for i in range(len(songs)):

        # DEBUG
        songTitleTMP = songs[i]["title"]
        songIdTMP = songs[i]["id"]
        logging.info(f"[Genius] [fetchSongs] Found {songTitleTMP} on page {str(pageNumber)}")

        insertCursor = mydb.cursor(buffered=True)
        sql = "INSERT INTO lastfetch (song_id,song_artist_id,song_name) VALUES (%s, %s, %s)"
        val = (songIdTMP,artistID,songTitleTMP)

        try:
            insertCursor.execute(sql,val)
        except Exception as e:
            exceptionCode = e.args[0]
            if not exceptionCode == 1062:
                logging.warning(f"[Genius] [fetchSongs] Skipped {songTitleTMP} because is already present")
                continue
            

    if nextPage is not None:
        # If after that for loop you find another page go for it.
        mydb.commit()
        fetchSongs(artistID,artist,nextPage)
    return

def startFetchingSongs(artistsList):
    # Iterate through the artists list and start downloading songs

    for i in range(len(artistsList)):
        artist = artistsList[i].rstrip()
        artistID = fetchArtistID(artist,"LOCAL")
        if artistID == -1:
            continue
        logging.debug(f"[CODE] [startFetchingSongs] Fetching songs by {artist} ({artistID})")
        fetchSongs(artistID,artist,1)

    return

def getLyricsForStoredSongs():
    # REQUIRES GENIUS API KEY
    # Gets lyrics from the stored songs obtained with fetchSongs() and checks for cities names in the lyrics.

    todaysDate = time.strftime('%Y-%m-%d %H-%M-%S')

    songListCursor = mydb.cursor(buffered=True)
    songListCursor.execute("SELECT * FROM lastfetch WHERE song_id NOT IN (SELECT song_id FROM alreadydone)")

    insertCursor = mydb.cursor(buffered=True)

    for song in songListCursor:
        songIdTMP = song[0]
        songTitleTMP = song[2]

        logging.info(f"[Genius] [getLyricsForStoredSongs] Searching for cities in {songTitleTMP}")
        r = requests.get(f"https://api.genius.com/songs/{songIdTMP}", headers={"Accept":"application/json","Content-Type":"application/json","Authorization":"Bearer " + geniusApiKey})

        if r.status_code != 200:
            logging.critical(f"[Genius] [getLyricsForStoredSongs] Unable to fetch lyrics for {songTitleTMP} ({songIdTMP}) ({r.status_code})")
            exit()

        lyricsJson = json.loads(r.text)
        # "Generate" song lyrics URL
        songLyricsPath = lyricsJson["response"]["song"]["path"]
        artistIdTMP = lyricsJson["response"]["song"]["primary_artist"]["id"]
        lyricsUrl = f"https://genius.com{songLyricsPath}"
        rL = requests.get(lyricsUrl)
        # Parse lyrics from html result
        soup = BeautifulSoup(rL.text, 'html.parser')
        div_tags = soup.find_all('div',{"class":"lyrics"})
        lyrics = ""
        for divContent in div_tags:
            lyrics += divContent.text
        # Got the lyrics, search for cities.

        fCity = open("cities.txt","r")
        cities = fCity.readlines() # Complete city list. Too much memory used if big city list
        for j in range(len(cities)):
            cityTMP = cities[j].rstrip()
            try:
                # I don't want to bother with case-sensitive so I just lowercase everything.
                index = lyrics.lower().index(cityTMP.lower())
                # If I found something the index var will return the index of the first letter, by doing this I get the full city name
                indexEnd = index + lyrics[index:].index(' ')
                firstChar = lyrics[index][0] # The first character of the word that looks like a city
                fullWord = lyrics[index:indexEnd].lower().rstrip() # The word that looks like a city
                if firstChar.isupper() and fullWord == cityTMP.lower():
                    lyricsLineTMP = getCityLine(lyrics,"\n",fullWord)
                    logging.info(f"[CODE] [getLyricsForStoredSongs] Found {fullWord} in {songTitleTMP}!")
                    sql = "INSERT INTO songslocations (song_id, song_artist_id, song_city, song_latitude, song_longitude, song_lyricsUrl, song_lyricsLine, song_added, song_title) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                    val = (songIdTMP,artistIdTMP,fullWord,-1,-1,lyricsUrl,lyricsLineTMP,todaysDate,songTitleTMP)

                    insertCursor.execute(sql,val)

            except ValueError:
                index = -1

    alreadyDoneCursor = mydb.cursor(buffered=True)
    alreadyDoneCursor.execute("INSERT INTO alreadydone (song_id) SELECT song_id FROM songslocations WHERE song_id NOT IN (SELECT song_id FROM alreadydone)")

    mydb.commit()
    
    return

def updateCoordinates():

    # Finds coordinates for songs that do not have them.
    # Searches for the city coordinates with Nominatim.


    songsCursor = mydb.cursor(buffered = True)
    songsCursor.execute("SELECT * FROM `songslocations` WHERE song_latitude = -1 and song_longitude = -1 GROUP BY song_city ORDER BY song_city ASC")
    updateCursor = mydb.cursor(buffered = True)

    geolocator = Nominatim(user_agent = "IndieMap by PaaaulZ")

    for songs in songsCursor:
        song_lyricsUrl = songs[5]
        song_city = songs[2]

        cachedCity = searchLocationsCache(song_city)

        if cachedCity is None:
            cachedLatitude = cachedCity['song_latitude']
            cachedLongitude = cachedCity['song_longitude']
            updateCursor.execute(f"UPDATE songslocations SET song_latitude = {cachedLatitude},song_longitude = {cachedLongitude} WHERE song_city = '{song_city}'")
            logging.info(f"[CODE] [updateCoordinates] Found ({cachedLatitude},{cachedLongitude}) for {song_lyricsUrl} CACHE")
        else:
            location = geolocator.geocode(song_city)
            if location is None:
                logging.error(f"[Nominatim] [updateCoordinates] Can't find coordinates for {song_lyricsUrl}")
                continue
            else:
                updateCursor.execute(f"UPDATE songslocations SET song_latitude = {location.latitude},song_longitude = {location.longitude} WHERE song_city = '{song_city}'")
                logging.info(f"[Nominatim] [updateCoordinates] Found ({location.latitude},{location.longitude}) for {song_lyricsUrl} and updated every instance found!")

    mydb.commit()
        
        
 
    return

def getCityLine(string, first, last):
    # TODO: Fix this function
    # THIS SUCKS

    lfFound = []

    try:

        string = string.lower().rstrip()
        last = last.lower().rstrip()

        rowBefore = 0
        rowAfter = len(string)

        # Search for \n closest to the city name

        for i in range(string.index(last)):
            tmp1 = string[i]
            tmp2 = string[i+1]
            if string[i] == '\n':
                # ok is a line feed, add it to the list
                if i <= string.index(last):
                    rowBefore = i
                else:
                    rowAfter = i
                lfFound.append(i)

        start = rowBefore
        end = rowAfter

        outString = re.sub('[^a-zA-Z0-9 \n\.\'èéòòìàù]', '', string[start:end])
    except ValueError:
        outString = ""
    return outString.capitalize()

def loadArtistsList():

    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM artists WHERE 1")

    list = []

    for res in mycursor:
        list.append(res[1])
 
    return list

def clearTemporaryTables():
    truncateCursor = mydb.cursor()
    truncateCursor.execute("TRUNCATE lastfetch")
    return

def searchLocationsCache(cityName):

    mycursor = mydb.cursor()
    mycursor.execute(f"SELECT song_latitude,song_longitude FROM songslocations WHERE song_city = '{cityName.lower()}' LIMIT 1")

    for res in mycursor:
        # TODO: Useless for loop, remove!
        return {'song_latitude':res[0],'song_longitude':res[1]}
    else:
        return None

def main():

    if len(sys.argv) == 1 and bypassArg == '':

        logging.info("--------------------- RUNNING IN NORMAL MODE ---------------")
        clearTemporaryTables()
        artistsList = searchForNewArtists()
        startFetchingSongs(artistsList)
        getLyricsForStoredSongs()
        updateCoordinates()
        logging.info("--------------------- DONE ---------------")

    else:

        if bypassArg != '':
            logging.warning("YOU ARE BYPASSING sys.argv (bypassArg is set config.json)! Set bypassArg = '' to use sys.argv.")
            arg = bypassArg
        else:
            arg = sys.argv[1]

        if arg == '-w':
            # Running in "wait for approval mode", I'll just fill the final table but leave the locations to -1. You can manually check the cities, remove wrong results and run again the script with -a to finalize.

            logging.info("--------------------- RUNNING IN WAIT FOR APPROVAL MODE ---------------")
            clearTemporaryTables()
            artistsList = searchForNewArtists()
            startFetchingSongs(artistsList)
            getLyricsForStoredSongs()
            logging.info("--------------------- DONE ---------------")

        elif arg == '-a':

            logging.info("--------------------- RUNNING IN APPROVAL MODE ---------------")
            updateCoordinates()
            logging.info("--------------------- DONE ---------------")
        elif arg == '-xd':
            insertTitlesForgotten()



    return
 
if __name__ == "__main__":
    # Load configuration file with various API keys
    try:
        with open('config.json', 'r') as f:
            datastore = json.load(f)
            spotifyApiKey = datastore["spotifyApiKey"]
            geniusApiKey = datastore["geniusApiKey"]
            spotifyPlaylistID = datastore["spotifyPlaylistID"]
            dbhost = datastore['dbhost']
            dbuser = datastore['dbuser']
            dbpass = datastore['dbpass']
            dbase = datastore['dbase']
            bypassArg = datastore['bypassArg']
            logLevel = datastore['logLevel']
    except IOError:
            print("config.json not found, create your own by following the README on https://github.com/PaaaulZ/IndieMap")
            exit()

    fh = logging.FileHandler('indiemap.log')
    if logLevel == '' or logLevel == 0:
        logging.basicConfig(format='%(asctime)s - [%(levelname)s]: %(message)s', level=logging.ERROR)
    elif logLevel == 1:
        logging.basicConfig(format='%(asctime)s - [%(levelname)s]: %(message)s', level=logging.WARNING)
    else:
        logging.basicConfig(format='%(asctime)s - [%(levelname)s]: %(message)s', level=logging.DEBUG)
    log = logging.getLogger()
    log.addHandler(fh)


    mydb = mysql.connector.connect(host=dbhost,user=dbuser,passwd=dbpass,database=dbase)
    main()



# --- START UNUSED CODE, MAY BE UGLY --- 

#def oldJsonToDB():

    # --- WARNING: UGLY UNUSED CODE --- 

#    f = open('found4map.json', 'r')
#    foundCities = json.load(f)

#    insertCursor = mydb.cursor(buffered=True)
#    todaysDate = time.strftime('%Y-%m-%d %H-%M-%S')
    
#    for fakeIndex in foundCities:
#        artist = foundCities[str(fakeIndex)][0]['artist']
#        city = foundCities[str(fakeIndex)][0]['city']
#        latitude = foundCities[str(fakeIndex)][0]['latitude']
#        longitude = foundCities[str(fakeIndex)][0]['longitude']
#        lyricsLine = foundCities[str(fakeIndex)][0]['lyricsLine']
#        lyricsUrl = foundCities[str(fakeIndex)][0]['lyricsUrl']
#        title = foundCities[str(fakeIndex)][0]['title']
#        ids = fetchIdsFromUrl(lyricsUrl)
#        if ids is None:
#            print(f"{artist} - {title} NOT FOUND")
#        else:
#            artist_id = ids['artist_id']
#            song_id = ids['song_id']
#            sql = "INSERT INTO songslocations (song_id,song_artist_id,song_city,song_latitude,song_longitude,song_lyricsUrl,song_lyricsLine,song_added) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
#            val = (song_id,artist_id,city,latitude,longitude,lyricsUrl,lyricsLine,todaysDate)
#            try:
#                insertCursor.execute(sql,val)
#            except Exception as e:
#                exceptionCode = e.args[0]
#                if not exceptionCode == 1062:
#                    print(f"{songTitleTMP} is already present, skipped.")
#                    continue
#    mydb.commit()

#    return

#def fetchIdsFromUrl(url):

#    r = requests.get(url)
#    str = r.text
#    x = re.findall("var TRACKING_DATA = {\"Song ID\":[0-9]{1,300}", str)
#    y = re.findall("\"Primary Artist ID\":[0-9]{1,300}", str)
#    if len(x) > 0 and len(y) > 0:
#        return {'artist_id':y[0].replace('\"Primary Artist ID\":',''),'song_id':x[0].replace('var TRACKING_DATA = {\"Song ID\":','')}
#    else:
#        return None

#def fixIndexes():

#    # WARNING: THIS PROCEDURE IS A FIX FOR THE BAD INDEXES IN FOUND4MAP.JSON DUE TO ME MANUALLY REMOVING SONGS.
#    # PLEASE BACKUP FOUND4MAP.JSON BEFORE RUNNING THIS PROCEDURE

#    if not os.path.exists('found4map.json'):
#        return

#    f = open('found4map.json','r')
#    f2 = open('found4map_fixed.json','a')
#    count = 0
#    for row in f:

#        try:
#            artistIndex = row.index(': [{')-1
#        except:
#            f2.write(row)
#            continue

#        indexSlice = row[1:artistIndex].replace('"','').rstrip()

#        row = row.replace('"' + str(indexSlice) + '": [{','"' + str(count) + '": [{')

#        f2.write(row)
#        count += 1

#    f.close()
#    f2.close()

#    os.remove('found4map.json')
#    os.rename('found4map_fixed.json','found4map.json')
    
#    return

#def lastFakeIndex():

#    higher = 0
#    with open('found4map.json','r') as f:
#        fJson = json.load(f)
#        for fakeIndex in fJson:
#            if int(fakeIndex) > int(higher):
#                higher = int(fakeIndex)
#    return higher


# --- END UNUSED CODE, MAY BE UGLY --- 
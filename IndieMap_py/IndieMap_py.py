
import json
import requests
import re
import os
import csv
from bs4 import BeautifulSoup
from geopy.geocoders import Nominatim

spotifyApiKey = ''
geniusApiKey = ''
spotifyPlaylistID = ''
songsList = []

def searchForNewArtists():

    # REQUIRES SPOTIFY API KEY 
    # Searches on the specified Spotify playlist for new artists

    r = requests.get("https://api.spotify.com/v1/playlists/" + spotifyPlaylistID + "/tracks", headers={"Accept":"application/json","Content-Type":"application/json","Authorization":"Bearer " + spotifyApiKey})
    if r.status_code != 200:
        print("Unable to get tracks from playlist ",r.status_code)
        exit()
    tracksJson = json.loads(r.text)
    for i in range(len(tracksJson["items"])):
        # Iterate through all the tracks in the playlist
        for j in range((len(tracksJson["items"][i]["track"]["artists"]))):
            # Iterate through all the artists in the playlist
            exists = os.path.isfile('artists.txt')
            if exists:
                # If file exists check if artist is new
                if not tracksJson["items"][i]["track"]["artists"][j]["name"] in open('artists.txt').read():
                    # If it's new add it to the list of valid artists.
                    f = open("artists.txt","a")
                    print("Found artist " + tracksJson["items"][i]["track"]["artists"][j]["name"].rstrip() + " [" + str(i+1) + "/" + str(len(tracksJson["items"])) + "]") 
                    f.write(tracksJson["items"][i]["track"]["artists"][j]["name"].rstrip() + "\n")
                    f.close()
            else:
                # If file does not exist the artist is 100% new
                    f = open("artists.txt","a")
                    print("Found artist " + tracksJson["items"][i]["track"]["artists"][j]["name"].rstrip() + " [" + str(i+1) + "/" + str(len(tracksJson["items"])) + "]") 
                    f.write(tracksJson["items"][i]["track"]["artists"][j]["name"].rstrip() + "\n")
                    f.close()                
    return

def fetchArtistID(artist):
    # REQUIRES GENIUS API
    # Gets the artist ID by searching the name of the artists and selecting the best match
    r = requests.get("https://api.genius.com/search?q=" + artist, headers={"Accept":"application/json","Content-Type":"application/json","Authorization":"Bearer " + geniusApiKey})
    # HACK: Ugly code to fix this artist, Spotify calls it Carl Brave x Franco 126 but genius calls it Carl Brave x Franco126
    if artist == "Carl Brave x Franco 126":
        artist = "Carl Brave x Franco126"
    searchJson = json.loads(r.text)
    if searchJson["meta"]["status"] != 200:
        print("Unable to fetch artist id")
        exit()
    for i in range(len(searchJson["response"]["hits"])):
        # HACK: The for loop is not necessary, might fix later.
        return searchJson["response"]["hits"][i]["result"]["primary_artist"]["id"]


def fetchSongs(artistID,artist,pageNumber):
    # REQUIRES GENIUS API KEY
    # Iterates through every artist and starts downloading songs

    # TODO: Just for the first time stores the songs list in memory. Might be worth to switch to a file/DB?
    
    r = requests.get("https://api.genius.com/artists/" + str(artistID) + "/songs/?page=" + str(pageNumber), headers={"Accept":"application/json","Content-Type":"application/json","Authorization":"Bearer " + geniusApiKey})
    if r.status_code != 200:
        print("Unable to get songs by " + artist)
        exit()
    songsJson = json.loads(r.text)
    for i in range(len(songsJson["response"]["songs"])):

        # DEBUG
        print("Found song " + songsJson["response"]["songs"][i]["title"] + " [" + str(i+1) + "/" + str(len(songsJson["response"]["songs"])) + "] page " + str(pageNumber))
        songsList.append({"id":songsJson["response"]["songs"][i]["id"],"title":songsJson["response"]["songs"][i]["title"],"artist":artist})

    if songsJson["response"]["next_page"] is not None:
        # If after that for loop you find another page go for it.
        fetchSongs(artistID,artist,songsJson["response"]["next_page"])
    return

def startFetchingSongs():
    # Iterate through the artists list and start downloading songs
    try:
        artistsFile = open("artists.txt","r")
        artists = artistsFile.readlines()
        for i in range(len(artists)):
            artist = artists[i].rstrip()
            artistID = fetchArtistID(artist)
            # DEBUG
            print("--- FETCHING SONGS FOR " + artist + " ---")
            fetchSongs(artistID,artist,1)
    except IOError:
        print("Unable to find artists.txt, did you run searchForNewArtists?")
        exit()
    return

def getLyricsForStoredSongs():
    # REQUIRES GENIUS API KEY
    # Gets lyrics from the stored songs obtained with fetchSongs() and checks for cities names in the lyrics.

    foundObj = {}
    count = 0

    for i in range(len(songsList)):

        exists = os.path.isfile('done.txt')
        if exists:
            if str(songsList[i]["id"]) in open('done.txt').read():
                    # If I already analyzed this song just skip it.
                    next

        # DEBUG
        print("Searching for cities in " + songsList[i]["title"] + " [" + str(i+1) + "/" + str(len(songsList)) + "]")
        r = requests.get("https://api.genius.com/songs/" + str(songsList[i]["id"]), headers={"Accept":"application/json","Content-Type":"application/json","Authorization":"Bearer " + geniusApiKey})
        if r.status_code != 200:
            print("Unable to fetch lyrics for song " + songsList[i]["title"] + " with ID " + str(songsList[i]["id"]))
            exit()
        lyricsJson = json.loads(r.text)
        # Generate song lyrics URL
        lyricsUrl = "https://genius.com" + lyricsJson["response"]["song"]["path"]
        rL = requests.get(lyricsUrl)
        soup = BeautifulSoup(rL.text, 'html.parser')
        div_tags = soup.find_all('div',{"class":"lyrics"})
        lyrics = ""
        for x in div_tags:
            lyrics += x.text
        # Got the lyrics, search for cities.

        fCity = open("cities.txt","r")
        cities = fCity.readlines()
        ffound = open('found.json',"a")

        for j in range(len(cities)):
            try:
                # I don't want to bother with case-sensitive so I just lowercase everything.
                index = lyrics.lower().index(cities[j].lower().rstrip())
                # If I found something the index var will return the index of the first letter, by doing this I get the full city name
                indexEnd = index + len(cities[j])
                if lyrics[index][0].isupper() and lyrics[index:indexEnd].lower().rstrip() == cities[j].lower().rstrip():
                    # To prevent getting trash (not real cities) i check if the first letter is uppercase. Most of the times this works.
                    # And i check if the name matches EXACTLY
                    foundObj[count] = []  
                    foundObj[count].append({  
                        'artist': songsList[i]["artist"].rstrip(),
                        'title': songsList[i]["title"].rstrip(),
                        'city': cities[j].rstrip().capitalize(),
                        'lyricsUrl': lyricsUrl,
                        'lyricLine': getCityLine(lyrics,"\n",cities[j]),
                        'latitude': -1,
                        'longitude': -1
                    })
                    count += 1
                    print("FOUND " + lyrics[index:indexEnd].rstrip() + " in " + songsList[i]["title"].rstrip() + " by " + songsList[i]["artist"].rstrip())
            except ValueError:
                index = -1
        
        f = open("done.txt","a")
        f.write(str(songsList[i]["id"]) + "\n")
        f.close()
        lyrics = ""
    json.dump(foundObj, ffound)
    ffound.close()
    return


def getCoordinates():

    # Searches for the city coordinates with Nominatim.
    # TODO: Implement a cache system so I don't have to search a city multiple times. Example: happens that I already know the coordinates for Rome because I found it in another song.

    geolocator = Nominatim(user_agent = "IndieMap by PaaaulZ")
    f = open('found.json', 'r')
    f4m = open('found4map.json','a')
    foundCities = json.load(f)

    for i in range(len(foundCities)):
        # HACK: I have to fix this horrible JSON writer/reader. It's 2AM have mercy
        toSearch = foundCities[str(i)][0]['city']
        location = geolocator.geocode(toSearch)
        if location is None:
            print("NOT FOUND coordinates for " + toSearch + " [" + str(i+1) + "/" + str(len(foundCities)) + "]")
        else:
            foundCities[str(i)][0]['latitude'] = location.latitude
            foundCities[str(i)][0]['longitude'] = location.longitude
            print("Found coordinates for " + toSearch + " [" + str(i+1) + "/" + str(len(foundCities)) + "]")

    json.dump(foundCities,f4m)
    f.close()
    f4m.close()

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

        # Your start index will be the \n before the last one \I found earlier.
        # Your end index will be the last one

        #if len(lfFound) >= 2:
        #    #start = lfFound[len(lfFound)-2] + len(first)
        #    #end = lfFound[len(lfFound)-1] + len(last)
        #    start = lfFound[len(lfFound)-2]
        #    end = string.index(last, start) + len(last)
        #else:
        #    start = 0
        #    end = string.index(last, start) + len(last)

        #start = lfFound[len(lfFound)-1] + len(first)
        #end = string.index(last, start) + len(last)
        outString = re.sub('[^a-zA-Z0-9 \n\.\'èéòòìàù]', '', string[start:end])
    except ValueError:
        outString = ""
    return outString.capitalize()

# Load configuration file with various API keys
try:
    with open('config.json', 'r') as f:
        datastore = json.load(f)
        spotifyApiKey = datastore["spotifyApiKey"]
        geniusApiKey = datastore["geniusApiKey"]
        spotifyPlaylistID = datastore["spotifyPlaylistID"]
except IOError:
        print("config.json not found, create your own by following the README on https://github.com/PaaaulZ/IndieMap")
        exit()

searchForNewArtists()
startFetchingSongs()
getLyricsForStoredSongs()
getCoordinates()







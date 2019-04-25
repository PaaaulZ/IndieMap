
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

# Configuration loading routine

with open('config.json', 'r') as f:
	datastore = json.load(f)
	spotifyApiKey = datastore["spotifyApiKey"]
	geniusApiKey = datastore["geniusApiKey"]
	spotifyPlaylistID = datastore["spotifyPlaylistID"]

# Functions

def getArtistsFromSpotifyPlaylist():

    r = requests.get("https://api.spotify.com/v1/playlists/" + spotifyPlaylistID + "/tracks", headers={"Accept":"application/json","Content-Type":"application/json","Authorization":"Bearer " + spotifyApiKey})
    if r.status_code != 200:
        print("Unable to get tracks from playlist ",r.status_code)
        exit()
    tracksJson = json.loads(r.text)
    for i in range(len(tracksJson["items"])):
        for j in range((len(tracksJson["items"][i]["track"]["artists"]))):
            if not tracksJson["items"][i]["track"]["artists"][j]["name"] in open('artists.txt').read():
                f = open("artists.txt","a")
                f.write(tracksJson["items"][i]["track"]["artists"][j]["name"] + "\n")
                f.close()
    return

def fetchArtistID(artist):
    r = requests.get("https://api.genius.com/search?q=" + artist, headers={"Accept":"application/json","Content-Type":"application/json","Authorization":"Bearer " + geniusApiKey})
    if artist == "Carl Brave x Franco 126":
        artist = "Carl Brave x Franco126"
    searchJson = json.loads(r.text)
    if searchJson["meta"]["status"] != 200:
        print("Unable to fetch artist id")
        exit()
    for i in range(len(searchJson["response"]["hits"])):
        return searchJson["response"]["hits"][i]["result"]["primary_artist"]["id"]


def getSongsFromArtist_step2(artistID,artist,pageNumber):

    r = requests.get("https://api.genius.com/artists/" + str(artistID) + "/songs/?page=" + str(pageNumber), headers={"Accept":"application/json","Content-Type":"application/json","Authorization":"Bearer " + geniusApiKey})
    if r.status_code != 200:
        print("Unable to get songs by " + artist)
        exit()
    songsJson = json.loads(r.text)
    for i in range(len(songsJson["response"]["songs"])):
        # DEBUG
        print("--- SONG " + songsJson["response"]["songs"][i]["title"] + " ---")
        songsList.append({"id":songsJson["response"]["songs"][i]["id"],"title":songsJson["response"]["songs"][i]["title"],"artist":artist})

    if songsJson["response"]["next_page"] is not None:
        getSongsFromArtist_step2(artistID,artist,songsJson["response"]["next_page"])
    return

def getSongsFromArtist_step1():
    f = open("artists.txt","r")
    fl = f.readlines()
    for i in range(len(fl)):
        artist = fl[i]
        artistID = fetchArtistID(artist)
        # DEBUG
        print("--- ARTIST " + artist + " ---")
        getSongsFromArtist_step2(artistID,artist,1)   
    return

def getLyricsForStoredSongs():
    for i in range(len(songsList)):

        exists = os.path.isfile('done.txt')
        if exists:
            if str(songsList[i]["id"]) in open('done.txt').read():
                    next

        # DEBUG
        print("--- SONG CITY " + songsList[i]["title"] + " ---")
        r = requests.get("https://api.genius.com/songs/" + str(songsList[i]["id"]), headers={"Accept":"application/json","Content-Type":"application/json","Authorization":"Bearer " + geniusApiKey})
        if r.status_code != 200:
            print("Unable to fetch lyrics for song " + songsList[i]["title"] + " with ID " + str(songsList[i]["id"]))
            exit()
        lyricsJson = json.loads(r.text)
        lyricsUrl = "https://genius.com" + lyricsJson["response"]["song"]["path"]
        rL = requests.get(lyricsUrl)
        soup = BeautifulSoup(rL.text, 'html.parser')
        div_tags = soup.find_all('div',{"class":"lyrics"})
        lyrics = ""
        for x in div_tags:
            lyrics += x.text

        fCity = open("cities.txt","r")
        fl = fCity.readlines()
        for j in range(len(fl)):
            try:
                index = lyrics.lower().index(fl[j].lower())
                indexEnd = index + len(fl[j])
                if lyrics[index][0].isupper():
                    ffound = open('found.txt',"a")
                    ffound.write("" + songsList[i]["artist"].rstrip() + ";" + songsList[i]["title"].rstrip() + ";" + fl[j] + "\n") 
                    ffound.close()
                    print("Trovato " + lyrics[index:indexEnd] + " in " + songsList[i]["title"].rstrip() + " by " + songsList[i]["artist"].rstrip())
            except ValueError:
                index = -1
        
        
        f = open("done.txt","a")
        f.write(str(songsList[i]["id"]) + "\n")
        f.close()
    return


def getCoordinates():

    alreadyDone = []

    geolocator = Nominatim(user_agent = "IndieMap by PaaaulZ")

    csv.register_dialect('myDialect',delimiter = ';',skipinitialspace=True)

    f = open('locations.txt','a')
    with open('found.txt', 'r') as csvFile:
        fl = csvFile.readlines()
        for i in range(len(fl)):
            flSplit = fl[i].split(";")
            toSearch = flSplit[2].rstrip()
            if toSearch not in alreadyDone:
                print("--- SEARCHING COORDINATES FOR " + toSearch + " ---")
                location = geolocator.geocode(toSearch)
                if location is None:
                    print(toSearch + " is none")
                else:
                    f.write(fl[i].rstrip() + ";" + str(location.latitude) + ";" + str(location.longitude) + "\n")
                    alreadyDone.append(toSearch)

    f.close()

    return


getArtistsFromSpotifyPlaylist()
getSongsFromArtist_step1()
getLyricsForStoredSongs()
getCoordinates()








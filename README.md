# IndieMap
A Python script that finds cities in lyrics of songs by Italian Indie Artists and a PHP page to show everything on a map

---

Want to see it working? Check my [LIVE VERSION](http://paaaulz.altervista.org)

## DISCLAIMER

This is my first Python project and I'm a bit rusty in PHP so I wrote everything with the knowledge I have at this time. Don't expect something complicated, it's just a simple project for a simple concept. I will update the code and make it better as I learn so I'm kinda using this code to show my future self how much I learned and improved.

I think the Python code looks better than before but the PHP side it's a bit of a mess. Maybe I'll switch to React.js and learn it.


## A BIT OF BACKGROUND

For those who don't know there is a meme in the Italian community about Indie artists using cities in every song, even the smallest unknown city (see Peschiera del Garda). I started this project to see if it's just a meme or the situation is really like that and (why not?) get better at Python. So is the meme true? Judge by yourself watching the [MAP](http://paaaulz.altervista.org).

## CONTENT

- cities.txt

It's a list of cities and countries of the world. I just manually removed some ambiguous names like "Amore, Onore, Pandino", they exist but unfortunately are also words in the italian dictionary so to avoid false matches I had to delete those.


---

- IndieMap_py.py

It's the download script, works in different steps:

1) Reads artists from a Spotify playlist of only Italian Indie songs and adds them to the **artists** table, at the ends of this you'll have a list of Italian Indie artists to work with.
2) Reads songs titles from Genius for every single artist and stores them in the **lastfetch** table.
3) Reads lyrics for every song stored before and searches for cities/countries. Songs done are saved in the **alreadydone** table so next time they will be skipped, matches found are stored in the **songslocations** table (just info about the song and the city found, nothing more for now).
4) Reads the **songslocations** table and adds informations about the city (latitude and longitude).

At the end of this you will have:

- Artist.
- Title.
- City/Country name found in the lyrics.
- Genius link to read the full lyrics.
- A section of the lyrics to show where the match has been found (I need to improve the code, that's temporary but works).
- Latitude.
- Longitude.

**You will need a config.json and config.php, see config section below**

---

_website/map.php

It's the webpage to show the locations on the map, just that, nothing more.

---

_website/config.php

It's the webpage configuration, contains only the MySQL connection informations.

---

_website/getDetails.php

It's used to get the **lyricsUrl** and **lyricsLine** and show it near the map when you click on a song, nothing more.

---

## CONFIG.JSON TEMPLATE

```json
{
  "spotifyApiKey": "SPOTIFY_API_KEY",
  "spotifyPlaylistID": "37i9dQZF1DX6PSDDh80gxI",
  "geniusApiKey": "GENIUS.COM_API_KEY",
  "dbhost": "DATABASE_IP",
  "dbuser": "DATABASE_USERNAME",
  "dbpass": "DATABASE_PASSWORD",
  "dbase": "indiemap",
}
```

You can of course change the **spotifyPlaylistID** with a Spotify playlist id of your choice.
You can use the **bypassArg** config to force some arguments if you don't want to use arguments from the command line. I personally use bypassArgs = '-w'. Arguments for this script are:

-w: Runs the script without searching for latitude and longitude so you can go into the database and delete errors, ambiguous names or things you don't want on your map.
-a: Updates latitude and longitude for songs without coordinates (usually launched after a -w run).

You can use the **logLevel** config (0 => ERROR, 1 => WARNING , 2+ => DEBUG) to choose what you want to see in the logs. 0 is only errors, 1 shows even warnings, everything else shows also debug informations.
You can use the **noFeaturing** config (true/false) to only get the primary artist from songs.

---

## CONFIG.PHP TEMPLATE

```php
error_reporting(0);

$dbhost = 'DATABASE_IP';
$dbuser = 'DATABASE_USERNAME';
$dbpass = 'DATABASE_PASSWORD';
$dbase = 'indiemap';

$dbc = mysqli_connect($dbhost,$dbuser,$dbpass,$dbase);
if (mysqli_connect_errno())
{
    die("[ERROR] [config] MySQL connection error.");
}
```

## REQUIREMENTS

- Python 3.x

`https://www.python.org/downloads/`

---

- Requests

`pip3 install requests`

---

- MySQL Connector

`pip3 install mysql-connector`

---

- BeautifulSoup

`pip3 install BeautifulSoup4`

---

- Geopy

`pip3 install geopy`

---

- MySQL Server

---

## USAGE

1) Download or clone this repository.
2) Create the tables in your database by using **indiemap.sql**.
3) Create a **config.json** with the template above and put it near **IndieMap_py.py**
4) Launch **IndieMap_py.py** and wait for it to finish.
5) Copy the contents of **_website** folder and paste into your webserver folder.
6) Visit **http://[your_server]/map.php**

## SIDE NOTES

If you have a Google Maps API you can change provider for GeoPy and search cities/countries with Google Maps instead of Nominatim. To do this:

Change the import from:

```python
from geopy.geocoders import Nominatim
```

to:

```python
from geopy.geocoders import GoogleV3
```

---

In **getCoordinates()** from:

```python
geolocator = Nominatim(user_agent = "IndieMap by PaaaulZ")
```

to:

```python
geolocator = GoogleV3(api_key=YOUR_GOOGLE_API_KEY_HERE)
```

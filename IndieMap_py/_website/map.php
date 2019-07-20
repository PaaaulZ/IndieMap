<!DOCTYPE html>
<html>
<head>
	<?php header('Content-Type: text/html; charset=utf-8'); ?>
	<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<title>IndieMap by PaaaulZ | https://github.com/PaaaulZ/IndieMap</title>
	<!-- Load leaflet maps library and stylesheet -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.4.0/dist/leaflet.css" integrity="sha512-puBpdR0798OZvTTbP4A8Ix/l+A4dHDD0DGqYW6RQ+9jxkRFclaxxQb/SJAWZfWAkuyeQUytO7+7N4QKrDh+drA==" crossorigin=""/>
    <script src="https://unpkg.com/leaflet@1.4.0/dist/leaflet.js" integrity="sha512-QVftwZFqvtRNi0ZyCtsznlKSWOStnDORoefr1enyq5mVL4tmKB3S/EnC3rRJcxCPavG10IcrVGSmPh6Qw5lwrg==" crossorigin=""></script>

	<style>
		html, body 
		{
			height: 100%;
			margin: 0;
		}

		#map 
		{
			<?php
				// eww hardcoded sizes.
			if (isMobile())
			{
				echo("width: 400px;height: 550px;");
			}
			else
			{
				echo("width: 1024px;height: 768px;");
			}
			?>
		}
	</style>
</head>
<body>
<table rows = 1 cols = 2>
	<tr>
		<td>
			<div id = 'map'><!-- here goes the map --></div>
		<td>
		<td>
			<div id = 'details' style='font-family:Calibri'><!-- here goes the lyrics --></div>
		</td>
</table>
<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.4.1/jquery.min.js"></script>
<script>

	var blueIcon = new L.Icon({
	iconUrl: 'https://cdn.rawgit.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
	shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
	iconSize: [25, 41],
	iconAnchor: [12, 41],
	popupAnchor: [1, -34],
	shadowSize: [41, 41]
	});

	var greenIcon = new L.Icon({
	iconUrl: 'https://cdn.rawgit.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
	shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
	iconSize: [25, 41],
	iconAnchor: [12, 41],
	popupAnchor: [1, -34],
	shadowSize: [41, 41]
	});

	var redIcon = new L.Icon({
	iconUrl: 'https://cdn.rawgit.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
	shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
	iconSize: [25, 41],
	iconAnchor: [12, 41],
	popupAnchor: [1, -34],
	shadowSize: [41, 41]
	});

	function details(songId,cityName)
	{
		$.ajax({
				url: "getDetails.php?idSearch=" + songId + "&citySearch=" + cityName,
				contentType: "application/x-www-form-urlencoded;charset=utf-8",
        		success: function(result)
				{
            		document.getElementById('details').innerHTML = result;
				}
				})
	}

	var map = L.map('map').setView([41.91, 12.39], 2);

	L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'}).addTo(map);



	<?php

		require_once('config.php');

		// Connect to DB to get songs.

		$queryCount = mysqli_query($dbc,"SELECT song_city,count(song_id) AS song_timesused FROM songslocations WHERE song_latitude <> -1 AND song_longitude <> -1 GROUP BY song_city");
		$querySongs = mysqli_query($dbc,"SELECT l.song_title,l.song_city,l.song_lyricsUrl,l.song_latitude,l.song_longitude,l.song_lyricsLine,l.song_id,a.artist_name FROM songslocations AS l INNER JOIN artists AS a ON a.artist_id = l.song_artist_id WHERE song_latitude <> -1 AND song_longitude <> -1");

		$counts = array();

		while ($cityCount = $queryCount->fetch_object()) 
		{
			$counts[strtolower($cityCount->song_city)] = $cityCount->song_timesused;
		}

		$songsPerCities = array();

		while ($songsLocations = $querySongs->fetch_object()) 
		{
			$artistProperCase = ucfirst($songsLocations->artist_name);
			$cityProperCase = ucfirst($songsLocations->song_city);

			if (!in_array($cityProperCase,array_keys($songsPerCities)))
			{
				$songsPerCities[$cityProperCase] = array();
			}

			array_push($songsPerCities[$cityProperCase],array('song_lyricsUrl' => $songsLocations->song_lyricsUrl,'artist' => $artistProperCase,'song_title' => $songsLocations->song_title,'song_id' => $songsLocations->song_id,'song_city' => $songsLocations->song_city,'song_latitude' => $songsLocations->song_latitude,'song_longitude' => $songsLocations->song_longitude));

		}

		for ($i = 0; $i < count($songsPerCities); $i++)
		{
			// For every city
			$cityProperCase = array_keys($songsPerCities)[$i];
			$textTMP = "<p style = \"text-align:center\"><b>{$cityProperCase}</b></p><br/>";
			for ($j = 0; $j < count($songsPerCities[array_keys($songsPerCities)[$i]]); $j++)
			{
				// And every song
				$song = $songsPerCities[array_keys($songsPerCities)[$i]][$j]; // WOW THIS LOOKS HORRIBLE
				$textTMP .= "<a href = javascript:details({$song['song_id']},\"{$cityProperCase}\")>{$song['artist']} - {$song['song_title']}<br/></a>";
			}

			// Remove special chars in the popup or the map goes boom.
			$textTMP = preg_replace('/[^A-Za-z0-9\-\s<br\/>\;\"\:\=\.\(\)àèéùì]\,/', '', $textTMP);
	
			switch (true) 
			 {
				case $counts[strtolower($cityProperCase)] >= 5:
					$pinColor = 'redIcon';
					break;
				case $counts[strtolower($cityProperCase)] >= 2:
					$pinColor = 'greenIcon';
					break;
				default:
					$pinColor = 'blueIcon';
					break;
	
			}

			// Convert everything to UTF8
			$textTMP = mb_convert_encoding($textTMP,'UTF-8','ISO-8859-1');
			echo("L.marker([{$song['song_latitude']}, {$song['song_longitude']}], {icon: $pinColor}).bindPopup('$textTMP').addTo(map);\n");	
		}


		function isMobile() 
		{
			return preg_match("/(android|avantgo|blackberry|bolt|boost|cricket|docomo|fone|hiptop|mini|mobi|palm|phone|pie|tablet|up\.browser|up\.link|webos|wos)/i", $_SERVER["HTTP_USER_AGENT"]);
		}

	?>

</script>

<?php

$queryDate = mysqli_query($dbc,"SELECT MAX(song_added) AS lastDate FROM songslocations ORDER BY song_added DESC LIMIT 1");

if ($date = $queryDate->fetch_object()) 
{
	echo("<br/><br/>LAST UPDATE: " . date("d/m/Y", strtotime($date->lastDate))); 
}

mysqli_close($dbc);
?>


</body>

</html>


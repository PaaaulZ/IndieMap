
<!DOCTYPE html>
<html>
<head>
	
	<title>IndieMap by PaaaulZ | https://github.com/IndieMap</title>

	<meta charset="utf-8" />
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	
	<link rel="shortcut icon" type="image/x-icon" href="docs/images/favicon.ico" />

    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.4.0/dist/leaflet.css" integrity="sha512-puBpdR0798OZvTTbP4A8Ix/l+A4dHDD0DGqYW6RQ+9jxkRFclaxxQb/SJAWZfWAkuyeQUytO7+7N4QKrDh+drA==" crossorigin=""/>
    <script src="https://unpkg.com/leaflet@1.4.0/dist/leaflet.js" integrity="sha512-QVftwZFqvtRNi0ZyCtsznlKSWOStnDORoefr1enyq5mVL4tmKB3S/EnC3rRJcxCPavG10IcrVGSmPh6Qw5lwrg==" crossorigin=""></script>


	<style>
		html, body {
			height: 100%;
			margin: 0;
		}
		#map {
			width: 1024px;
			height: 768px;
		}
	</style>

	
</head>
<body>

<div id='map'><button type = 'button' onclick = 'javascript:readTextFile("locations.txt");'></button></div>

<script>

	var map = L.map('map').setView([41.91, 12.39], 2);

	L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
		attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
	}).addTo(map);

	var LeafIcon = L.Icon.extend({
		options: {
			shadowUrl: 'leaf-shadow.png',
			iconSize:     [38, 95],
			shadowSize:   [50, 64],
			iconAnchor:   [22, 94],
			shadowAnchor: [4, 62],
			popupAnchor:  [-3, -76]
		}
	});

	var greenIcon = new LeafIcon({iconUrl: 'leaf-green.png'}),
		redIcon = new LeafIcon({iconUrl: 'leaf-red.png'}),
		orangeIcon = new LeafIcon({iconUrl: 'leaf-orange.png'});

	<?php

		// GROUP SONGS WITH THE SAME LOCATION
		
		$jsonFileContent = file_get_contents('found4map.json');
		$json = json_decode($jsonFileContent);

		$locationArray = array();

		foreach ($json as &$row)
		{
			// Group songs by city
			$cityTMP = $row[0]->city;

			if (!in_array($cityTMP,array_keys($locationArray)))
			{
				$locationArray[$cityTMP] = array();
			}
			array_push($locationArray[$cityTMP],$row);
		}

		// TODO: Change the text shown and beautify code and map.
		foreach ($locationArray as &$citySong)
		{
			$textTMP = "";
			foreach ($citySong as &$song)
			{
				$textTMP = $song[0]->city;
			}
			$textTMP = preg_replace('/[^A-Za-z0-9\-\s]/', '', $textTMP);
			echo("L.marker([{$song[0]->latitude}, {$song[0]->longitude}]).bindPopup('$textTMP').addTo(map);\n");
		}
	?>

	// L.marker([41.91, 12.39], {icon: greenIcon}).bindPopup("I am a green leaf.").addTo(map);

</script>



</body>
</html>

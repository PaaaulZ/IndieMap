
<!DOCTYPE html>
<html>
<head>
	
	<title>Custom Icons Tutorial - Leaflet</title>

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
		$locationsText = file_get_contents('locations.txt');
		$rows = explode("\n",$locationsText);
		for ($i = 0;$i < count($rows)-1; $i++)
		{
			$column = explode(";",$rows[$i]);
			$column[0] = preg_replace('/[^A-Za-z0-9\-\s]/', '', $column[0]);
			$column[1] = preg_replace('/[^A-Za-z0-9\-\s]/', '', $column[1]);
			$column[2] = preg_replace('/[^A-Za-z0-9\-\s]/', '', $column[2]);
			echo("L.marker([{$column[3]}, {$column[4]}]).bindPopup('{$column[0]} - {$column[1]} \[{$column[2]}\]').addTo(map);\n");
		}
	?>

	// L.marker([41.91, 12.39], {icon: greenIcon}).bindPopup("I am a green leaf.").addTo(map);

</script>



</body>
</html>

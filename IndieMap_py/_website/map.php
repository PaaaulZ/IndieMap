

<!DOCTYPE html>

<html>

<head>

	

	<title>IndieMap by PaaaulZ | https://github.com/PaaaulZ/IndieMap</title>



	<meta charset="utf-8" />

	<meta name="viewport" content="width=device-width, initial-scale=1.0">

	

	<!-- <link rel="shortcut icon" type="image/x-icon" href="docs/images/favicon.ico" /> -->



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



<div id='map'></div>



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





	var map = L.map('map').setView([41.91, 12.39], 2);



	L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {

		attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'

	}).addTo(map);



	<?php

		$jsonFileContent = file_get_contents('found4map.json');

		$json = json_decode($jsonFileContent);

		$locationArray = array();

		$countArray = array();

		foreach ($json as &$row)
		{


			// Group songs by city so we can show 1 point on the map and write the songs on the note

			$cityTMP = $row[0]->city;



			if (!in_array($cityTMP,array_keys($locationArray)))

			{

				// If it's the first time that I encounter this city create the array before pushing to avoid errors.

				$locationArray[$cityTMP] = array();

				$countArray[$cityTMP] = 0;

			}

			// Add this song to the location.

			array_push($locationArray[$cityTMP],$row);

			$countArray[$cityTMP]++;

		}



		// TODO: Change the text shown and beautify code and map.

		foreach ($locationArray as &$citySong)

		{

			$textTMP = "<p style = \"text-align:center\"><b>{$citySong[0][0]->city}</b></p><br/>";

			foreach ($citySong as &$song)

			{

				// Here we prepare the text that goes in the tooltip		

				$textTMP .= "<a href = '{$song[0]->lyricsUrl}'>{$song[0]->artist} - {$song[0]->title}<br/></a>";

			}

			// Remove special chars in the popup or the map goes boom.

			$textTMP = preg_replace('/[^A-Za-z0-9\-\s<br\/>\;\"\:\=\.àèéùì]/', '', $textTMP);



			switch (true) 

			{

				case $countArray[$citySong[0][0]->city] >= 5:

					echo("L.marker([{$song[0]->latitude}, {$song[0]->longitude}], {icon: redIcon}).bindPopup('$textTMP').addTo(map);\n");

					break;

				case $countArray[$citySong[0][0]->city] >= 2:

					echo("L.marker([{$song[0]->latitude}, {$song[0]->longitude}], {icon: greenIcon}).bindPopup('$textTMP').addTo(map);\n");

					break;

				default:

					echo("L.marker([{$song[0]->latitude}, {$song[0]->longitude}], {icon: blueIcon}).bindPopup('$textTMP').addTo(map);\n");	

					break;

			}

		}



		function isMobile() 

		{

			return preg_match("/(android|avantgo|blackberry|bolt|boost|cricket|docomo|fone|hiptop|mini|mobi|palm|phone|pie|tablet|up\.browser|up\.link|webos|wos)/i", $_SERVER["HTTP_USER_AGENT"]);

		}

	?>

</script>

<?php echo "LAST UPDATE: " . date("d/m/Y H:i:s", filemtime('found4map.json')); ?>

</body>

</html>


<?php

require_once('config.php');
header('Access-Control-Allow-Origin: *');



$idSearch = intval($_GET['idSearch']);

$citySearch = mysqli_real_escape_string($dbc,$_GET['citySearch']);



$queryLine = mysqli_query($dbc,"SELECT song_lyricsLine,song_lyricsUrl,song_city FROM songslocations WHERE song_id = $idSearch AND song_city = '$citySearch'");



if ($line = $queryLine->fetch_object()) 

{

    $source_charset = 'UTF-8';

    $target_charset = 'ISO-8859-1';

    // I have to do all of this or else special characters won't work. Don't know why, please it's late at night.

    $finalString = mb_convert_encoding($line->song_lyricsLine,'UTF-8','ISO-8859-1');

    // Higlight the city in the lyrics, just to add some color and clarity.

    $finalString = str_replace(strtolower($line->song_city),"<b><font color = 'red'>" . ucfirst($line->song_city) . "</font></b>",$finalString);
    $finalString .= "<br/><br/><a href = 'javascript:window.open(\"{$line->song_lyricsUrl}\",\"_blank\"); void(0);'>Full lyrics on Genius.com</a>";
    $finalString = ucfirst($finalString);

    die($finalString);

}

?>
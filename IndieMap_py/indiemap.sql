SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `indiemap`
--

-- --------------------------------------------------------

--
-- Struttura della tabella `alreadydone`
--

CREATE TABLE `alreadydone` (
  `song_id` int(11) NOT NULL COMMENT 'GENIUS.COM song ID'
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Struttura della tabella `artists`
--

CREATE TABLE `artists` (
  `artist_id` int(20) NOT NULL,
  `artist_name` varchar(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Struttura della tabella `lastfetch`
--

CREATE TABLE `lastfetch` (
  `song_id` int(11) NOT NULL,
  `song_artist_id` int(11) NOT NULL,
  `song_name` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Struttura della tabella `songslocations`
--

CREATE TABLE `songslocations` (
  `song_id` int(11) NOT NULL,
  `song_artist_id` int(11) NOT NULL,
  `song_city` varchar(60) NOT NULL,
  `song_latitude` float NOT NULL,
  `song_longitude` float NOT NULL,
  `song_lyricsUrl` varchar(300) NOT NULL,
  `song_lyricsLine` text NOT NULL,
  `song_added` date NOT NULL COMMENT 'Used to mark NEW songs and show last update',
  `song_title` varchar(60) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
--
-- Indici per le tabelle `alreadydone`
--
ALTER TABLE `alreadydone`
  ADD PRIMARY KEY (`song_id`);

--
-- Indici per le tabelle `artists`
--
ALTER TABLE `artists`
  ADD PRIMARY KEY (`artist_id`,`artist_name`);

--
-- Indici per le tabelle `lastfetch`
--
ALTER TABLE `lastfetch`
  ADD PRIMARY KEY (`song_id`);

--
-- Indici per le tabelle `songslocations`
--
ALTER TABLE `songslocations`
  ADD PRIMARY KEY (`song_id`,`song_artist_id`,`song_city`);

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;

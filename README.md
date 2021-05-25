# kpub: Publication database

***A database of scientific publications related to a mission.***

`kpub` is a generic tool that enables an institution to keep track of it's scientific publications in an easy way. It leverages SQLite and the [ADS API](https://github.com/adsabs/adsabs-dev-api) to create and curate a database that contains the metadata of mission-related articles.

This tool is made possible thanks to the efforts of Geert Barentsen who wrote the original version of [kpub](https://github.com/KeplerGO/kpub) for Kepler/K2.  The major changes here are:

- Code is now config file driven so it can be used by any mission or facility.
- Added optional tracking of instrument assocations and associated new plots.
- Added optional tracking of archive references and associated new plots.
- Added affiliations mapping and plotting.
- Added automated PDF download, view, and search for highlight snippets.
- Removed reliance on 'ads' third-party module (due to some limitations).

## Example use

Search ADS by pubdate month or year for new articles and try to add them interactively:
```
kpub-update 2015-07
kpub-update 2015
```

Add a new article to the database interactively using its bibcode:
```
kpub-add 2015arXiv150204715F
```

Remove an article using its bibcode:
```
kpub-delete 2015ApJ...800...46B
```

For example output, see the `data/output/` sub-directory in this repository.

## Installation

First, get the source code:
```
git clone https://github.com/KeckObservatory/kpub.git
```

Next, edit your config.live.yaml file.  Read the config file and edit sections as needed.  At a minimum, you will need to add the ADS_API_KEY value.  There are two example config files for Keck and Kepler as well.:
```
cd kpub/kpub/config
cp config.yaml config.live.yaml
```

Finally, run installation script:
```
python setup.py install
```

Note that the `kpub` tools will use `~/.kpub.db` as the default database file. This repository contains a recent version of the database file (`data/kpub.db`), which you may want to link to the default file as follows:
```
ln -s /path/to/git/repo/data/kpub.db ~/.kpub.db
```

The `kpub-add`and `kpub-update` tools that come with this package require an api key from NASA ADS labs to retrieve publication meta-data.

## Usage

`kpub` adds a number of tools to the command line (described below).

There is a `Makefile` which makes your life easy for updating the database. 
Simply type:
* `make update` to search for new publications with pubdate of current month;
* `make push` to push the updated database to the git repo;
* `make refresh` to export and import all publications, this is slow and necessary only if you want to remove duplicates and fetch fresh citation statistics.

## Command-line tools

After installation, this package adds the following command-line tools to your path:
* `kpub` prints the list of publications in markdown format;
* `kpub-update` adds new publications by searching ADS (interactive);
* `kpub-add` adds a publication using its ADS bibcode;
* `kpub-delete` deletes a publication using its ADS bibcode;
* `kpub-import` imports bibcodes from a csv file;
* `kpub-export` exports bibcodes to a csv file;
* `kpub-plot` creates a visualization of the database;
* `kpub-spreadsheet` exports the publications to an Excel spreadsheet.

Listed below are the usage instructions for each command:

*kpub*
```
$ kpub --help
usage: kpub [-h] [-f dbfile] [-m] [--science science] [--mission mission]

View the publication list in markdown format.

optional arguments:
  -h, --help          show this help message and exit
  -f dbfile           Location of the publication db. Defaults to ~/.kpub.db.
  -m, --month         Group the papers by month rather than year.
  --science           Only show a particluar science.  Defaults to all.
  --mission           Only show a particluar mission.  Defaults to all.
```

*kpub-update*
```
$ kpub-update --help
usage: kpub-update [-h] [-f dbfile] [month]

Interactively query ADS for new publications.

positional arguments:
  month       Month to query, e.g. 2015-06.

optional arguments:
  -h, --help  show this help message and exit
  -f dbfile   Location of the publication db. Defaults to ~/.kpub.db.
```

*kpub-add*
```
$ kpub-add --help
usage: kpub-add [-h] [-f dbfile] bibcode [bibcode ...]

Add a paper to the publication list.

positional arguments:
  bibcode     ADS bibcode that identifies the publication.

optional arguments:
  -h, --help  show this help message and exit
  -f dbfile   Location of the publication db. Defaults to ~/.kpub.db.
```

*kpub-delete*
```
$ kpub-delete --help
usage: kpub-delete [-h] [-f dbfile] bibcode [bibcode ...]

Deletes a paper from the publication list.

positional arguments:
  bibcode     ADS bibcode that identifies the publication.

optional arguments:
  -h, --help  show this help message and exit
  -f dbfile   Location of the publication db. Defaults to ~/.kpub.db.
```

*kpub-import*
```
$ kpub-import --help 
usage: kpub-import [-h] [-f dbfile] csvfile

Batch-import papers into the publication db from a CSV file. The
CSV file must have five columns (bibcode,mission,science,instruments,archive) 
separated by commas. For example: '2004ApJ...610.1199G,kepler,astrophysics'.

positional arguments:
  csvfile     Filename of the csv file to ingest.

optional arguments:
  -h, --help  show this help message and exit
  -f dbfile   Location of thepublication db. Defaults to ~/.kpub.db.
```

*kpub-export*
```
$ kpub-export --help
usage: kpub-export [-h] [-f dbfile]

Export the publication db in CSV format.

optional arguments:
  -h, --help  show this help message and exit
  -f dbfile   Location of the publication db. Defaults to ~/.kpub.db.
```

*kpub-spreadsheet*
```
$ kpub-spreadsheet --help
usage: kpub-spreadsheet [-h] [-f dbfile]

Export the publication db in XLS format.

optional arguments:
  -h, --help  show this help message and exit
  -f dbfile   Location of the publication db. Defaults to ~/.kpub.db.
```

## Authors
Original Kepler/K2-specific version created by Geert Barentsen (geert.barentsen at nasa.gov)
on behalf of the Kepler/K2 Guest Observer Office.

This generalized configurable version created by Josh Riley (jriley at keck.hawaii.edu).


## Acknowledgements
This tool is made possible thanks to the efforts of Geert Barentsen who wrote the original version of [kpub](https://github.com/KeplerGO/kpub) for Kepler/K2.  Thanks also to NASA ADS for providing a web API to their database.


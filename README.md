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
- Replaced installation and Makefile with simple run script (due to some limitations).


## Installation and Configuration

First, download the source code to a directory of your choice:
```
git clone https://github.com/KeckObservatory/kpub.git
```

Next, edit the `config.live.yaml` file.  Read the config file and edit sections as needed.  At a minimum, you will need to add the `ADS_API_KEY` value.  There are two example config files pre-configuraed for Keck and Kepler as well.
```
cd kpub/src/config
cp config.yaml config.live.yaml
```

Finally, add `kpub` start script to path (optional):

export PATH=/home/observer/kpub:$PATH

Note that the `kpub` tools will use `~/.kpub.db` as the default database file. This repository contains a recent version of the database file (`data/kpub.db`), which you may want to link to the default file as follows:
```
ln -s /path/to/git/repo/data/kpub.db ~/.kpub.db
```


## Usage
Add `--help` to any command below to get full usage instructions

* `kpub update` adds new publications by searching ADS (interactive);
* `kpub add` adds a publication using its ADS bibcode;
* `kpub delete` deletes a publication using its ADS bibcode;
* `kpub import` imports bibcodes from a csv file;
* `kpub export` exports bibcodes to a csv file;
* `kpub plot` creates a visualization of the database;
* `kpub markdown` prints the list of publications in markdown format;
* `kpub spreadsheet` exports the publications to an Excel spreadsheet
* `kpub update` to search for new publications with pubdate of current month;
* `kpub push` to push the updated database to the git repo;
* `kpub refresh` to export and import all publications (this is slow and necessary only if you want to remove duplicates and fetch fresh citation statistics)


## Example use

Search ADS by pubdate month or year for new articles and try to add them interactively:
```
kpub update 2015-07
kpub update 2015
```

Add a new article to the database interactively using its bibcode:
```
kpub add 2015arXiv150204715F
```

Remove an article using its bibcode:
```
kpub delete 2015ApJ...800...46B
```

For example output, see the `data/output/` sub-directory in this repository.


## Authors
This new configurable version created by Josh Riley (jriley at keck.hawaii.edu).

Original Kepler/K2-specific version created by Geert Barentsen (geert.barentsen at nasa.gov).



## Acknowledgements
This tool is made possible thanks to the efforts of Geert Barentsen who wrote the original version of [kpub](https://github.com/KeplerGO/kpub) for Kepler/K2.  Thanks also to NASA ADS for providing a web API to their database.


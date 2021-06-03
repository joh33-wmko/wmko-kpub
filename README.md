# kpub: Publication database

***A database of scientific publications related to a mission.***

`kpub` is a generic tool that enables an institution to keep track of it's scientific publications in an easy way. It leverages SQLite and the [ADS API](https://github.com/adsabs/adsabs-dev-api) to create and curate a database that contains the metadata of mission-related articles.

This tool is made possible thanks to the efforts of Geert Barentsen who wrote the original version of [kpub](https://github.com/KeplerGO/kpub) for Kepler/K2.  The major changes here are:

- Code is now config-file driven so it can be used by any facility or institution.
- Added optional tracking of instrument assocations and associated new plots.
- Added optional tracking of archive references and associated new plots.
- Added affiliations mapping and plotting.
- Added automated PDF download, view, and search for highlight snippets.
- Removed reliance on 'andycasey/ads' third-party module (due to some limitations).
- Replaced installation script and Makefile with run script (due to some limitations).


## Installation and Configuration

1) Download the source code (assuming $HOME for examples below):
```
cd $HOME
git clone https://github.com/KeckObservatory/kpub.git
```

2) Create an account at https://ui.adsabs.harvard.edu/, generate an ADS API key (https://ui.adsabs.harvard.edu/user/settings/token) and copy it for use in step 3 below.

3) Edit the `config.live.yaml` file.  Read the config file and edit sections as needed.  At a minimum, you will need to add the `ADS_API_KEY` value.  There are two example config files pre-configured for Keck and Kepler as well.
```
cd $HOME/kpub/src/config
cp config.keck.yaml config.live.yaml
```

4) Install dependencies:

Option 1: Create a conda environment using the provided environment.yaml file:
```
cd $HOME/kpub
conda env create -f environment.yaml
````

Option 2: Or, install them manually:
```
pip install textract pyyaml requests jinja2 matplotlib bokeh
```

5) (optional) Add kpub install directory to PATH so you can run `kpub` from anywhere:
```
export PATH=/home/observer/kpub:$PATH
```

6) (optional) `kpub` uses `data/kpub.db` as the database file. This repository contains the most recent version of that file.  If you want to start completely over, delete this file before starting kpub.


## Usage
Add `--help` to any command below to get full usage instructions

* `kpub update` adds new publications by searching ADS (interactive);
* `kpub push` to push the updated database and other data files to the git repo;
* `kpub add` adds a publication using its ADS bibcode;
* `kpub delete` deletes a publication using its ADS bibcode;
* `kpub import` imports bibcodes from a csv file;
* `kpub export` exports bibcodes to a csv file and saves to data/ dir
* `kpub plot` creates a visualization of the database and saves to data/plots/ dir here;
* `kpub stats` creates publications stats in markdown format and saves to data/output dir here;
* `kpub spreadsheet` exports the publications to an Excel spreadsheet
* `kpub refresh` to export and re-import all publications (this is slow and necessary only if you want to remove duplicates and fetch fresh citation statistics)


## Example use

Search ADS by pubdate month or year for new articles and add them interactively (and push to repo):
```
kpub update 2015-07
kpub update 2015
kpub push
```

Update plots and stats files (and push to repo):
```
kpub plot
kpub stats
kpub push
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


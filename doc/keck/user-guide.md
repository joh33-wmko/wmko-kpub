# KPUB User Guide
Date: 2021-May
Author: Josh Riley


## Background
Keck collects records of publications that use Keck instrument data.  This has traditionally been completed by Peggi Kamisato in a mostly manual search-and-find manner.  Peggi is retiring in June 2021.  The software group was tasked to automate this process as much as possible, store the records in a database, and provide on-demand reporting and graphing utilities on the data.

The solution was to modify Kepler's "kpub" python script to work as a general purpose, config-driven script for any facility or institution to use to find and store publications.  Kepler-specific code was refactored and specific variables were moved to a config file.  Some new features were added as well.  

It is important to note that although kpub automates many of the steps involved, it does not replace having a person look at the context of each article to confirm it is Keck-related.  


## Installation
The code can be installed by following the instructions at https://github.com/KeckObservatory/kpub
There is a Keck-specific config file checked in at src/config.config.keck.yaml that should be used during the installation step when creating your config.live.yaml file.  The only change to make is to add your ADS API key.


## Updating the database
To update a particular year or month:
    kpub update [YYYY]
    kpub update [YYYY-MM]

To update the repo/database after an update:
    kpub push


## Plotting and Stats
Plots files are written to png/pdf/html files in kpub/data/plots/
    kpub plot

Stats are written to markdown files in kpub/data/output/
    kpub stats


## Citation Refresh
Once a year or before doing an annual report, you can run a full requery of all records to refresh their metadata, such as citations.  This can take a while, up to an hour or more.  After running the refresh, you can then rerun plotting and stats:
    kpub refresh
    kpub stats
    kpub plot


## Add and Delete
To add or delete a single record by bibcode:
    kpub add [BIBCODE] 
    kpub delete [BIBCODE] 

NOTE: The ADS highlighting doesn't work at first when adding by bibcode, so use [m] to view more context to see the full highlighting.

Important notes:
- Only one person should update the database at a time.  The code uses the github repo to store the database files. So, multiple users cannot update the data at once or they will clobber each other's work.  And as such, a 'git pull' should be performed anytime data updates are performed.
- When doing a 'kpub update', the code will first query for "keck" in the acknowledgement or abstract (minus some exclusion terms).  This first group should hopefully mostly be good matches.  A second query is done of "Keck Observatory" and "Keck/[instrument]" in the full text.  Searching only for "keck" in the full text produces too many false matches.  This second group will still have many false matches, but depending on how much time and resources you have to put towards searching, this could produce a few more papers.  This is inline with the manual search technique done prior.
- The code attempts to download the PDF to identify context snippets and other things.  This is successful most of the time. If it cannot, it will use a series of inefficient ADS queries to try and get this info using the ADS "highlights" query option, which purposefully limits the number of context results.
- Context matching is brainless so when confirming the instrument list, the code may pick up references to other instruments, AO, etc and so the instrument list needs to be confirmed with context if possible.
- KOA references are detected as well but this is fairly accurate so results are not displayed for confirmation. 
- Since retrieving the PDF can take up to a minute, it is not retrieved by default right away; instead relying on ADS's limited highlights query feature.  If desired, use the 'm' option to download the PDF and show more context snippets.  Use the 'p' option to open the PDF in your browser.
- We are unable to exclude "Keck Foundation" from the query b/c this appears in legitimate Keck-related papers too, so you may see several matches with 'keck' in acknowledgements that have nothing to do with Keck Observatory.  They are easy to identify and reject.
- We don't include -bibgroup:keck so we can ensure all are in our database.  Those that are skipped are printed out, but you have to scroll up to see it.
- When doing a kpub update, you can use YYYY-MM to target a particular month or just YYYY to do the whole year.  Some articles don't show up until many months after their official publication YYYY-MM.  One strategy could be to run this for the whole year YYYY and run it every month throughout the year to pick up late-comers.  Or do it by current month but always run the previous ~4 months.  In other words, if you tried to publish a 2020 report on Jan 2021, there will still be some small percentage of articles still being found through the first half of 2021 or longer.


## KPUB modifications
Here is a summary of the main modifications made to the original Kepler-specific kpub:

- Code is now config-file driven so it can be used by any facility or institution.
- Added automated PDF download, view, and search for highlight snippets.
- Added optional tracking of instrument associations and added related plots.
- Added optional tracking of archive references.
- Added affiliations mapping and plotting.
- Removed reliance on 'andycasey/ads' third-party module (due to some limitations).
- Replaced installation script and Makefile with run script (due to some limitations).


## Reference
- Peggi's shared folder:
https://keckhawaii-my.sharepoint.com/:f:/g/personal/kamisato_keck_hawaii_edu/EgactX9ejEVMtvpoGXEFBQQB5jJJyx5oF5zWxyPoh_SS-w?e=5%3aAWoDuH&at=9
- ADS API:
https://github.com/adsabs/adsabs-dev-api
- Kepler publications retrieval tool: 
https://github.com/KeplerGO/kpub


## Tasks
A list of tasks to complete the kpub port and option or low-priority tasks that can be worked on

Must do: 
- [done] Move kepler specific variables to config file based.
- [done] Add PDF d/l, parse and search (with alt ADS requery fallback method)
- [done] Added ADS "highlight" text snippets to review text.
- [done] Write script to load and validate existing article data from CVS files and import to new database. 
- [done] Do a full proper import of all Keck article legacy data, including instrument associations.
- [done] Add instrument search, highlight and user prompt for inclusion to db.
- [done] Remove reliance on 'ads' third-party module?
- [done] Create affiliations mapping config for search criteria. 
- [done] Code algorithm for determining affiliation category. See plot.py for test code.
- [done] Auto search for KOA in full text and insert 1 or 0 in new 'archive' DB column.
- [done] Option to open local pdf in browser.
- [done] Add plotting of instruments per year
- [done] Add report/graph of pubs by affiliation type (1st auth, <= 3rd auth) 
- [done] Update README and other code docs with kepler/k2 mentions
- [done] Replace installation script and makefile with simple run script
- Try mysql version with install on keck server
- "out of sort memory" for plots and stats.  Due to JSON column
- Create keck-specific user guide (confluence?)
- Post ADS bibcodes files to www2.
- See www:/home/jriley/test/kpub-copy.py
- Need to make kcron owner of 2 files
- Move to keckobservatory github 
- Move plotting params to config, such as 'start year' (some are still hard-coded to 2005)
- Run kpub for all of 2020 up to present 
- Deal with data anomalies below
- pdftotext is faster but not as good, pdfminder is slower sometimes but i think works better
- Add plotting of KOA reference
- See if 'scripts' dir works with recent changes?
- "make refresh" with optional year param?
- Fix issue with kpub add not highlighting by default?
- Create a webform to replace appeals email where the only input to form is bibcodes(reads our www file copy)? Send PIs a link/URL to search ADS by their name? Send link to https://www2.keck.hawaii.edu/library/adskeck.txt?
- How will we query, insert and report on thesis papers?  doctype='phdthesis', property contains 'NONARTICLE'
- Change plots to all use bokeh or all matplotlib


Low-priority:
- Add full spelling of instruments as optional search params.  So 'KCWI' counts will search for 'KCWI' and "KECK Cosmic Web Imager".  Use OR in query. Reprocess records with empty instruments?
- Add ability to review and/or export 'unrelated' entries.
- Context: Make context snippet length a config item? Provide full sentence context?
- Might want to show KOA results to confirm.  There was a case 2020MNRAS.499.3775S that said "these data are available thru KOA" which does not mean they used koa.
- To speed things up, have code retrieve the pdf of the next article? 
- Create a GUI interface (flask or pyqt)

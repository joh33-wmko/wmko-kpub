# KPUB User Guide
Author: Josh Riley


## Background
Keck collects records of publications that use Keck instrument data.  This has traditionally been completed by Peggi Kamisato in a mostly manual search-and-find manner.  Peggi is retiring in June 2021.  The software group was tasked to automate this process as much as possible, store the records in a database, and provide on-demand reporting and graphing utilities on the data.

The solution was to modify Kepler's "kpub" python script to work as a general purpose, config-driven script for any facility or institution to use to find and store publications.  Kepler-specific code was refactored and specific variables were moved to a config file.  Some new features were added as well.  



## Installation
The code can be installed by following the instructions at https://github.com/KeckObservatory/kpub
There is a Keck-specific config file checked in at src/config.config.keck.yaml that should be used during the installation step when creating your config.live.yaml file.  The only change to make is to add your ADS API key.


## Updating the database
There are two important things to know about updating the kpub database:
- kpub does not replace having a person look at the article context to confirm it is Keck-related.  
- kpub uses the github repo as a database, so only one person should update the database at a time.

To update a particular year or month:
    git pull
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


## Important notes:
- Only one person should update the database at a time.  The code uses the github repo to store the database files. So, multiple users cannot update the data at once or they will clobber each other's work.  And as such, a 'git pull' should first be performed anytime data updates are performed.
- When doing a 'kpub update', the code will first query for "keck" in the acknowledgement or abstract (minus some exclusion terms).  This first group should hopefully mostly be good matches.  A second query is done of "Keck Observatory" and "Keck/[instrument]" in the full text.  Searching only for "keck" in the full text produces too many false matches.  This second group will still have many false matches, but depending on how much time and resources you have to put towards searching, this could produce a few more papers.  This is inline with the manual search technique done prior.
- The code attempts to download the PDF to identify context snippets and other things.  This is successful most of the time. If it cannot, it will use a series of inefficient ADS queries to try and get this info using the ADS "highlights" query option, which purposefully limits the number of context results.
- Since retrieving the PDF can take up to a minute, it is not retrieved by default right away; instead relying on ADS's limited highlights query feature.  If desired, use the 'm' option to download the PDF and show more context snippets.  Use the 'p' option to open the PDF in your browser.
- Context matching is brainless, so when confirming the instrument list, the code may pick up references to other instruments, AO, etc and so the instrument list needs to be confirmed with context if possible.
- KOA references are detected as well but this is fairly accurate so results are not displayed for confirmation. 
- We are unable to exclude "Keck Foundation" from the query b/c this appears in legitimate Keck-related papers too, so you may see several matches with 'keck' in acknowledgements that have nothing to do with Keck Observatory.  They are easy to identify and reject.
- We don't include -bibgroup:keck so we can ensure all are in our database.  Those that are skipped are printed out, but you have to scroll up to see it.
- When doing a kpub update, you can use YYYY-MM to target a particular month or just YYYY to do the whole year.  Some articles don't show up until many months after their official publication YYYY-MM.  One strategy could be to always run kpub for the whole year YYYY and run it every month throughout the year to pick up late-comers.  Or do it by current month but always run the previous ~4 months.  In other words, if you tried to publish a 2020 report on Jan 2021, there will still be some small percentage of articles still being found through the first half of 2021 or longer.



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


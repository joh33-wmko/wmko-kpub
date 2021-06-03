
Must do: 
- [DONE] Move kepler specific variables to config file based.
- [DONE] Add PDF d/l, parse and search (with alt ADS requery fallback method)
- [DONE] Added ADS "highlight" text snippets to review text.
- [DONE] Write script to load and validate existing article data from CVS files and import to new database. 
- [DONE] Do a full proper import of all Keck article legacy data, including instrument associations.
- [DONE] Add instrument search, highlight and user prompt for inclusion to db.
- [DONE] Remove reliance on 'ads' third-party module?
- [DONE] Create affiliations mapping config for search criteria. 
- [DONE] Code algorithm for determining affiliation category. See plot.py for test code.
- [DONE] Auto search for KOA in full text and insert 1 or 0 in new 'archive' DB column.
- [DONE] Option to open local pdf in browser.
- [DONE] Add plotting of instruments per year
- [DONE] Add report/graph of pubs by affiliation type (1st auth, <= 3rd auth) 
- [DONE] Update README and other code docs with kepler/k2 mentions
- [DONE] Replace installation script and makefile with simple run script
- [DONE] Create keck-specific user guide (confluence?)
- Run kpub for all of 2020 and up to present.
- Turn on www cron that copies bibcode files to www2.
- Move plotting params to config, such as 'start year' (some are still hard-coded to 2005)
- Add plotting of KOA reference
- Create a webform to replace appeals email where the only input to form is bibcodes(reads our www file copy)? Send PIs a link/URL to search ADS by their name? Send link to https://www2.keck.hawaii.edu/library/adskeck.txt?
- Fix issue with 'kpub add' not highlighting by default?
- Change plots to all use bokeh or all matplotlib
- See if 'scripts' dir works with recent changes?


Low-priority:
- How will we query, insert and report on thesis papers?  doctype='phdthesis', property contains 'NONARTICLE'
- Email ADS about increasing highlight limits?
- pdftotext is faster but not as good, pdfminer is slower sometimes but i think works better
- Try mysql version with install on keck server (see mysql branch; mostly done but did not have time to finish)
- Add full spelling of instruments as optional search params.  So 'KCWI' counts will search for 'KCWI' and "KECK Cosmic Web Imager".  Use OR in query. Reprocess records with empty instruments?
- Add ability to review and/or export 'unrelated' entries.
- Context: Make context snippet length a config item? Provide full sentence context?
- Might want to show KOA results to confirm.  There was a case 2020MNRAS.499.3775S that said "these data are available thru KOA" which does not mean they used koa.
- To speed things up, have code retrieve the pdf of the next article? 
- Create a GUI interface (flask or pyqt)
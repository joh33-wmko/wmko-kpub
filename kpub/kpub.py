"""
Build and maintain a database of publications.
"""

from __future__ import print_function, division, unicode_literals

# Standard library
import os
import re
import sys
import json
import datetime
import argparse
import collections
import sqlite3 as sql
import numpy as np
import yaml
import requests
import readline
import webbrowser
from pprint import pprint

try:    
    import textract
except: 
    textract = None

# External dependencies
import jinja2
from six.moves import input  # needed to support Python 2
from astropy import log
from astropy.utils.console import ProgressBar

#todo: temp hack until we figure out packaging stuff
#from . import plot
import plot
PACKAGEDIR = os.path.abspath(os.path.dirname(__file__))

#ADS API URL
ADS_API = 'https://api.adsabs.harvard.edu/v1/search/query?'

# Where is the default location of the SQLite database?
DEFAULT_DB = os.path.expanduser("~/.kpub.db")

# Which metadata fields do we want to retrieve from the ADS API?
# (basically everything apart from 'body' to reduce data volume)
FIELDS = ['date', 'pub', 'id', 'volume', 'links_data', 'citation', 'doi',
          'eid', 'keyword_schema', 'citation_count', 'data', 'data_facet',
          'year', 'identifier', 'keyword_norm', 'reference', 'abstract', 'recid',
          'alternate_bibcode', 'arxiv_class', 'bibcode', 'first_author_norm',
          'pubdate', 'reader', 'doctype', 'doctype_facet_hier', 'title', 'pub_raw', 'property',
          'author', 'email', 'orcid', 'keyword', 'author_norm',
          'cite_read_boost', 'database', 'classic_factor', 'ack', 'page',
          'first_author', 'reader', 'read_count', 'indexstamp', 'issue', 'keyword_facet',
          'aff', 'facility', 'simbid']

#Defines colors for highlighting words in the terminal.
HIGHLIGHTS = {
    "RED"    : "\033[4;31m",
    "GREEN"  : "\033[4;32m",
    "YELLOW" : "\033[4;33m",
    "BLUE"   : "\033[4;34m",
    "PURPLE" : "\033[4;35m",
    "CYAN"   : "\033[4;36m",
    "END"    : '\033[0m',
}


class PublicationDB(object):
    """Class wrapping the SQLite database containing the publications.

    Parameters
    ----------
    filename : str
        Path to the SQLite database file.
    """
    def __init__(self, filename=DEFAULT_DB, config=None):
        self.filename = filename
        self.config = config
        self.con = sql.connect(filename)
        pubs_table_exists = self.con.execute(
                                """
                                   SELECT COUNT(*) FROM sqlite_master
                                   WHERE type='table' AND name='pubs';
                                """).fetchone()[0]
        if not pubs_table_exists:
            self.create_table()    

    def create_table(self):
        self.con.execute("""CREATE TABLE pubs(
                                id UNIQUE,
                                bibcode UNIQUE,
                                year,
                                month,
                                date,
                                mission,
                                science,
                                instruments,
                                archive,
                                metrics)""")

    def add(self, article, mission="", science="", instruments="", archive=""):
        """Adds a single article object to the database.

        Parameters:
            article (json): Article json object returned from ADS API
            mission (str)
            science (str)
            instruments (str): Pipe-delimited list of instruments
            archive (str): 0 or 1 indicating if archiving reference was found
        """
        log.debug('Ingesting {}'.format(article['bibcode']))

        # Store the extra metadata in the json string
        month = article['pubdate'][0:7]
        article['mission'] = mission
        article['science'] = science
        article['instruments'] = instruments
        article['archive'] = archive

        #insert to db
        try:
            cur = self.con.execute("INSERT INTO pubs "
                "(id, bibcode, year, month, date, mission, science, instruments, archive, metrics) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [article['id'], article['bibcode'], article['year'], month, article['pubdate'],
                mission, science, instruments, archive, json.dumps(article)])
            log.info('Inserted {} row(s).'.format(cur.rowcount))
            self.con.commit()
        except sql.IntegrityError:
            log.warning('{} was already ingested.'.format(article['bibcode']))

    def add_interactively(self, article, statusmsg="", highlights=None):
        """Adds an article by prompting the user for the classification.

        Parameters:
            article (json): Article json object returned from ADS API
        """        

        # Do not show an article that is already in the database
        if self.article_exists(article):
            log.info("{} is already in the database "
                     "-- skipping.".format(article['bibcode']))
            return

        # Print paper information to stdout
        print(chr(27) + "[2J")  # Clear screen
        print(statusmsg)
        display_abstract(article, self.config['colors'], highlights)

        # Prompt the user to classify the paper by mission
        #NOTE: 'unrelated' is how things are permenantly marked to skip in DB.
        valmap = {'0': 'unrelated'}
        missions = self.config.get('missions', [])
        valmap = add_prompt_valmaps(valmap, missions)
        mission = ''
        while True:
            print("\n([p] PDF view  [m] More context)")
            mission = prompt_grouping(valmap, 'Mission')
            if mission.lower() == 'm':
                self.find_all_snippets(article['bibcode'])
            elif mission.lower() == 'p':
                self.open_pdf(article['bibcode'])
            else:
                break

        #Hitting return or any unrecognized key results in skip
        mission = valmap.get(mission, '')
        if not mission:
            return

        # Prompt the user to classify the paper by science
        science = ''
        sciences = self.config.get('sciences', [])
        if mission != 'unrelated' and sciences:
            valmap = {}
            valmap = add_prompt_valmaps(valmap, sciences)
            science = prompt_grouping(valmap, 'Science')

        # Promput user to confirm instruments?
        instruments = ''
        if mission != 'unrelated':
            instruments = self.prompt_instruments(article['bibcode'])

        # Get archive ack
        archive = ''
        if mission != 'unrelated':
            archive = self.get_archive_acknowledgement(article['bibcode'])

        #add it
        self.add(article, mission=mission, science=science, instruments=instruments,
                 archive=archive)


    def find_all_snippets(self, bibcode):

        colors = self.config.get('colors')
        missions = self.config.get('missions', [])
        instruments = self.config.get('instruments', [])
        ads_api_key = self.config.get('ADS_API_KEY')

        #if not config for this, then return empty array
        words = []
        words += missions
        words += instruments
        if not words:
            return []

        #try two methods for finding matches
        try:
            counts = get_word_match_counts_by_pdf(bibcode, words, ads_api_key)
        except Exception as e:
            print("WARN: Could not parse PDF file.  Using alternate ADS query method...")
            counts = get_word_match_counts_by_query(bibcode, words)

        #print snippets
        print("\nSNIPPETS FOUND:")
        for instr, count in counts.items():
            for snippet in count['snippets']:
                snippet = highlight_text(snippet, colors)
                print(f'"... {snippet}"')

        return counts


    def get_archive_acknowledgement(self, bibcode):
        '''Search for instances of archive strings in full article.'''

        #if not config for this, then return empty array
        archive = self.config.get('archive')
        if not archive:
            return ''

        #try two methods for finding matches
        try:
            ads_api_key = self.config.get('ADS_API_KEY')
            counts = get_word_match_counts_by_pdf(bibcode, archive, ads_api_key)
        except Exception as e:
            print("WARN: Could not parse PDF file.  Using alternate ADS query method...")
            counts = get_word_match_counts_by_query(bibcode, archive)

        #print snippets
        # print("ARCHIVE SNIPPETS FOUND:")
        # for key, count in counts.items():
        #     for snippet in count['snippets']:
        #         snippet = highlight_text(snippet, self.config['colors'])
        #         print(f'"... {snippet}"')
        if len(counts) > 0:
            print("ARCHIVE ACKNOWLDGEMENT FOUND")

        #return "0" or "1"
        #NOTE: Using str values b/c original code used blobs for all DB cols.
        val = "1" if len(counts) > 0 else "0"
        return val


    def prompt_instruments(self, bibcode):
        '''Search for instances of instrument strings in full article.'''

        #if not config for this, then return empty array
        instruments = self.config.get('instruments')
        if not instruments:
            return ''

        #try two methods for finding matches
        try:
            ads_api_key = self.config.get('ADS_API_KEY')
            counts = get_word_match_counts_by_pdf(bibcode, instruments, ads_api_key)
        except Exception as e:
            print("WARN: Could not parse PDF file.  Using alternate ADS query method...")
            counts = get_word_match_counts_by_query(bibcode, instruments)

        #print snippets
        print("\nINSTRUMENT SNIPPETS FOUND:")
        for instr, count in counts.items():
            for snippet in count['snippets']:
                snippet = highlight_text(snippet, self.config['colors'])
                print(f'"... {snippet}"')

        #prompt for user confirmation
        instr_str = "|".join(counts.keys())
        val = input_with_prefill('\n=> Edit instrument list (pipe-seperated): ', instr_str)
        val = val.replace(' ', '')
        return val


    def add_by_bibcode(self, bibcode, interactive=False, **kwargs):
        #TODO: NOTE: Without querying for 'keck' in full text, highlights will not be returned.
        q = f"identifier:{bibcode}"
        data = self.query_ads(q)
        articles = data['response']['docs'] 
        for article in articles:
            # Print useful warnings
            if bibcode != article['bibcode']:
                log.warning("Requested {} but ADS API returned {}".format(bibcode, article['bibcode']))
            if interactive and ('NONARTICLE' in article['property']):
                # Note: data products are sometimes tagged as NONARTICLE
                log.warning("{} is not an article.".format(article['bibcode']))
            if self.article_exists(article):
                log.warning("{} is already in the db.".format(article['bibcode']))
            else:
                if interactive:
                    self.add_interactively(article)
                else:
                    self.add(article, **kwargs)

    def delete_by_bibcode(self, bibcode):
        cur = self.con.execute("DELETE FROM pubs WHERE bibcode = ?;", [bibcode])
        log.info('Deleted {} row(s).'.format(cur.rowcount))
        self.con.commit()

    def article_exists(self, article):
        count = self.con.execute("SELECT COUNT(*) FROM pubs WHERE id = ? OR bibcode = ?;",
                                 [article['id'], article['bibcode']]).fetchone()[0]
        return bool(count)

    def query(self, mission=None, science=None, year=None):
        """Query the database by mission and/or science and/or year.

        Parameters
        ----------
        mission : str
            Examples: 'kepler' or 'k2'
        science : str
            Examples: 'exoplanets' or 'astrophysics'
        year : int or list of int
            Examples: 2009, 2010, [2009, 2010], ...

        Returns
        -------
        rows : list
            List of SQLite result rows.
        """
        # Build the query
        if mission is None:
            where = "(mission != 'unrelated') "
        else:
            where = "(mission = '{}') ".format(mission)

        if science is not None:
            where += " AND science = '{}' ".format(science)

        if year is not None:
            if isinstance(year, (list, tuple)):  # Multiple years?
                str_year = ["'{}'".format(y) for y in year]
                where += " AND year IN (" + ", ".join(str_year) + ")"
            else:
                where += " AND year = '{}' ".format(year)

        cur = self.con.execute("SELECT year, month, metrics, bibcode "
                               "FROM pubs "
                               "WHERE {} "
                               "ORDER BY date DESC; ".format(where))
        return cur.fetchall()

    def get_metadata(self, bibcode):
        """Returns a dictionary of the raw metadata given a bibcode."""
        cur = self.con.execute("SELECT metrics FROM pubs WHERE bibcode = ?;", [bibcode])
        return json.loads(cur.fetchone()[0])

    def to_markdown(self, title="Publications",
                    group_by_month=False, save_as=None, **kwargs):
        """Returns the publication list in markdown format.
        """
        if group_by_month:
            group_idx = 1
        else:
            group_idx = 0  # by year

        articles = collections.OrderedDict({})
        for row in self.query(**kwargs):
            group = row[group_idx]
            if group.endswith("-00"):
                group = group[:-3] + "-01"
            if group not in articles:
                articles[group] = []
            art = json.loads(row[2])
            # The markdown template depends on "property" being iterable
            if art["property"] is None:
                art["property"] = []
            articles[group].append(art)

        templatedir = os.path.join(PACKAGEDIR, 'templates')
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(templatedir))
        template = env.get_template('template.md')
        markdown = template.render(title=title, save_as=save_as,
                                   articles=articles)
        if sys.version_info >= (3, 0):
            return markdown  # Python 3
        else:
            return markdown.encode("utf-8")  # Python 2

    def save_markdown(self, output_fn, **kwargs):
        """Saves the database to a text file in markdown format.

        Parameters
        ----------
        output_fn : str
            Path of the file to write.
        """
        markdown = self.to_markdown(save_as=output_fn.replace("md", "html"),
                                    **kwargs)
        log.info('Writing {}'.format(output_fn))
        f = open(output_fn, 'w')
        f.write(markdown)
        f.close()

    def plot(self):
        """Saves beautiful plot of the database."""
        missions = self.config.get('missions', [])
        sciences = self.config.get('sciences', [])
        plots_cfg = self.config.get('plots', [])
        # for ext in ['pdf', 'png']:
        #     plot.plot_by_year(self, f"kpub-publication-rate.{ext}", missions=missions)
        #     plot.plot_by_year(self, f"kpub-publication-rate-no-extrapolation.{ext}", missions=missions, extrapolate=False)
        #     for mission in missions:
        #         plot.plot_by_year(self, f"kpub-publication-rate-{mission}.{ext}", missions=[mission])
        #     plot.plot_science_piechart(self, f"kpub-piechart.{ext}", sciences=sciences)
        #     plot.plot_author_count(self, f"kpub-author-count.{ext}")

        # #bokeh plots
        # if plots_cfg['instruments']:
        #     plot.plot_instruments(self, f"kpub-publications-by-instrument", 
        #                           year_begin=plots_cfg['year_begin'],
        #                           missions=missions, 
        #                           instruments=plots_cfg['instruments'])

        if self.config['aff_defs']:
            plot.plot_affiliations(self, f"kpub-affiliations", 
                                  year_begin=plots_cfg['year_begin'],
#                                  year_begin=plots_cfg['year_begin'],
                                  missions=missions)


    def get_metrics(self, year=None):
        """Returns a dictionary of overall publication statistics.

        The metrics include:
        * # of publications since XX.
        * # of unique author surnames.
        * # of citations.
        * # of peer-reviewed pubs.
        * # of per mission and science
        """

        missions = self.config.get('missions', [])
        sciences = self.config.get('sciences', [])

        #init stats
        metrics = {}
        metrics['publication_count'] = 0
        metrics['refereed_count'] = 0
        metrics['citation_count'] = 0
        metrics['phd_count'] = 0
        for mission in missions:
            metrics[f'{mission}_count'] = 0
            metrics[f'{mission}_refereed_count'] = 0
            metrics[f'{mission}_citation_count'] = 0
            metrics[f'{mission}_phd_count'] = 0
        for science in sciences:
            metrics[f'{science}_count'] = 0


        authors, first_authors = {}, {}
        authors['all'] = []
        first_authors['all'] = []
        for mission in missions:
            authors[mission] = []
            first_authors[mission] = []

        for article in self.query(year=year):
            api_response = article[2]
            js = json.loads(api_response)

            #general count
            metrics["publication_count"] += 1
            metrics[f"{js['mission']}_count"] += 1

            #phd counts
            if "PhDT" in js['bibcode']:
                metrics["phd_count"] += 1
                metrics[f"{js['mission']}_phd_count"] += 1

            #science counts
            try:
                metrics[f"{js['science']}_count"] += 1
            except KeyError:
                pass
                #log.warning(f"{js['bibcode']}: no science category")

            #author counts
            authors['all'].extend(js['author_norm'])
            first_authors['all'].append(js['first_author_norm'])
            authors[js['mission']].extend(js['author_norm'])
            first_authors[js['mission']].append(js['first_author_norm'])

            #refereed counts
            try:
                if "REFEREED" in js['property']:
                    metrics["refereed_count"] += 1
                    metrics[f"{js['mission']}_refereed_count"] += 1
            except TypeError:  # proprety is None
                pass

            #citation counts
            try:
                metrics["citation_count"] += js['citation_count']
                metrics[f"{js['mission']}_citation_count"] += js['citation_count']
            except (KeyError, TypeError):
                log.warning("{}: no citation_count".format(js["bibcode"]))

        metrics["author_count"] = np.unique(authors['all']).size
        metrics["first_author_count"] = np.unique(first_authors['all']).size
        for mission in missions:
            metrics[f"{mission}_author_count"] = np.unique(authors[mission]).size
            metrics[f"{mission}_first_author_count"] = np.unique(first_authors[mission]).size

        # Also compute fractions
        pubcount = metrics["publication_count"]
        for mission in missions:
            metrics[mission+"_fraction"] = metrics[mission+"_count"] / pubcount if pubcount > 0 else 0
        for science in sciences:
            metrics[science+"_fraction"] = metrics[science+"_count"] / pubcount if pubcount > 0 else 0
    
        return metrics

    def get_all(self, mission=None, science=None):
        """Returns a list of dictionaries, one entry per publication."""
        articles = self.query(mission=mission, science=science)
        return [json.loads(art[2]) for art in articles]

    def get_most_cited(self, mission=None, science=None, top=10):
        """Returns the most-cited publications."""
        bibcodes, citations = [], []
        articles = self.query(mission=mission, science=science)
        for article in articles:
            api_response = article[2]
            js = json.loads(api_response)
            bibcodes.append(article[3])
            if js["citation_count"] is None:
                citations.append(0)
            else:
                citations.append(js["citation_count"])
        idx_top = np.argsort(citations)[::-1][0:top]
        return [json.loads(articles[idx][2]) for idx in idx_top]

    def get_most_read(self, mission=None, science=None, top=10):
        """Returns the most-cited publications."""
        bibcodes, citations = [], []
        articles = self.query(mission=mission, science=science)
        for article in articles:
            api_response = article[2]
            js = json.loads(api_response)
            bibcodes.append(article[3])
            citations.append(js["read_count"])
        idx_top = np.argsort(citations)[::-1][0:top]
        return [json.loads(articles[idx][2]) for idx in idx_top]

    def get_most_active_first_authors(self, min_papers=6):
        """Returns names and paper counts of the most active first authors."""
        articles = self.query()
        authors = {}
        for article in articles:
            api_response = article[2]
            js = json.loads(api_response)
            first_author = js["first_author_norm"]
            try:
                authors[first_author] += 1
            except KeyError:
                authors[first_author] = 1
        names = np.array(list(authors.keys()))
        paper_count = np.array(list(authors.values()))
        idx_top = np.argsort(paper_count)[::-1]
        mask = paper_count[idx_top] >= min_papers
        return zip(names[idx_top], paper_count[idx_top[mask]])

    def get_all_authors(self, top=20):
        articles = self.query()
        authors = {}
        for article in articles:
            api_response = article[2]
            js = json.loads(api_response)
            for auth in js["author_norm"]:
                try:
                    authors[auth] += 1
                except KeyError:
                    authors[auth] = 1
        names = np.array(list(authors.keys()))
        paper_count = np.array(list(authors.values()))
        idx_top = np.argsort(paper_count)[::-1][:top]
        return names[idx_top], paper_count[idx_top]

    def get_affiliation_counts(self, year_begin, year_end, mission):

        #init data
        counts = {}
        aff_defs = self.config['aff_defs']
        for affdef in aff_defs:
            counts['first author '+affdef['type']] = {}
            counts['top3 authors '+affdef['type']] = {}
            for year in range(year_begin, year_end+1):
                counts['first author '+affdef['type']][year] = 0
                counts['top3 authors '+affdef['type']][year] = 0

        #query
        cur = self.con.execute("select year, metrics from pubs "
                               f" where mission='{mission}' "
                               f" and year >= '{year_begin}'"
                               f" and year <= '{year_end}'"
                               )
        articles = cur.fetchall()

        #for each article, get affiliations for first 3 authors for each article
        for article in articles:
            year = int(article[0])
            metrics = json.loads(article[1])
            num_affs = len(metrics['aff'])
            affs = []
            for i in range(0,3):
                if num_affs > i:
                    afftype = self.get_aff_type(metrics['aff'][i], aff_defs)
                    if not afftype: continue
                    affs.append(afftype)
                    if i == 0:
                        counts['first author '+afftype][year] += 1
            if len(affs) == 3 and len(set(affs)) == 1:
                counts['top3 authors '+afftype][year] += 1

        return counts

    def get_aff_type(self, affstr, aff_defs):
        '''
        Search for institution strings in affiliation string.  Affiliation string
        can have multiple semicolon-delimited entries.  'affmap' is an ordered 
        array of preferred affiliation types.  Each type has an array of strings to
        search for.
        '''
        #Sometimes the value is blank or "-"
        if len(affstr.strip()) <= 2:
            return None

        default = ''
        affs = affstr.split(";")
        for affdef in aff_defs:
            afftype = affdef['type']
            if not affdef['strings']: 
                default = afftype
                continue
            for string in affdef['strings']:
                for aff in affs:
                    if string.isupper():
                        if re.search(string, aff):
                            return afftype
                    else:
                        if re.search(string, aff, re.IGNORECASE):
                            return afftype                  
        return default

    def get_annual_publication_count(self, year_begin=2009, year_end=datetime.datetime.now().year,
                                     instrument=None):
        """Returns a dict containing the number of publications per year per mission.

        Parameters
        ----------
        year_begin : int
            Year to start counting. (default: 2009)

        year_end : int
            Year to end counting. (default: current year)
        """
        # Initialize a dictionary to contain the data to plot
        result = {}
        missions = self.config.get('missions', [])
        for mission in missions:
            result[mission] = {}
            for year in range(year_begin, year_end + 1):
                result[mission][year] = 0
            q = "SELECT year, COUNT(*) FROM pubs "
            q += f" WHERE mission = '{mission}' "
            q += f" AND year >= '{year_begin}' "
            if instrument: 
                q += f" AND instruments like '%{instrument}%' "
            q += " GROUP BY year;"
            cur = self.con.execute(q)
            rows = list(cur.fetchall())
            for row in rows:
                if int(row[0]) <= year_end:
                    result[mission][int(row[0])] = row[1]
        # Also combine counts
        result['both'] = {}
        for year in range(year_begin, year_end + 1):
            result['both'][year] = sum(result[mission][year] for mission in missions)
        return result

    def get_annual_publication_count_cumulative(self, year_begin=2009, year_end=datetime.datetime.now().year):
        """Returns a dict containing the cumulative number of publications per year per mission.

        Parameters
        ----------
        year_begin : int
            Year to start counting. (default: 2009)

        year_end : int
            Year to end counting. (default: current year)
        """
        # Initialize a dictionary to contain the data to plot
        result = {}
        missions = self.config.get('missions', [])
        for mission in missions:
            result[mission] = {}
            for year in range(year_begin, year_end + 1):
                cur = self.con.execute("SELECT COUNT(*) FROM pubs "
                                       "WHERE mission = ? "
                                       "AND year <= ?;",
                                       [mission, str(year)])
                result[mission][year] = cur.fetchone()[0]
        # Also combine counts
        result['both'] = {}
        for year in range(year_begin, year_end + 1):
            result['both'][year] = sum(result[mission][year] for mission in missions)
        return result

    def update(self, month=None):
        """
        Query ADS for new publications.
        Parameters:
            month (str): Used for ADS pubdate param. Format "YYYY-MM" or "YYYY".
        """
        # # git pull reminder
        # print(HIGHLIGHTS['YELLOW'] +
        #       "Reminder: did you `git pull` kpub before running "
        #       "this command? [y/n] " +
        #       HIGHLIGHTS['END'],
        #       end='')
        # if input() == 'n':
        #     return

        #Assume current month if not supplied.
        #NOTE: We use the term "month" but user can supply just the year to do a whole year.
        if month is None:
            month = datetime.datetime.now().strftime("%Y-%m")

        #query 1
        queries = self.config.get('ads_queries')
        for query in queries:
            log.info(f"\nQuerying {query['name']} (date={month})")
            data = self.query_ads(query['query'], month)
            tmp_articles = data['response']['docs'] 

            #remove those already in our db
            articles = []
            for a in tmp_articles:
                if self.article_exists(a): print(f"SKIPPING {a['bibcode']} already in DB.")
                else: articles.append(a)

            #loop and add
            for idx, article in enumerate(articles):

                # Ignore articles without abstract
                if not article.get('abstract'):
                    continue

                # Ignore proposals, cospar abstracts and tmp articles
                bibcode = article['bibcode']
                if ".prop." in bibcode or "cosp.." in bibcode or ".tmp" in bibcode:
                    continue

                # Propose to the user
                statusmsg = f"Showing article {idx+1} out of {len(articles)} ({query['name']} query)\n\n"
                highlights = data['highlighting'][article['id']]
                self.add_interactively(article, statusmsg=statusmsg, highlights=highlights)

        log.info(f'\nFinished reviewing all articles for {month}.')


    def open_pdf(self, bibcode):
        '''Open PDF file in local browser.  Download if necessary.'''
        key = self.config.get('ADS_API_KEY')
        outfile = get_pdf_file(bibcode, key)
        if os.path.isfile(outfile):
            print(f"Opening {outfile}...")
            webbrowser.open('file://' + os.path.realpath(outfile))


    def query_ads(self, query, pubdate=None):
        '''
        Query ADS API.  Add in standard params needed for data store and text highlights.

        Parameters:
            query (str): An ADS compliant query string (exactly what is entered in web search GUI.)
            date (str): Optional ADS pubdate param. YYYY-MM or YYYY. Ex: "2019-03", "2020"
        '''

        query = query.replace(' ', '+')
        query = query.replace('"', '%22')
        if pubdate: query += f"+pubdate:{pubdate}"

        fl = ','.join(FIELDS)
        url = (f'{ADS_API}'
            f'q={query}'
            f"&fl={fl}"
            "&sort=date+asc"
            "&hl=true"
            "&hl.fl=ack,body,title,abstract"
            "&hl.snippets=4"
            "&hl.fragsize=100"
            "&hl.maxAnalyzedChars=500000"
            "&rows=9999999"
        )
        key = self.config.get('ADS_API_KEY')
        headers = {'Authorization': f'Bearer {key}'}
        r = requests.get(url, headers=headers)
        data = r.json()
        return data


##################
# Helper functions
##################

def highlight_text(text, colors):

    for word, color in colors.items():
        pattern = re.compile(word, re.IGNORECASE)
        text = pattern.sub(HIGHLIGHTS[color] + word + HIGHLIGHTS['END'], str(text))
    return text
     
def display_abstract(article_dict, colors, highlights=None):
    """Prints the title and abstract of an article to the terminal,
    given a dictionary of the article metadata.

    Parameters
    ----------
    article : `dict` containing standard ADS metadata keys
    colors  : `dict` mapping keywords to colors
    highlights: `dict` containing 'ack' and 'body' lists of relevent text snippets
    """
    title = article_dict['title'][0]
    try:
        abstract = article_dict['abstract']
    except KeyError:
        abstract = ""

    title = highlight_text(title, colors)
    abstract = highlight_text(abstract, colors)

    ack_hl = 'NONE'
    if highlights and 'ack' in highlights:
        ack_hl = ''
        for ack in highlights['ack']:
            ack = ack.replace('<em>', '').replace('</em>', '')
            ack_hl += "\n\t" + '"...' + highlight_text(ack, colors) + '"'

    body_hl = 'NONE'
    if highlights and 'body' in highlights:
        body_hl = ''
        for body in highlights['body']:
            body = body.replace('<em>', '').replace('</em>', '')
            body_hl += "\n\t" + '"...' + highlight_text(body, colors) + '"'

    print(title)
    print('-'*len(title))
    print(abstract)
    print('')
    print(f"Acknowledgement highlights: {ack_hl}")
    print(f"Body highlights: {body_hl}")
    print('')
    print('Authors: ' + ', '.join(article_dict['author']))
    print('Date: ' + article_dict['pubdate'])
    print('Status: ' + str(article_dict['property']))
    print('URL: http://adsabs.harvard.edu/abs/' + article_dict['bibcode'])
    print('')


def get_word_match_counts_by_query(bibcode, words):

    bibcode = bibcode.replace('&', '%26')

    counts = {}
    for word in words:
        word = word.replace(' ', '+')
        url = (f'{ADS_API}' 
            f'q=bibcode:%22{bibcode}%22+full:%22{word}%22'
            "&fl=id,bibcode"
            "&sort=date+asc"
            "&hl=true"
            "&hl.fl=ack,body,title,abstract"
            "&hl.snippets=4"
            "&hl.fragsize=100"
            "&hl.maxAnalyzedChars=500000"
        )
        headers = {'Authorization': 'Bearer kKZEcC7UXr11ITa3Kh34RPZvFJHHCEXXbDITGDDU'}
        r = requests.get(url, headers=headers)
        data = r.json()
        counts[word] = {'count': 0, 'snippets': []}
        for doc in data['response']['docs']:
            id = doc['id']
            highlights = data['highlighting'][id]
            for field, snippets in highlights.items():
                for snippet in snippets:
                    counts[word]['count'] += 1
                    counts[word]['snippets'].append(snippet)

    #only return counts > 0
    counts = {key:val for key, val in counts.items() if val['count'] != 0}
    return counts
 

def get_word_match_counts_by_pdf(bibcode, words, ads_api_key):

    #get pdf file and text
    outfile = get_pdf_file(bibcode, ads_api_key)
    text = get_pdf_text(outfile).lower()
    text = text.replace("\n",' ')
    text = text.replace("\r",' ')
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]', ' ', text)

    #count up matches
    counts = {}
    for word in words:
        counts[word] = {'count': 0, 'snippets': []}
        for ch in (' ', '/', '\(', '-', ':'):
            find = f"{ch}{word}".lower()
            for m in re.finditer(find, text):
                    snippet = text[m.start()-80:m.end()+80]
                    counts[word]['count'] += 1
                    counts[word]['snippets'].append(snippet)

    #only return counts > 0
    counts = {key:val for key, val in counts.items() if val['count'] != 0}
    return counts
  

def get_pdf_file(bibcode, ads_api_key):

    outfile = f'/tmp/{bibcode}.pdf'
    if os.path.isfile(outfile):
        return outfile

    print('\nRetrieving PDF (May take up to a minute)...')
    url = f'https://ui.adsabs.harvard.edu/link_gateway/{bibcode}/EPRINT_PDF'
    #url = f'https://ui.adsabs.harvard.edu/link_gateway/{bibcode}/PUB_PDF'
    headers = {f'Authorization': f'Bearer {ads_api_key}'}
    r = requests.get(url, headers=headers)
    if r.status_code != 200 or len(r.content) < 1000:
        print("Could not download PDF file.")
        return False
    with open(outfile, 'wb') as f:
         f.write(r.content)
    return outfile


def get_pdf_text(outfile):
    assert textract, "No textract module found."
    try:
        text = textract.process(outfile, method='pdfminer')
    except Exception as e:
        print("textract: pdfminer method failed.  Trying pdftotext method...")
        text = textract.process(outfile, method='pdftotext')
    text = text.decode("utf-8")
    return text


def input_with_prefill(prompt, text):
    def hook():
        readline.insert_text(text)
        readline.redisplay()
    readline.set_pre_input_hook(hook)
    result = input(prompt)
    readline.set_pre_input_hook()
    return result


def add_prompt_valmaps(valmap, vals):

    for idx, val in enumerate(vals):
        k = str(idx+1)
        valmap[k] = val
    return valmap


def prompt_grouping(valmap, type):

    prompt = f"=> Select {type}: "
    for key, val in valmap.items():
        prompt += f" [{key}] {val.capitalize()} "
    prompt += " or [] skip? "

    print(prompt, end="")
    val = input()
    return val




#########################
# Command-line interfaces
#########################

def kpub(args=None):
    """Lists the publications in the database in Markdown format."""
    parser = argparse.ArgumentParser(
        description="View the publication list in markdown format.")
    parser.add_argument('-f', metavar='dbfile',
                        type=str, default=DEFAULT_DB,
                        help="Location of the publication list db. "
                             "Defaults to ~/.kpub.db.")
    parser.add_argument('--science', dest="science", type=str, default=None,
                        help="Only show a particular science. Defaults to all.")
    parser.add_argument('--mission', dest="mission", type=str, default=None,
                        help="Only show a particular mission. Defaults to all.")
    parser.add_argument('-m', '--month', action='store_true',
                        help='Group the papers by month rather than year.')
    parser.add_argument('-s', '--save', action='store_true',
                        help='Save the output and plots in the current directory.')
    args = parser.parse_args(args)

    config = yaml.load(open(f'{PACKAGEDIR}/config/config.live.yaml'), Loader=yaml.FullLoader)
    title = config.get('prepend', '').capitalize()

    db = PublicationDB(args.f)

    if args.save:
        for bymonth in [True, False]:
            if bymonth:
                suffix = "-by-month"
                title_suffix = " by month"
            else:
                suffix = ""
                title_suffix = ""

            output_fn = f'kpub{suffix}.md'
            db.save_markdown(output_fn,
                             group_by_month=bymonth,
                             title=f"{title} publications{title_suffix}")

            sciences = self.config.get('sciences', [])
            for science in sciences:
                output_fn = f'kpub-{science}{suffix}.md'
                db.save_markdown(output_fn,
                                 group_by_month=bymonth,
                                 science=science,
                                 title=f"{title} {science} publications{title_suffix}")

            missions = self.config.get('missions', [])
            for mission in missions:
                output_fn = f'kpub-{mission}{suffix}.md'
                db.save_markdown(output_fn,
                                 group_by_month=bymonth,
                                 mission=mission,
                                 title=f"{mission.capitalize()} publications{title_suffix}")

        # Finally, produce an overview page
        templatedir = os.path.join(PACKAGEDIR, 'templates')
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(templatedir))
        template = env.get_template('template-overview.md')
        markdown = template.render(metrics=db.get_metrics(),
                                   most_cited=db.get_most_cited(top=20),
                                   most_active_first_authors=db.get_most_active_first_authors(),
                                   now=datetime.datetime.now())
        # most_read=db.get_most_read(20),
        filename = 'publications.md'
        log.info('Writing {}'.format(filename))
        f = open(filename, 'w')
        if sys.version_info >= (3, 0):
            f.write(markdown)  # Python 3
        else:
            f.write(markdown.encode("utf-8"))  # Legacy Python
        f.close()

    else:
        output = db.to_markdown(group_by_month=args.month, mission=args.mission, science=args.science)
        from signal import signal, SIGPIPE, SIG_DFL
        signal(SIGPIPE, SIG_DFL)
        print(output)


def kpub_plot(args=None):
    """Creates beautiful plots of the database."""
    parser = argparse.ArgumentParser(description="Creates beautiful plots of the database.")
    parser.add_argument('-f', metavar='dbfile',
                        type=str, default=DEFAULT_DB,
                        help="Location of the publication list db. Defaults to ~/.kpub.db.")
    args = parser.parse_args(args)

    config = yaml.load(open(f'{PACKAGEDIR}/config/config.live.yaml'), Loader=yaml.FullLoader)
    PublicationDB(args.f, config).plot()


def kpub_update(args=None):
    """Interactively query ADS for new publications."""
    parser = argparse.ArgumentParser(
        description="Interactively query ADS for new publications.")
    parser.add_argument('-f', metavar='dbfile',
                        type=str, default=DEFAULT_DB,
                        help="Location of the publication list db. Defaults to ~/.kpub.db.")
    parser.add_argument('month', nargs='?', default=None,
                        help='Month to query, YYYY-MM or YYYY. e.g. "2015-06" or "2020"')
    args = parser.parse_args(args)

    config = yaml.load(open(f'{PACKAGEDIR}/config/config.live.yaml'), Loader=yaml.FullLoader)

    PublicationDB(args.f, config).update(month=args.month)


def kpub_add(args=None):
    """Add a publication with a known ADS bibcode."""
    parser = argparse.ArgumentParser(
        description="Add a paper to the publication list.")
    parser.add_argument('-f', metavar='dbfile',
                        type=str, default=DEFAULT_DB,
                        help="Location of the publication list db. Defaults to ~/.kpub.db.")
    parser.add_argument('bibcode', nargs='+',
                        help='ADS bibcode that identifies the publication.')
    args = parser.parse_args(args)

    config = yaml.load(open(f'{PACKAGEDIR}/config/config.live.yaml'), Loader=yaml.FullLoader)

    db = PublicationDB(args.f, config)
    for bibcode in args.bibcode:
        db.add_by_bibcode(bibcode, interactive=True)


def kpub_delete(args=None):
    """Deletes a publication using its ADS bibcode."""
    parser = argparse.ArgumentParser(
        description="Deletes a paper from the publication list.")
    parser.add_argument('-f', metavar='dbfile',
                        type=str, default=DEFAULT_DB,
                        help="Location of the publication list db. Defaults to ~/.kpub.db.")
    parser.add_argument('bibcode', nargs='+',
                        help='ADS bibcode that identifies the publication.')
    args = parser.parse_args(args)

    config = yaml.load(open(f'{PACKAGEDIR}/config/config.live.yaml'), Loader=yaml.FullLoader)

    db = PublicationDB(args.f, config)
    for bibcode in args.bibcode:
        db.delete_by_bibcode(bibcode)


def kpub_import(args=None):
    """Import publications from a csv file.

    The csv file must contain entries of the form "bibcode,mission,science".
    The actual metadata of each publication will be grabbed using the ADS API,
    hence this routine may take 10-20 minutes to complete.
    """
    parser = argparse.ArgumentParser(
        description="Batch-import papers into the publication list "
                    "from a CSV file. The CSV file must have three columns "
                    "(bibcode,mission,science) separated by commas. "
                    "For example: '2004ApJ...610.1199G,kepler,astrophysics'.")
    parser.add_argument('-f', metavar='dbfile',
                        type=str, default=DEFAULT_DB,
                        help="Location of the publication list db. Defaults to ~/.kpub.db.")
    parser.add_argument('csvfile',
                        help="Filename of the csv file to ingest.")
    args = parser.parse_args(args)

    config = yaml.load(open(f'{PACKAGEDIR}/config/config.live.yaml'), Loader=yaml.FullLoader)

    db = PublicationDB(args.f, config)
    import time
    for line in ProgressBar(open(args.csvfile, 'r').readlines()):
        line = line.strip()
        if not line:
            continue
        for attempt in range(5):
            try:
                col = line.strip().split(',')  # Naive csv parsing
                bibcode = col[0]
                mission = col[1]
                science = col[2]
                instrs  = col[3]
                archive = col[4]
                db.add_by_bibcode(bibcode, mission=mission, science=science,
                    instruments=instrs, archive=archive)
                time.sleep(0.1)
                break
            except Exception as e:
                print("Warning: attempt #{} for {}: error '{}'".format(attempt, col[0], e))


def kpub_export(args=None):
    """Export the bibcodes and classifications in CSV format."""
    parser = argparse.ArgumentParser(description="Export the publication list in CSV format.")
    parser.add_argument('-f', metavar='dbfile', type=str, default=DEFAULT_DB,
        help="Location of the publication list db. Defaults to ~/.kpub.db.")
    parser.add_argument("--archive", default=False, action="store_true",
        help="Only export records marked as archived.")
    parser.add_argument("--bibcodes", default=False, action="store_true",
        help="Only export one bibcode column.")
    args = parser.parse_args(args)

    q = "SELECT bibcode, mission, science, instruments, archive "
    q += " FROM pubs WHERE 1"
    if args.archive: 
        q += " AND archive='1' "
    q += " ORDER BY bibcode asc;"

    config = yaml.load(open(f'{PACKAGEDIR}/config/config.live.yaml'), Loader=yaml.FullLoader)
    db = PublicationDB(args.f, config)
    cur = db.con.execute(q)

    for row in cur.fetchall():
        if args.bibcodes: print(f'{row[0]}')
        else:             print(f'{row[0]},{row[1]},{row[2]},{row[3]},{row[4]}')


def kpub_spreadsheet(args=None):
    """Export the publication database to an Excel spreadsheet."""
    try:
        import pandas as pd
    except ImportError:
        print('ERROR: pandas needs to be installed for this feature.')

    parser = argparse.ArgumentParser(
        description="Export the publication list in XLS format.")
    parser.add_argument('-f', metavar='dbfile',
                        type=str, default=DEFAULT_DB,
                        help="Location of the publication list db. Defaults to ~/.kpub.db.")
    args = parser.parse_args(args)

    config = yaml.load(open(f'{PACKAGEDIR}/config/config.live.yaml'), Loader=yaml.FullLoader)

    db = PublicationDB(args.f, config)
    spreadsheet = []
    cur = db.con.execute("SELECT bibcode, year, month, date, mission, science, metrics "
                         "FROM pubs WHERE mission != 'unrelated' ORDER BY bibcode;")
    for row in cur.fetchall():
        metrics = json.loads(row[6])
        try:
            if 'REFEREED' in metrics['property']:
                refereed = 'REFEREED'
            elif 'NOT REFEREED' in metrics['property']:
                refereed = 'NOT REFEREED'
            else:
                refereed = ''
        except TypeError:  # .property is None
            refereed = ''
        # Compute citations per year
        try:
            dateobj = datetime.datetime.strptime(row[3], '%Y-%m-00')
        except ValueError:
            dateobj = datetime.datetime.strptime(row[3], '%Y-00-00')
        publication_age = datetime.datetime.now() - dateobj
        try:
            citations_per_year = metrics['citation_count'] / (publication_age.days / 365)
        except (TypeError, ZeroDivisionError):
            citations_per_year = 0

        myrow = collections.OrderedDict([
                    ('bibcode', row[0]),
                    ('year', row[1]),
                    ('date', row[3]),
                    ('mission', row[4]),
                    ('science', row[5]),
                    ('refereed', refereed),
                    ('citation_count', metrics['citation_count']),
                    ('citations_per_year', round(citations_per_year, 2)),
                    ('read_count', metrics['read_count']),
                    ('first_author_norm', metrics['first_author_norm']),
                    ('title', metrics['title'][0]),
                    ('keyword_norm', metrics['keyword_norm']),
                    ('abstract', metrics['abstract']),
                    ('co_author_norm', metrics['author_norm']),
                    ('affiliations', metrics['aff'])])
        spreadsheet.append(myrow)

    output_fn = 'kpub-publications.xls'
    print('Writing {}'.format(output_fn))
    pd.DataFrame(spreadsheet).to_excel(output_fn, index=False)


if __name__ == '__main__':

    #todo: This is a hack until we figure out packaging
    cmd = sys.argv[1]
    if   cmd == 'update': kpub_update(sys.argv[2:])
    elif cmd == 'plot':   kpub_plot(sys.argv[2:])
    elif cmd == 'add':    kpub_add(sys.argv[2:])
    elif cmd == 'delete': kpub_delete(sys.argv[2:])
    elif cmd == 'import': kpub_import(sys.argv[2:])
    elif cmd == 'export': kpub_export(sys.argv[2:])
    else:                 kpub(sys.argv[1:])


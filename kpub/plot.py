"""Creates beautiful visualizations of the publication database."""
import datetime
import numpy as np
from astropy import log
from pprint import pprint
import sys

from matplotlib import pyplot as pl
import matplotlib.patheffects as path_effects
import matplotlib as mpl

from bokeh.palettes import Category20
from bokeh.plotting import figure, show, output_file, save
from bokeh.models import Legend, ColumnDataSource, Title
from bokeh.io import export_png


# Configure the aesthetics
mpl.rcParams["figure.figsize"] = (10, 6)
mpl.rcParams["interactive"] = False
mpl.rcParams["lines.antialiased"] = True
# Patches
mpl.rcParams["patch.linewidth"] = 0.5
mpl.rcParams["patch.facecolor"] = "348ABD"
mpl.rcParams["patch.edgecolor"] = "eeeeee"
mpl.rcParams["patch.antialiased"] = True
# Font
mpl.rcParams["font.family"] = "sans-serif"
mpl.rcParams["font.size"] = 16
mpl.rcParams["font.sans-serif"] = "Open Sans"
mpl.rcParams["text.color"] = "333333"
# Axes
mpl.rcParams["axes.facecolor"] = "ecf0f1"
mpl.rcParams["axes.edgecolor"] = "bdc3c7"
mpl.rcParams["axes.linewidth"] = 1.0
mpl.rcParams["axes.grid"] = False
mpl.rcParams["axes.titlesize"] = "x-large"
mpl.rcParams["axes.labelsize"] = "x-large"
mpl.rcParams["axes.labelweight"] = "normal"
mpl.rcParams["axes.labelcolor"] = "333333"
mpl.rcParams["axes.axisbelow"] = True
mpl.rcParams["axes.unicode_minus"] = True
# Ticks
mpl.rcParams["xtick.color"] = "333333"
mpl.rcParams["ytick.color"] = "333333"
mpl.rcParams["xtick.major.size"] = 0
mpl.rcParams["ytick.major.size"] = 0
# Grid
mpl.rcParams["grid.color"] = "bdc3c7"
mpl.rcParams["grid.linestyle"] = "-"
mpl.rcParams["grid.linewidth"] = 1


def plot_instruments(db,
                     output_fn='kpub-publications-by-instrument.html',
                     year_begin=2000,
                     missions=[],
                     instruments=[]):
    """Plots a multiline graph showing the number of publications per instrument per year.

    Parameters
    ----------
    db : `PublicationDB` object
        Data to plot.

    output_fn : str
        Output filename of the plot.

    first_year : int
        What year should the plot start?
    """
    # Obtain the dictionary which provides the annual counts
    data = {}
    for instr in instruments:    
      year_end = datetime.datetime.now().year -1
      counts = db.get_annual_publication_count(year_begin=year_begin, 
                                               year_end=year_end,
                                               instrument=instr)
      data[instr] = counts['keck']

    years = list(np.arange(year_begin, year_end+1))
    years = [str(year) for year in years]
    instrs = list(data.keys())
    pallete = Category20[len(instrs)]
    values = []
    for instr, idata in data.items():
      vals = [idata[year] for year in idata]
      values.append(vals)
    plotdata = {
      'years': [years] * len(instrs),
      'values': values,
      'columns': instrs,
      'color': pallete[0:len(instrs)]
    }
    source = ColumnDataSource(plotdata)
    p = figure(width = 1000, height = 800, x_range = years)
    p.multi_line(xs = 'years',
                 ys = 'values',
                 color = 'color',
                 legend = 'columns',
                 line_width = 3,
                 source = source)
    p.add_layout(Title(text="by instrument", text_font_style="italic"), 'above')
    p.add_layout(Title(text="Publications per year", text_font_size="16pt"), 'above')
    p.legend.location = 'top_left'

    log.info("Writing {}".format(output_fn))
    output_file(output_fn)
    save(p)
    #show(p)


def plot_by_year(db,
                 output_fn='kpub-publication-rate.pdf',
                 first_year=2009,
                 barwidth=0.75,
                 dpi=200,
                 extrapolate=True,
                 missions=[],
                 colors=["#3498db", "#27ae60", "#95a5a6"]):
    """Plots a bar chart showing the number of publications per year.

    Parameters
    ----------
    db : `PublicationDB` object
        Data to plot.

    output_fn : str
        Output filename of the plot.

    first_year : int
        What year should the plot start?

    barwidth : float
        Aesthetics -- how wide are the bars?

    dpi : float
        Output resolution.

    extrapolate : boolean
        If `True`, extrapolate the publication count in the current year.

    missions : list str
        Example: ['kepler', 'k2']

    colors : list of str
        Define the facecolor for plots
    """
    # Obtain the dictionary which provides the annual counts
    current_year = datetime.datetime.now().year
    counts = db.get_annual_publication_count(year_begin=first_year, year_end=current_year)
    pprint(counts)
    sys.exit()
    # Now make the actual plot
    fig = pl.figure()
    ax = fig.add_subplot(111)
    for i, mission in enumerate(missions):
        idx = i % len(colors)
        bottom = None
        if i>0:
            prev = missions[i-1]
            bottom = list(counts[prev].values())        
        pl.bar(np.array(list(counts[mission].keys())),
               list(counts[mission].values()),
               bottom = bottom,
               label=mission.capitalize(),
               facecolor=colors[idx],
               width=barwidth)

    # Also plot the extrapolated prediction for the current year
    if extrapolate:
        now = datetime.datetime.now()
        fraction_of_year_passed = float(now.strftime("%-j")) / 365.2425
        current_total = 0
        for mission in missions:
            current_total += counts[mission][current_year]
        expected = (1/fraction_of_year_passed - 1) * current_total
        pl.bar(current_year,
               expected,
               bottom=current_total,
               label='Extrapolation',
               facecolor=colors[2],
               width=barwidth)

    # Aesthetics
    pl.ylabel("Publications per year")
    ax.get_xaxis().get_major_formatter().set_useOffset(False)
    pl.xticks(range(first_year - 1, current_year + 1))
    pl.xlim([first_year - 0.75*barwidth, current_year + 0.75*barwidth])
    pl.legend(bbox_to_anchor=(0.1, 1., 1., 0.),
              loc=3,
              ncol=3,
              borderaxespad=0.,
              handlelength=0.8,
              frameon=False)
    # Disable spines
    ax.spines["left"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    # Only show bottom and left ticks
    ax.get_xaxis().tick_bottom()
    ax.get_yaxis().tick_left()
    # Only show horizontal grid lines
    ax.grid(axis='y')
    pl.tight_layout(rect=(0, 0, 1, 0.95), h_pad=1.5)
    log.info("Writing {}".format(output_fn))
    pl.savefig(output_fn, dpi=dpi)
    pl.close()


def plot_science_piechart(db, output_fn="kpub-piechart.pdf", dpi=200, sciences=[]):
    """Plots a piechart showing science category publications.

    Parameters
    ----------
    db : `PublicationDB` object
        Data to plot.

    output_fn : str
        Output filename of the plot.

    dpi : float
        Output resolution.

    sciences : str list
        List of sciences categories to plot independently
    """
    if not sciences:
      return

    count = []
    for science in sciences:
        cur = db.con.execute("SELECT COUNT(*) FROM pubs "
                             "WHERE science = ?;", [science])
        rows = list(cur.fetchall())
        count.append(rows[0][0])

    # Plot the pie chart
    patches, texts, autotexts = pl.pie(count,
                                       colors=['#f39c12', '#18bc9c'],
                                       autopct="%.0f%%",
                                       startangle=90)
    # Now take care of the aesthetics
    for t in autotexts:
        t.set_fontsize(32)
        t.set_color("white")
        t.set_path_effects([path_effects.Stroke(linewidth=2,
                                                foreground='#333333'),
                            path_effects.Normal()])
    pl.legend(handles=patches,
              labels=sciences,
              fontsize=22,
              bbox_to_anchor=(0.2, 1.05, 1., 0.),
              loc=3,
              ncol=2,
              borderaxespad=0.,
              handlelength=0.8,
              frameon=False)

    pl.axis('equal')  # required to ensure pie chart has equal aspect ratio
    pl.tight_layout(rect=(0, 0, 1, 0.85), h_pad=1.5)
    log.info("Writing {}".format(output_fn))
    pl.savefig(output_fn, dpi=dpi)
    pl.close()


def plot_author_count(db,
                      output_fn='kpub-author-count.pdf',
                      first_year=2008,
                      dpi=200,
                      colors=["#3498db", "#27ae60", "#95a5a6"]):
    """Plots a line chart showing the number of authors over time.

    Parameters
    ----------
    db : `PublicationDB` object
        Data to plot.

    output_fn : str
        Output filename of the plot.

    first_year : int
        What year should the plot start?

    dpi : float
        Output resolution.

    colors : list of str
        Define the facecolors
    """
    # Obtain the dictionary which provides the annual counts
    current_year = datetime.datetime.now().year

    # Now make the actual plot
    fig = pl.figure()
    ax = fig.add_subplot(111)

    cumulative_years = []
    paper_counts = []
    author_counts, first_author_counts = [], []
    for year in range(first_year - 1, current_year + 1):
        cumulative_years.append(year)
        metrics = db.get_metrics(cumulative_years)
        paper_counts.append(metrics['publication_count'])
        author_counts.append(metrics['author_count'])
        first_author_counts.append(metrics['first_author_count'])

    # plot it
    ax.plot([y for y in cumulative_years], paper_counts, label="Publications", lw=9)
    #ax.plot(cumulative_years, author_counts, label="Unique authors", lw=6)
    ax.plot([y for y in cumulative_years], first_author_counts, label="Unique first authors", lw=3)

    # Aesthetics
    #pl.title("Scientific output over time")
    pl.ylabel("Cumulative count")
    ax.get_xaxis().get_major_formatter().set_useOffset(False)
    pl.xticks(range(first_year - 1, current_year + 1))
    pl.xlim([first_year + 0.5, current_year + 0.5])
    pl.ylim([0, 1.05*np.max(paper_counts)])
    pl.legend(bbox_to_anchor=(0.03, 0.95, 0.95, 0.),
              loc="upper left",
              ncol=1,
              borderaxespad=0.,
              handlelength=1.5,
              frameon=True)
    # Disable spines
    ax.spines["left"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    # Only show bottom and left ticks
    ax.get_xaxis().tick_bottom()
    ax.get_yaxis().tick_left()
    # Only show horizontal grid lines
    ax.grid(axis='y')
    pl.tight_layout(rect=(0, 0, 1, 0.98), h_pad=1.5)
    log.info("Writing {}".format(output_fn))
    pl.savefig(output_fn, dpi=dpi)
    pl.close()


def plot_affiliations():
    '''
    TODO: This is just some test code showing how to parse and map affiliations from
    metrics data.  Need to think about how to plot.
    '''

    bibcode = ''
    affdefs = '' #todo: load from config

    con = sql.connect('/Users/joshriley/.kpub.db')
    cur = con.execute(f"SELECT id, bibcode, metrics from pubs where bibcode='{bibcode}'")
    pub = cur.fetchone()
    if not pub:
        #print(f"ERROR could not find {bibcode}")
        return

    #todo: probably can move this and get_aff_type to PublicationDB object
    raw = json.loads(pub[2])
    num_affs = len(raw['aff'])
    affs = []
    for i in range(0,3):
        aff = ''
        if num_affs > i:
            aff = get_aff(raw['aff'][i], affdefs)
        affs.append(aff)


def get_aff_type(affstr, affdefs):
    '''
    Search for institution strings in affiliation string.  Affiliation string
    can have multiple semicolon-delimited entries.  'affmap' is an ordered 
    array of preferred affiliation types.  Each type has an array of strings to
    search for.
    '''
    affs = affstr.split(";")
    for affdef in affdefs:
        afftype = affdef['type']
        for string in affdef['strings']:
            for aff in affs:
                if string.isupper():
                    if re.search(string, aff):
                        return afftype
                else:
                    if re.search(string, aff, re.IGNORECASE):
                        return afftype                  
    return "other"



if __name__ == "__main__":
    plot_by_year()
    plot_science_piechart()

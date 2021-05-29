Title: Publications
Save_as: publications.html

[TOC]

## Publication database

This database contains a list of scientific publications pertaining to {{ institution }}.
The database contains {{ metrics["publication_count"] }} publications, of which {{ metrics["refereed_count"] }} are peer-reviewed.
It demonstrates the important impact of {{ institution }} data on astronomical research.

Last update: {{ now.strftime('%d %b %Y') }}.

<hr/>

## Number of authors

The entries in the publication database have been authored and co-authored
by a total of {{ metrics["author_count"] }} unique author names.
We define the author name at "last name, first initial".
Slight variations in the spelling may increase the number of unique names,
while common names with the same first initial may result in undercounting.

[![Number of papers and unique authors over time](/images/kpub/kpub-author-count.png)](/images/kpub/kpub-author-count.png)

<hr/>

## Most-cited publications

{{ institution }} publications have cumulatively 
been cited {{ metrics["citation_count"] }} times.
The list below shows the most-cited publications, based on the citation count obtained from NASA ADS.

{% for art in most_cited %}
{{loop.index}}. {{art['title'][0].upper()}}  
{{ ', '.join(art['author'][0:3]) }}{% if art['author']|length > 3 %}, et al.{% endif %}    
{{ '[{bibcode}](http://adsabs.harvard.edu/abs/{bibcode})'.format(**art) }}
<span class="badge">{{ art['citation_count'] }} citations</span>
{% endfor -%}

<hr/>


## Most-active authors

Below we list the most-active authors, defined as those with six or more first-author publications in our database.

{% for author in most_active_first_authors %}
 * {{author[0]}} ({{ "%.0f"|format(author[1]) }} publications)
{% endfor -%}

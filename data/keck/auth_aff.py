import sqlite3 as sql
import json
from pprint import pprint
import re
import pandas as pd

#Affiliation categorie types with search strings to identify.  "other" is default cat
#NOTE: If all caps, then search is case-sensitive.
affdefs = [
    {
        "type": "keck",
        "strings": [
            "keck",
            "WMKO",
            "California Institute of Technology",
            "Caltech",
            "CIT",
            "University of California",
            #"UCB", #This matches UCB (U Colorado at Boulder)
            "UCD",
            "UCI",
            "UCLA",
            "UCR",
            "UCSB",
            "UCSC",
            "UCSD",
            "USRA",
            "University of Hawaii",
            "University of Hawai'i",
            "University of Hawai`i",
            "University of Hawai‘i",
            "Manoa",
            "ANU",
            "Australian National University",
            "Northwestern",
            "Swinburne",
            "Yale",
            "JPL",
            "Jet Propulsion Laboratory",
        ]
    },
    {
        "type": "usa",
        "strings": [
            "USA",
            "United States of America",
            "NASA",
            "National Aeronautics and Space Administration",
        ]
    },
]


def main():

    con = sql.connect('/Users/joshriley/.kpub.db')

    df = pd.read_csv('SciencePaperBiblio.csv', sep=',', quotechar='"')
    df = df.fillna('')
    for idx, row in df.iterrows():
        bibcode = row['BibCode']
        if not bibcode:
            continue

        aff1 = row['AUaff1'].strip()
        aff2 = row['AUaff2'].strip()
        aff3 = row['AUaff3'].strip()

        aff1 = aff1[0] if len(aff1) > 0 and aff1[0].isdigit() else None
        aff2 = aff2[0] if len(aff2) > 0 and aff2[0].isdigit() else None
        aff3 = aff3[0] if len(aff3) > 0 and aff3[0].isdigit() else None

        if not aff1:
            #print("Skipping", bibcode)
            continue

        cur = con.execute(f"SELECT id, bibcode, metrics from pubs where bibcode='{bibcode}'")
        pub = cur.fetchone()
        if not pub:
            #print(f"ERROR could not find {bibcode}")
            continue

        raw = json.loads(pub[2])
        num_affs = len(raw['aff'])
        affs = []
        for i in range(0,3):
            aff = ''
            if num_affs > i:
                aff = get_aff(raw['aff'][i], affdefs)
            affs.append(aff)

        #print(affs, aff1, aff2, aff3)
        affmap = {'1':'keck', '2':'usa', '3':'other', None:''}
        aff1 = affmap[aff1]
        aff2 = affmap[aff2]
        aff3 = affmap[aff3]

        if affs[0] == aff1 and affs[1] == aff2 and affs[2] == aff3:
            continue
        else:
            print("\n" + bibcode)
            if affs[0] != aff1:
                print(f"\tAff1 {affs[0]} != {aff1}\n\t{raw['aff'][0]}\n\t{row['AUaff1']}")
            if affs[1] != aff2:
                print(f"\tAff2 {affs[1]} != {aff2}\n\t{raw['aff'][1]}\n\t{row['AUaff2']}")
            if affs[2] != aff3:
                print(f"\tAff3 {affs[2]} != {aff3}\n\t{raw['aff'][2]}\n\t{row['AUaff3']}")

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
        #print("\t", afftype)
        for string in affdef['strings']:
            #print("\t\t", string)
            for aff in affs:
                #print("\t\t\t", aff)
                if string.isupper():
                    if re.search(string, aff):
                        #print("====>", afftype)
                        return afftype
                else:
                    if re.search(string, aff, re.IGNORECASE):
                        #print("====>", afftype)
                        return afftype                  
    #print("====> other")
    return "other"


if __name__ == "__main__":
    main()
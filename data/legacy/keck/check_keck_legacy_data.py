import pandas as pd
from pprint import pprint

df = pd.read_csv('SciencePaperBiblio.csv', sep=',', quotechar='"')
df = df.fillna('')
newdata = []
instruments = {}
for idx, row in df.iterrows():
	bibcode = row['BibCode']
	if not bibcode:
		continue

	instrs = row['Instru']
	instrs = instrs.split('|')
	for instr in instrs:
		if instr not in instruments:
			instruments[instr] = 0
		instruments[instr] += 1

pprint(instruments)
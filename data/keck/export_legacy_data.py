import pandas as pd


df = pd.read_csv('SciencePaperBiblio.csv', sep=',', quotechar='"')
df = df.fillna('')
newdata = []
for idx, row in df.iterrows():
	bibcode = row['BibCode']

	if not bibcode:
		continue

	tac = row['TAC'].upper()
	archive = 1 if 'KOA' in tac else 0

	data = {
		'bibcode':bibcode, 
		'mission':'keck', 
		'science':'', 
		'instruments':row['Instru'],
		'archive':archive
	}
	newdata.insert(0, data)

#write out all for use with kpub import 
#TODO: include instruments?
newdf = pd.DataFrame(newdata)
newdf.to_csv('keck_import.csv', sep=',', index=False, header=False)

import pandas as pd


df = pd.read_csv('SciencePaperBiblio.csv', sep=',', quotechar='"')
df = df.fillna('')
newdata = []
for idx, row in df.iterrows():
	bibcode = row['BibCode']
	if not bibcode:
		continue
	data = {'bibcode':bibcode, 'mission':'keck', 'science':''}
	newdata.insert(0, data)

#write out all for use with kpub import 
#TODO: include instruments?
newdf = pd.DataFrame(newdata)
newdf.to_csv('keck_import.csv', sep=',', index=False, header=False)

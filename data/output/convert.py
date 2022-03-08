import markdown

with open('kpub-keck-publications.md','r') as f:
   text = f.read()
   html = markdown.markdown(text)

with open ('kpub-keck-publications.html','w') as f:
   f.write(html)

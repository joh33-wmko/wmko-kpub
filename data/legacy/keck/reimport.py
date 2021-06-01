import sqlite3 as sql
import db_conn
import yaml
import json

config = yaml.load(open(f'config/config.live.yaml'), Loader=yaml.FullLoader)
db = db_conn.db_conn(config['DATABASE'], persist=True)

con = sql.connect('../data/kpub.db')
rows = con.execute('SELECT id, bibcode, year, month, date, mission, science, instruments, archive, metrics from pubs order by bibcode asc').fetchall()
for row in rows:
    metrics = json.loads(row[9])
    month = int(row[3][-2:])
    year = int(row[2])
    archive = row[8]
    if not archive:
        archive = 0

    q = ("insert into pubs set"
        f" id=%s, bibcode=%s, year=%s, month=%s, date=%s, "
        f" mission=%s, science=%s, instruments=%s, archive=%s, "
        f" metrics=%s "
        )
    vals = (
        row[0], row[1], year, month, row[4], row[5], row[6], row[7], archive, row[9]
        )
    res = db.query('kpub', q, vals)
    if not res:
        print('ERROR: ', q, vals)
    # else:
    #     print(row[1])


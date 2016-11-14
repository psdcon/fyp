import json
import sqlite3

db = sqlite3.connect('videos.db')
c = db.cursor()
vids = json.load(open('dictionary.json'))


for v in vids:

  ell = v['ellipses'] if 'ellipses' in v else v['ellipsoids']
  ctps = v['center_points'] if 'center_points' in v else v['centroids']

  query = "INSERT INTO `videos`(`id`,`name`,`user_id`,`level`,`trampoline`,`bounces`,`ellipses`,`center_points`) VALUES (NULL,'{}',0,'{}','{}','{}','{}','{}');"
  query = query.format(v['video_name'],v['level'],json.dumps(v['trampoline']),json.dumps(v['bounces']),json.dumps(ell),json.dumps(ctps))
  print query

  # keys = (timestamp,) + tuple(data[c] for c in columns)
  c.execute(query)

c.close()

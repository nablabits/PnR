SELECT
sum(strftime('%s',stopped)-strftime('%s', started)) as lenght,
date(started)
   FROM work
   WHERE date(started) >= '2018-01-01'
   AND project IN (19)
   group BY date(started)

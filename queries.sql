-- all Entries
SELECT work.id as 'id', project as 'project', project_name as 'name', details,
  date(started) as 'started', time(started) as 'hour', date(stopped) as 'stopped',
  strftime('%s',stopped)-strftime('%s', started) as lenght
  FROM work
  WHERE date(started) >= '2018-01-01'
  ORDER BY datetime(started) ASC

-- Pickup labels by projects
SELECT work.id, tag.name as 'tag'
  FROM work
  INNER JOIN work_tag ON work.id=work_id
  INNER JOIN tag ON tag.id=work_tag.tag_id
  WHERE date(started) >= '2018-01-01'
  ORDER BY work.id ASC

--Sum Times by tag
  SELECT tag.name as 'tag', sum(strftime('%s',stopped)-strftime('%s', started)) as lenght
    FROM work
    INNER JOIN work_tag ON work.id=work_id
    INNER JOIN tag ON tag.id=work_tag.tag_id
    WHERE date(started) >= '2018-01-01' AND tag.name='BuildUp'
    GROUP BY tag
    ORDER BY work.id ASC

-- Sum times by project
  SELECT project_name as 'project', sum(strftime('%s',stopped)-strftime('%s', started)) as lenght
    FROM work
    WHERE date(started) >= '2018-01-01'
    group BY project

-- Sum times per date (dates with no entry are not returned)
    SELECT
    sum(strftime('%s',stopped)-strftime('%s', started)) as lenght,
    date(started)
       FROM work
       WHERE date(started) >= '2018-01-01'
       AND project IN (19)
       group BY date(started)

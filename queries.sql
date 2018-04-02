-- all Entries
SELECT work.id as 'id', project as 'project', project_name as 'name',
date(started) as 'started', time(started) as 'hour', date(stopped) as 'stopped',
strftime('%s',stopped)-strftime('%s', started) as lenght
FROM work
WHERE date(started) >= '2018-01-01'
ORDER BY datetime(started) ASC

-- Pickup labels by projects
SELECT work.id, started, stopped, work_tag.tag_id, tag.name
FROM work
INNER JOIN work_tag ON work.id=work_id
INNER JOIN tag ON tag.id=work_tag.tag_id
WHERE date(started) >= '2018-01-01'
ORDER BY work.id ASC

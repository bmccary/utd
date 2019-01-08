
CREATE TABLE IF NOT EXISTS "netid"
(
    id INTEGER PRIMARY KEY
    , netid TEXT NOT NULL UNIQUE ON CONFLICT IGNORE
    , last_name   TEXT NOT NULL
    , middle_name TEXT NOT NULL
    , first_name  TEXT NOT NULL
    
    , CHECK (typeof(netid) = 'text' AND length(netid) > 0)
    , CHECK (typeof(last_name) = 'text' AND length(last_name) > 0)
    , CHECK (typeof(middle_name) = 'text')
    , CHECK (typeof(first_name) = 'text' AND length(first_name) > 0)
);



--



CREATE TABLE IF NOT EXISTS "term"
(
    id INTEGER PRIMARY KEY
    , term TEXT NOT NULL UNIQUE
    , date0 TEXT
    , date1 TEXT
    , CHECK 
    (
        (typeof(term) = 'text')
        AND 
        (term = lower(term))
        AND 
        (length(term) = 4)
        AND 
        (substr(term, 1, 1) = '2')
        AND
        (cast(substr(term, 2, 2) AS INTEGER) BETWEEN 0 AND 99)
        AND
        (substr(term, 4, 1) IN ('2', '5', '8'))
    )
    , CHECK
    (
        (typeof(date0) IN ('null', 'text')) 
        AND 
        (typeof(date0) = typeof(date1))
    )
    , CHECK 
    (
        (date0 IS NULL)
        OR
        (
            (substr(strftime('%Y', date0), 3, 2) = substr(term, 2, 2))
            AND
            (
                CASE substr(term, 4, 1)
                    WHEN '2' THEN strftime('%m-%d', date0) BETWEEN '01-01' AND '02-01'
                    WHEN '5' THEN strftime('%m-%d', date0) BETWEEN '05-10' AND '06-10'
                    WHEN '8' THEN strftime('%m-%d', date0) BETWEEN '08-10' AND '09-10'
                    ELSE FALSE
                END
            )
        )
    )
    , CHECK 
    (
        (date1 IS NULL)
        OR
        (
            (substr(strftime('%Y', date1), 3, 2) = substr(term, 2, 2))
            AND
            (
                CASE substr(term, 4, 1)
                    WHEN '2' THEN strftime('%m-%d', date1) BETWEEN '05-01' AND '06-01'
                    WHEN '5' THEN strftime('%m-%d', date1) BETWEEN '07-20' AND '08-20'
                    WHEN '8' THEN strftime('%m-%d', date1) BETWEEN '12-01' AND '12-23'
                    ELSE FALSE
                END
            )
        )
    )
);

--

CREATE VIEW IF NOT EXISTS "term*" AS
    WITH
        T (id, term, date0, date1, YYYY, L) AS
        (
            SELECT
                *,
                '20' || substr(term, 2, 2) AS YYYY,
                substr(term, 4, 1) AS L
            FROM term
        )
    SELECT
        T.id
        , T.term
        , 
        coalesce(T.date0,
            (
                T.YYYY || '-' ||
                CASE T.L
                    WHEN '2' THEN '01-10'
                    WHEN '5' THEN '05-20'
                    ELSE          '08-20'
                END
            )
        ) AS date0
        , 
        coalesce(T.date1,
            (
                T.YYYY || '-' ||
                CASE T.L
                    WHEN '2' THEN '01-20'
                    WHEN '5' THEN '06-10'
                    ELSE          '09-10'
                END
            )
        ) AS date1
        , (T.date0 IS NULL) AS "default"
        , substr(T.YYYY, 3, 2) ||
        CASE T.L
            WHEN '2' THEN 's'
            WHEN '5' THEN 'u'
            ELSE          'f'
        END AS cb
    FROM T
    ;

--

CREATE VIEW IF NOT EXISTS "term default" AS
    WITH RECURSIVE
        Y (yy) AS
        (
            SELECT 5
            UNION ALL
            SELECT yy + 1 FROM Y WHERE yy < 30
        ),

        L (x) AS
        (
            SELECT '2'
            UNION ALL
            SELECT '5'
            UNION ALL
            SELECT '8'
        )
    SELECT 
        '2' || printf('%02d', yy) || x AS term
    FROM Y 
    JOIN L
    ORDER BY term
    ;

--

CREATE VIEW IF NOT EXISTS "term known" AS
    SELECT '2172', '2017-01-09', '2017-05-11'
    UNION
    SELECT '2175', '2017-05-30', '2017-08-16'
    UNION
    SELECT '2178', '2017-08-21', '2017-12-21'
    UNION
    SELECT '2182', '2018-01-08', '2018-05-10'
    UNION
    SELECT '2185', '2018-05-21', '2018-08-08'
    UNION
    SELECT '2188', '2018-08-20', '2018-12-18'
    UNION
    SELECT '2192', '2019-01-14', '2019-05-15'
    UNION
    SELECT '2195', '2019-05-23', '2019-08-12'
    UNION
    SELECT '2198', '2019-08-19', '2019-12-18'
    ;

INSERT INTO term (term)               SELECT * FROM "term default" WHERE TRUE ON CONFLICT (term) DO NOTHING;
INSERT INTO term (term, date0, date1) SELECT * FROM "term known"   WHERE TRUE ON CONFLICT (term) DO UPDATE SET date0 = EXCLUDED.date0, date1 = EXCLUDED.date1;



--



CREATE TABLE IF NOT EXISTS "prefix"
(
    id INTEGER PRIMARY KEY
    , prefix TEXT NOT NULL
    , CHECK ((typeof(prefix) = 'text') AND (prefix = lower(prefix)) AND (length(prefix) > 0))
    , UNIQUE (prefix) ON CONFLICT IGNORE
);
CREATE TRIGGER IF NOT EXISTS "prefix U" BEFORE UPDATE OF "prefix" ON "prefix" BEGIN SELECT RAISE(ABORT, 'prefix.prefix: update undefined.'); END;

INSERT OR IGNORE INTO "prefix" (prefix) VALUES ('math');
INSERT OR IGNORE INTO "prefix" (prefix) VALUES ('stat');
INSERT OR IGNORE INTO "prefix" (prefix) VALUES ('acts');
INSERT OR IGNORE INTO "prefix" (prefix) VALUES ('cs');
INSERT OR IGNORE INTO "prefix" (prefix) VALUES ('phys');



--



CREATE TABLE IF NOT EXISTS "course"
(
    id INTEGER PRIMARY KEY
    
    , "prefix/id" INTEGER NOT NULL REFERENCES "prefix" (id) ON UPDATE CASCADE ON DELETE RESTRICT
    , number TEXT NOT NULL
    , title TEXT
    
    , CHECK ((typeof(number) = 'text') AND (number = lower(number)) AND (length(number) = 4))
    , CHECK ((title IS NULL) OR ((typeof(title) = 'text') AND (length(title) > 0)))
    , UNIQUE ("prefix/id", number)
);
CREATE TRIGGER IF NOT EXISTS "course U" BEFORE UPDATE OF "number" ON "course" BEGIN SELECT RAISE(ABORT, 'course.number: update undefined.'); END;

CREATE VIEW IF NOT EXISTS "course*" AS
    SELECT
        C.id
        , C."prefix/id"
        , P.prefix
        , C.number
        , C.title
    FROM "course" AS C
    JOIN "prefix" AS P ON P.id = C."prefix/id"
    ;
CREATE TRIGGER IF NOT EXISTS "course* I" INSTEAD OF INSERT ON "course*"
BEGIN
    SELECT RAISE(ABORT, 'Data/input error: Unknown prefix.') WHERE NOT EXISTS (SELECT id FROM "prefix" WHERE prefix = NEW.prefix LIMIT 1);

    INSERT INTO "course" ("prefix/id", number, title)
    VALUES ((SELECT id FROM "prefix" WHERE prefix = NEW.prefix LIMIT 1), NEW.number, NEW.title)
    ON CONFLICT ("prefix/id", number) DO 
    UPDATE SET title = EXCLUDED.title WHERE EXCLUDED.title IS NOT NULL
    ;
END;



--



CREATE TABLE IF NOT EXISTS "activity"
(
    id INTEGER PRIMARY KEY
    , activity TEXT UNIQUE ON CONFLICT IGNORE
    , CHECK ((activity IS NULL) OR ((typeof(activity) = 'text') AND (activity = lower(activity)) AND (length(activity) > 0)))
);
INSERT OR IGNORE INTO "activity" (activity) VALUES (NULL);
INSERT OR IGNORE INTO "activity" (activity) VALUES ('examination');
INSERT OR IGNORE INTO "activity" (activity) VALUES ('laboratory');
INSERT OR IGNORE INTO "activity" (activity) VALUES ('lecture');
INSERT OR IGNORE INTO "activity" (activity) VALUES ('independent study');



--



CREATE TABLE IF NOT EXISTS "section"
(
    id INTEGER PRIMARY KEY
    
    , "term/id"     INTEGER NOT NULL REFERENCES "term"     (id) ON UPDATE CASCADE ON DELETE CASCADE
    , "course/id"   INTEGER NOT NULL REFERENCES "course"   (id) ON UPDATE CASCADE ON DELETE CASCADE
    , section       TEXT    NOT NULL
    , "activity/id" INTEGER NOT NULL REFERENCES "activity" (id) ON UPDATE CASCADE ON DELETE CASCADE
   
    , CHECK ((typeof(section) = 'text') AND (section = lower(section)) AND (length(section) = 3))

    , UNIQUE ("term/id", "course/id", section)
);

CREATE VIEW IF NOT EXISTS "section*" AS
    SELECT
        S.id
        , T.term
        , P.prefix
        , C.number
        , S.section
        , A.activity
        , T.cb || '-' || P.prefix || '-' || C.number || '-' || S.section AS address
    FROM "section"  AS S
    JOIN "term*"    AS T ON T.id = S."term/id"
    JOIN "course"   AS C ON C.id = S."course/id"
    JOIN "prefix"   AS P ON P.id = C."prefix/id"
    JOIN "activity" AS A ON A.id = S."activity/id"
    ;
CREATE TRIGGER IF NOT EXISTS "section* I" INSTEAD OF INSERT ON "section*"
BEGIN
    SELECT
        CASE
            WHEN NOT EXISTS (SELECT id FROM "term"     WHERE term             = NEW.term                 LIMIT 1) THEN RAISE(ABORT, 'Data/input error: Unknown term.') 
            WHEN NOT EXISTS (SELECT id FROM "course*"  WHERE (prefix, number) = (NEW.prefix, NEW.number) LIMIT 1) THEN RAISE(ABORT, 'Data/input error: Unknown (prefix, number).') 
            WHEN NOT EXISTS (SELECT id FROM "activity" WHERE activity IS NEW.activity                    LIMIT 1) THEN RAISE(ABORT, 'Data/input error: Unknown activity.') 
            ELSE NULL
        END
    ;

    INSERT INTO "section" ("term/id", "course/id", section, "activity/id")
    VALUES 
    (
        (SELECT id FROM "term" WHERE term = NEW.term LIMIT 1)
        , (SELECT id FROM "course*" WHERE (prefix, number) = (NEW.prefix, NEW.number) LIMIT 1)
        , NEW.section
        , (SELECT id FROM "activity" WHERE activity IS NEW.activity LIMIT 1)
    )
    ON CONFLICT ("term/id", "course/id", section) DO 
    NOTHING
    ;

END;



--



CREATE TABLE IF NOT EXISTS "student+section"
(
    id INTEGER PRIMARY KEY
    
    , "netid/id"   INTEGER NOT NULL REFERENCES "netid"   (id) ON UPDATE CASCADE ON DELETE CASCADE
    , "section/id" INTEGER NOT NULL REFERENCES "section" (id) ON UPDATE CASCADE ON DELETE CASCADE
    , UNIQUE ("netid/id", "section/id")
);

CREATE VIEW IF NOT EXISTS "student+section*" AS
    SELECT
        T.id
        , N.netid
        , N.last_name
        , N.middle_name
        , N.first_name
        , C.term
        , C.prefix
        , C.number
        , C.section
        , C.activity
        , C.address
    FROM "student+section" AS T
    JOIN "netid"           AS N ON N.id = T."netid/id"
    JOIN "section*"        AS C ON C.id = T."section/id"
    ;
CREATE TRIGGER IF NOT EXISTS "student+section* I" INSTEAD OF INSERT ON "student+section*"
BEGIN
    SELECT
        CASE
            WHEN NOT EXISTS (SELECT id FROM "netid"    WHERE netid = NEW.netid)                                                                         THEN RAISE(ABORT, 'Data/input error: Unknown netid.') 
            WHEN NOT EXISTS (SELECT id FROM "section*" WHERE (term, prefix, number, section) = (NEW.term, NEW.prefix, NEW.number, NEW.section) LIMIT 1) THEN RAISE(ABORT, 'Data/input error: Unknown (term, prefix, number, section).') 
            ELSE NULL
        END
    ;

    INSERT INTO "student+section" ("netid/id", "section/id")
    VALUES 
    (
        (SELECT id FROM "netid" WHERE netid = NEW.netid LIMIT 1)
        , (SELECT id FROM "section*" WHERE (term, prefix, number, section) = (NEW.term, NEW.prefix, NEW.number, NEW.section) LIMIT 1)
    )
    ON CONFLICT DO
    NOTHING
    ;

END;




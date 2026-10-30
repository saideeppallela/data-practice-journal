-- Day 1: Drivers Problem


CREATE TABLE dbo.Day1_Drivers
(
    DRIVER1 VARCHAR(20),
    DRIVER2 VARCHAR(20)
);

INSERT INTO dbo.Day1_Drivers (DRIVER1, DRIVER2)
VALUES
    ('Charles', 'Norris'),
    ('Sainz',   'Max'),
    ('Max',     'Piastri'),
    ('Lewis',   'Russel'),
    ('Alonso',  'Alonso'),
    ('Vettel',  'Senna'),
    ('Russel',  'Michael');

-- Verify the input data
select * FROM dbo.Day1_Drivers


SELECT D1.DRIVER1 , D2.DRIVER2
FROM dbo.Day1_Drivers AS D1
FULL JOIN dbo.Day1_Drivers AS D2
ON D1.DRIVER1 = D2.DRIVER2


/*
========================================================
Day 01: Drivers Problem
Database: SQL Server
Concept: FULL JOIN / Self-Join
========================================================

Problem:
Match DRIVER1 names with DRIVER2 names.
Retain unmatched names from both sides.

*/

-- =========================================
-- 1. CREATE AND POPULATE THE INPUT TABLE
-- =========================================

CREATE TABLE dbo.Day1_Drivers
(
    DRIVER1 VARCHAR(20),
    DRIVER2 VARCHAR(20)
);

INSERT INTO dbo.Day1_Drivers (DRIVER1, DRIVER2)
VALUES
    ('Charles', 'Norris'),
    ('Sainz',   'Max'),
    ('Max',     'Piastri'),
    ('Lewis',   'Russel'),
    ('Alonso',  'Alonso'),
    ('Vettel',  'Senna'),
    ('Russel',  'Michael');


-- =========================================
-- 2. VERIFY INPUT DATA
-- =========================================

SELECT *
FROM dbo.Day1_Drivers;


-- =========================================
-- 3. SOLUTION: FULL JOIN
-- =========================================

SELECT
    D1.DRIVER1,
    D2.DRIVER2
FROM dbo.Day1_Drivers AS D1
FULL JOIN dbo.Day1_Drivers AS D2
    ON D1.DRIVER1 = D2.DRIVER2;

-- 原文 2.1
SELECT *
FROM (
  VALUES (1, 'Alice', 'Sales', 5000),
   (2, 'Bob', 'Tech', 7000)
) t(id, name, dept, salary);

-- 原文 2.2
SELECT name, salary
FROM (
  VALUES (1, 'Alice', 5000),
   (2, 'Bob', 7000)
) t(id, name, salary);

-- 原文 2.3
VALUES (1, 'Alice', 'Sales'), (2, 'Bob', 'Tech'), (3, 'Charlie', 'Sales');

-- 原文 2.4
SELECT x
FROM (
  VALUES (1),
   (2)
) AS t(x);

SELECT name, salary
FROM (
  VALUES (1, 'Alice', 'Sales', 5000),
   (2, 'Bob', 'Tech', 7000)
) t(id, name, dept, salary);

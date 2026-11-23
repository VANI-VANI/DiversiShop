-- DiversiShop DBMS Project: SQL Query Collection
-- Run using SQLite (sqlite3 diversishop.db < sql/queries.sql).
-- DDL is in schema.sql. Seed data is inserted by app.py on first run.

-- 1. View all products with brand and category (INNER JOIN)
SELECT p.product_id,p.product_name,b.brand_name,c.category_name,p.price,p.rating
FROM products p
INNER JOIN brands b ON p.brand_id=b.brand_id
INNER JOIN categories c ON p.category_id=c.category_id;

-- 2. Products within a budget (WHERE, ORDER BY)
SELECT product_name,price,rating FROM products
WHERE price <= 70000 ORDER BY rating DESC LIMIT 10;

-- 3. Average rating and product count per brand (GROUP BY, AVG, COUNT)
SELECT b.brand_name,COUNT(p.product_id) AS total_products,
ROUND(AVG(p.rating),2) AS average_rating
FROM brands b LEFT JOIN products p ON b.brand_id=p.brand_id
GROUP BY b.brand_id,b.brand_name ORDER BY average_rating DESC;

-- 4. Categories with at least 5 products (HAVING)
SELECT c.category_name,COUNT(*) AS product_count
FROM categories c JOIN products p ON c.category_id=p.category_id
GROUP BY c.category_id HAVING COUNT(*) >= 5;

-- 5. Products with rating above the overall average (subquery)
SELECT product_name,rating FROM products
WHERE rating > (SELECT AVG(rating) FROM products)
ORDER BY rating DESC;

-- 6. Products whose price is between the category average and 1.5x average (correlated subquery)
SELECT p.product_name,p.price,c.category_name
FROM products p JOIN categories c ON p.category_id=c.category_id
WHERE p.price <= 1.5 * (SELECT AVG(p2.price) FROM products p2
                         WHERE p2.category_id=p.category_id);

-- 7. Top 3 products in each category (window function)
SELECT * FROM (
  SELECT c.category_name,p.product_name,p.rating,
         ROW_NUMBER() OVER(PARTITION BY c.category_id ORDER BY p.rating DESC,p.popularity DESC) AS rn
  FROM products p JOIN categories c ON p.category_id=c.category_id
) ranked WHERE rn <= 3;

-- 8. Brands with no products (LEFT JOIN / NULL)
SELECT b.brand_name FROM brands b
LEFT JOIN products p ON b.brand_id=p.brand_id
WHERE p.product_id IS NULL;

-- 9. Set operation: products with rating >= 4.5 OR price <= 25000
SELECT product_id,product_name FROM products WHERE rating >= 4.5
UNION
SELECT product_id,product_name FROM products WHERE price <= 25000;

-- 10. EXISTS: brands having at least one product rated >= 4.8
SELECT b.brand_name FROM brands b
WHERE EXISTS (SELECT 1 FROM products p WHERE p.brand_id=b.brand_id AND p.rating>=4.8);

-- 11. Update product stock (DML)
-- UPDATE products SET stock=25 WHERE product_id=1;

-- 12. Insert a product (DML)
-- INSERT INTO products(product_name,brand_id,category_id,price,rating,popularity,stock)
-- VALUES ('Demo Laptop',1,1,59999,4.4,120,10);

-- 13. Delete a product (DML)
-- DELETE FROM products WHERE product_name='Demo Laptop';

-- 14. Create a transaction (TCL)
-- BEGIN;
-- UPDATE products SET stock=stock-1 WHERE product_id=1 AND stock>0;
-- COMMIT;
-- If an error occurs, use ROLLBACK;

-- 15. View definition
SELECT * FROM product_catalogue_view LIMIT 20;

-- 16. Indexes (performance)
-- CREATE INDEX idx_products_price_rating ON products(price,rating DESC);
-- EXPLAIN QUERY PLAN SELECT * FROM products WHERE price<50000 ORDER BY rating DESC;

-- 17. Recommendation run history
SELECT * FROM recommendation_runs ORDER BY created_at DESC;

-- 18. Product popularity by category
SELECT c.category_name,SUM(p.popularity) AS total_popularity
FROM categories c JOIN products p ON c.category_id=p.category_id
GROUP BY c.category_id ORDER BY total_popularity DESC;

-- 19. Low-stock products
SELECT product_name,stock FROM products WHERE stock<10 ORDER BY stock;

-- 20. Brand-wise price statistics
SELECT b.brand_name,MIN(p.price) min_price,MAX(p.price) max_price,
       ROUND(AVG(p.price),2) avg_price
FROM brands b JOIN products p ON b.brand_id=p.brand_id
GROUP BY b.brand_id ORDER BY avg_price;

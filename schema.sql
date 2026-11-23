PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS brands (
    brand_id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand_name TEXT NOT NULL UNIQUE,
    country TEXT
);

CREATE TABLE IF NOT EXISTS categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name TEXT NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT NOT NULL,
    brand_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    price REAL NOT NULL CHECK(price >= 0),
    rating REAL NOT NULL CHECK(rating BETWEEN 0 AND 5),
    popularity INTEGER NOT NULL DEFAULT 0 CHECK(popularity >= 0),
    stock INTEGER NOT NULL DEFAULT 0 CHECK(stock >= 0),
    description TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (brand_id) REFERENCES brands(brand_id),
    FOREIGN KEY (category_id) REFERENCES categories(category_id)
);

CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS searches (
    search_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    search_text TEXT NOT NULL,
    category_id INTEGER,
    max_price REAL,
    min_rating REAL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (category_id) REFERENCES categories(category_id)
);

CREATE TABLE IF NOT EXISTS recommendation_runs (
    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    search_text TEXT NOT NULL,
    top_k INTEGER NOT NULL,
    ranking_criterion TEXT NOT NULL,
    requirements_json TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS recommendation_items (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    final_rank INTEGER NOT NULL,
    FOREIGN KEY (run_id) REFERENCES recommendation_runs(run_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    UNIQUE(run_id, product_id),
    UNIQUE(run_id, final_rank)
);

CREATE INDEX IF NOT EXISTS idx_products_price ON products(price);
CREATE INDEX IF NOT EXISTS idx_products_rating ON products(rating DESC);
CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand_id);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_products_category_price ON products(category_id, price);

CREATE VIEW IF NOT EXISTS product_catalogue_view AS
SELECT p.product_id, p.product_name, b.brand_name, c.category_name,
       p.price, p.rating, p.popularity, p.stock
FROM products p
JOIN brands b ON p.brand_id=b.brand_id
JOIN categories c ON p.category_id=c.category_id;

CREATE TRIGGER IF NOT EXISTS prevent_negative_stock
BEFORE UPDATE OF stock ON products
WHEN NEW.stock < 0
BEGIN
    SELECT RAISE(ABORT, 'Stock cannot be negative');
END;

CREATE TRIGGER IF NOT EXISTS log_recommendation_insert
AFTER INSERT ON recommendation_items
BEGIN
    UPDATE products SET popularity = popularity + 1
    WHERE product_id = NEW.product_id;
END;

-- Seed reference tables
INSERT OR IGNORE INTO brands(brand_name,country) VALUES ('Lenovo', 'Various');
INSERT OR IGNORE INTO brands(brand_name,country) VALUES ('HP', 'Various');
INSERT OR IGNORE INTO brands(brand_name,country) VALUES ('Dell', 'Various');
INSERT OR IGNORE INTO brands(brand_name,country) VALUES ('Asus', 'Various');
INSERT OR IGNORE INTO brands(brand_name,country) VALUES ('Acer', 'Various');
INSERT OR IGNORE INTO brands(brand_name,country) VALUES ('Apple', 'Various');
INSERT OR IGNORE INTO brands(brand_name,country) VALUES ('MSI', 'Various');
INSERT OR IGNORE INTO brands(brand_name,country) VALUES ('Samsung', 'Various');
INSERT OR IGNORE INTO categories(category_name,description) VALUES ('Laptop', 'Consumer laptop products');
INSERT OR IGNORE INTO categories(category_name,description) VALUES ('Smartphone', 'Consumer smartphone products');
INSERT OR IGNORE INTO categories(category_name,description) VALUES ('Headphones', 'Consumer headphones products');
INSERT OR IGNORE INTO categories(category_name,description) VALUES ('Tablet', 'Consumer tablet products');

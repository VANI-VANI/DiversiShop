# DiversiShop – DBMS Project

A runnable Streamlit + SQLite application for diverse Top-K product recommendations.

## Features
- Relational database with products, brands, categories, users, searches, recommendation runs and recommendation items.
- Product catalogue with search and filters.
- Diverse Top-K recommendation interface.
- PuLP/CBC MILP model for selecting brand-specific price relaxations.
- SQL Query Lab (read-only SELECT).
- Reports using JOIN, GROUP BY, aggregate functions and subqueries.
- SQL scripts demonstrating DDL, DML, DQL, joins, views, indexes, triggers, transactions, subqueries, set operations and window functions.

## Run (Windows / macOS / Linux)
1. Install Python 3.10+.
2. Extract this ZIP.
3. Open a terminal in the extracted `diversishop_dbms` folder.
4. Install dependencies:
   `pip install -r requirements.txt`
5. Start the app:
   `streamlit run app.py`
6. Open the local address printed in the terminal (usually http://localhost:8501).

The SQLite database `diversishop.db` is created and seeded automatically on first run.

## Reset database
Stop Streamlit, delete `diversishop.db`, and run the app again. The database is recreated from `sql/schema.sql` and `data/products.csv`.

## DBMS viva topics covered
- Entities, attributes, primary keys and foreign keys
- 1:M relationships
- Referential integrity and CHECK constraints
- Joins, nested queries, correlated subqueries, EXISTS, UNION
- GROUP BY, HAVING and aggregate functions
- Views, indexes, triggers and transactions
- Query execution plan

## Important implementation scope
This is an educational project implementation, not a complete reproduction of the research paper's full general MILP formulation. Its MILP selects brand-specific price-cap relaxations from a discrete set. The app then checks whether the actual ranked Top-K output satisfies the requested brand minima; if not, it reports infeasibility rather than silently claiming success. The original ranking criterion is retained. Review the paper and describe this scoped implementation accurately in your report.

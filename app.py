import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
from optimizer import optimize_recommendations

BASE = Path(__file__).parent
DB_PATH = BASE / "diversishop.db"

st.set_page_config(page_title="DiversiShop | DBMS Project", page_icon="🛍️", layout="wide")

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_conn()
    schema = (BASE / "sql" / "schema.sql").read_text(encoding="utf-8")
    conn.executescript(schema)
    count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    if count == 0:
        df = pd.read_csv(BASE / "data" / "products.csv")
        for _, r in df.iterrows():
            conn.execute("""INSERT INTO products
                (product_name, brand_id, category_id, price, rating, popularity, stock, description)
                VALUES (?, (SELECT brand_id FROM brands WHERE brand_name=?),
                (SELECT category_id FROM categories WHERE category_name=?), ?, ?, ?, ?, ?)""",
                (r.product_name, r.brand, r.category, float(r.price), float(r.rating),
                 int(r.popularity), int(r.stock), r.description))
        conn.commit()
    conn.close()

def query_df(sql, params=()):
    conn = get_conn()
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df

init_db()

st.title("🛍️ DiversiShop")
st.caption("DBMS Project • Query Refinement for Diverse Top-K Product Recommendations")
with st.sidebar:
    st.header("Navigation")
    page = st.radio("Choose module", ["Dashboard", "Product Catalogue", "Diverse Recommendations",
                                      "SQL Query Lab", "Database Reports", "Project Guide"])
    st.divider()
    st.caption("SQLite database • Python • Streamlit • PuLP/CBC")

if page == "Dashboard":
    a,b,c,d = st.columns(4)
    a.metric("Products", int(query_df("SELECT COUNT(*) n FROM products").iloc[0,0]))
    b.metric("Brands", int(query_df("SELECT COUNT(*) n FROM brands").iloc[0,0]))
    c.metric("Categories", int(query_df("SELECT COUNT(*) n FROM categories").iloc[0,0]))
    d.metric("Average rating", round(float(query_df("SELECT AVG(rating) n FROM products").iloc[0,0]),2))
    st.subheader("Database overview")
    st.write("DiversiShop is a relational database-backed product recommendation system. It stores products, brands, categories, users, searches and recommendation runs.")
    st.subheader("Top-rated products")
    st.dataframe(query_df("""SELECT p.product_id, p.product_name, b.brand_name AS brand,
        c.category_name AS category, p.price, p.rating, p.popularity, p.stock
        FROM products p JOIN brands b ON p.brand_id=b.brand_id
        JOIN categories c ON p.category_id=c.category_id
        ORDER BY p.rating DESC, p.popularity DESC LIMIT 8"""), use_container_width=True)

elif page == "Product Catalogue":
    st.subheader("Product catalogue")
    left,right=st.columns([2,1])
    with left:
        search=st.text_input("Search product name", "")
    with right:
        cats=query_df("SELECT category_name FROM categories ORDER BY category_name")["category_name"].tolist()
        category=st.selectbox("Category", ["All"]+cats)
    brands=query_df("SELECT brand_name FROM brands ORDER BY brand_name")["brand_name"].tolist()
    selected_brands=st.multiselect("Brands", brands, default=[])
    min_price,max_price=st.slider("Price range (₹)", 0, 150000, (0,150000), step=1000)
    sql="""SELECT p.product_id,p.product_name,b.brand_name AS brand,c.category_name AS category,
           p.price,p.rating,p.popularity,p.stock,p.description
           FROM products p JOIN brands b ON p.brand_id=b.brand_id
           JOIN categories c ON p.category_id=c.category_id WHERE p.price BETWEEN ? AND ?"""
    params=[min_price,max_price]
    if search:
        sql += " AND p.product_name LIKE ?"
        params.append(f"%{search}%")
    if category!="All":
        sql += " AND c.category_name=?"
        params.append(category)
    if selected_brands:
        sql += " AND b.brand_name IN ("+",".join(["?"]*len(selected_brands))+")"
        params.extend(selected_brands)
    sql += " ORDER BY p.rating DESC,p.popularity DESC"
    df=query_df(sql,params)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption(f"{len(df)} matching products")

elif page == "Diverse Recommendations":
    st.subheader("Generate diverse Top-K recommendations")
    st.write("Choose an original search and minimum representation constraints. The optimizer selects a minimally changed set of brand-specific price thresholds; SQL then executes the refined query.")
    cats=query_df("SELECT category_name FROM categories ORDER BY category_name")["category_name"].tolist()
    brands=query_df("SELECT brand_name FROM brands ORDER BY brand_name")["brand_name"].tolist()
    c1,c2,c3=st.columns(3)
    with c1:
        category=st.selectbox("Product category", cats)
        max_price=st.number_input("Original maximum price (₹)", min_value=1000, max_value=200000, value=70000, step=1000)
    with c2:
        top_k=st.number_input("Top-K", min_value=2, max_value=30, value=10, step=1)
        min_rating=st.slider("Minimum rating", 1.0, 5.0, 3.5, 0.1)
    with c3:
        ranking=st.selectbox("Ranking criterion", ["rating", "popularity", "value_score"])
        deviation=st.selectbox("Maximum allowed price relaxation (₹)", [0,5000,10000,20000,30000], index=2)
    st.markdown("**Brand diversity requirements**")
    chosen=st.multiselect("Brands that must be represented", brands, default=brands[:3])
    reqs={}
    cols=st.columns(min(3,max(1,len(chosen))))
    for i,brand in enumerate(chosen):
        with cols[i%len(cols)]:
            reqs[brand]=st.number_input(f"Minimum {brand}", min_value=0, max_value=int(top_k), value=1, key=f"req_{brand}")
    if st.button("✨ Generate diverse recommendations", type="primary", use_container_width=True):
        if not chosen or sum(reqs.values())>top_k:
            st.error("Choose at least one brand and ensure the sum of minimum brand counts does not exceed Top-K.")
        else:
            conn=get_conn()
            products=pd.read_sql_query("""SELECT p.product_id,p.product_name,b.brand_name AS brand,
                c.category_name AS category,p.price,p.rating,p.popularity,p.stock
                FROM products p JOIN brands b ON p.brand_id=b.brand_id
                JOIN categories c ON p.category_id=c.category_id
                WHERE c.category_name=? AND p.rating>=? AND p.stock>0""",
                conn, params=(category,min_rating))
            conn.close()
            if ranking=="value_score":
                products["value_score"]=(products["rating"]*20)+(products["popularity"].rank(pct=True)*20)-(products["price"]/max_price*5)
            result=optimize_recommendations(products, max_price, int(top_k), reqs, int(deviation), ranking)
            if not result["success"]:
                st.error(result["message"])
            else:
                st.success(result["message"])
                # Persist this recommendation run and its ranked items in a DB transaction.
                import json
                conn=get_conn()
                try:
                    cur=conn.execute("""INSERT INTO recommendation_runs
                        (search_text,top_k,ranking_criterion,requirements_json,status)
                        VALUES (?,?,?,?,?)""",
                        (f"{category} under ₹{max_price}",int(top_k),ranking,json.dumps(reqs),"SUCCESS"))
                    run_id=cur.lastrowid
                    for rank, (_, item) in enumerate(result["results"].iterrows(), start=1):
                        conn.execute("""INSERT INTO recommendation_items(run_id,product_id,final_rank)
                            VALUES (?,?,?)""",(run_id,int(item["product_id"]),rank))
                    conn.commit()
                    st.caption(f"Saved recommendation run #{run_id} to the database.")
                except Exception:
                    conn.rollback()
                    st.warning("Recommendations were generated, but the run could not be saved to history.")
                finally:
                    conn.close()
                st.subheader("Refined Top-K result")
                st.dataframe(result["results"], use_container_width=True, hide_index=True)
                m1,m2,m3=st.columns(3)
                m1.metric("Products returned",len(result["results"]))
                m2.metric("Brands represented",result["results"]["brand"].nunique())
                m3.metric("Refined maximum price",f"₹{result['refined_cap']:,}")
                st.subheader("Brand distribution")
                st.bar_chart(result["results"]["brand"].value_counts())
                st.subheader("Query refinement")
                st.code(result["refined_sql"], language="sql")
                st.write("Selected price thresholds by brand:", result["brand_caps"])
                st.download_button("Download recommendations CSV", result["results"].to_csv(index=False),
                                   "diversishop_recommendations.csv","text/csv")
                st.info("This is an educational, constrained implementation. It optimizes brand-specific price relaxations and then executes the resulting SQL query. It is not a full reproduction of every model and distance function in the research paper.")

elif page == "SQL Query Lab":
    st.subheader("SQL Query Lab")
    examples={
    "All products with brand and category":"""SELECT p.product_id,p.product_name,b.brand_name,c.category_name,p.price,p.rating
FROM products p JOIN brands b ON p.brand_id=b.brand_id
JOIN categories c ON p.category_id=c.category_id ORDER BY p.rating DESC;""",
    "Products under ₹60,000":"""SELECT product_name, price, rating FROM products WHERE price < 60000 ORDER BY rating DESC;""",
    "Average rating by brand":"""SELECT b.brand_name, ROUND(AVG(p.rating),2) AS avg_rating, COUNT(*) AS product_count
FROM brands b JOIN products p ON b.brand_id=p.brand_id GROUP BY b.brand_name ORDER BY avg_rating DESC;""",
    "Top 5 products per category":"""SELECT * FROM (SELECT c.category_name,p.product_name,p.rating,
ROW_NUMBER() OVER(PARTITION BY c.category_id ORDER BY p.rating DESC) AS rn
FROM products p JOIN categories c ON p.category_id=c.category_id) WHERE rn<=5;""",
    "Products with low stock":"""SELECT product_name, stock FROM products WHERE stock < 10 ORDER BY stock;""",
    "Recommendation history":"""SELECT run_id, search_text, top_k, status, created_at FROM recommendation_runs ORDER BY created_at DESC;"""
    }
    choice=st.selectbox("Load an example query",list(examples))
    sql=st.text_area("SQL (read-only SELECT statements)",examples[choice],height=180)
    if st.button("Run SQL"):
        if not sql.strip().lower().startswith("select"):
            st.error("For safety, this lab only executes SELECT queries. Use the provided SQL files for schema and DML examples.")
        else:
            try:
                st.dataframe(query_df(sql),use_container_width=True)
            except Exception as e: st.error(str(e))

elif page == "Database Reports":
    st.subheader("DBMS reports and aggregate queries")
    tabs=st.tabs(["Brand report","Category report","Price bands","Stock report"])
    with tabs[0]:
        st.dataframe(query_df("""SELECT b.brand_name,COUNT(*) products,ROUND(AVG(p.rating),2) avg_rating,
        ROUND(AVG(p.price),0) avg_price FROM brands b JOIN products p ON b.brand_id=p.brand_id
        GROUP BY b.brand_id ORDER BY products DESC"""),use_container_width=True)
    with tabs[1]:
        st.dataframe(query_df("""SELECT c.category_name,COUNT(*) products,ROUND(AVG(p.rating),2) avg_rating,
        MIN(p.price) min_price,MAX(p.price) max_price FROM categories c JOIN products p
        ON c.category_id=p.category_id GROUP BY c.category_id ORDER BY products DESC"""),use_container_width=True)
    with tabs[2]:
        st.dataframe(query_df("""SELECT CASE WHEN price<25000 THEN 'Below ₹25k'
        WHEN price<50000 THEN '₹25k–₹50k' WHEN price<75000 THEN '₹50k–₹75k'
        ELSE '₹75k+' END price_band,COUNT(*) product_count,ROUND(AVG(rating),2) avg_rating
        FROM products GROUP BY price_band ORDER BY MIN(price)"""),use_container_width=True)
    with tabs[3]:
        st.dataframe(query_df("""SELECT product_name,stock FROM products WHERE stock<15 ORDER BY stock ASC"""),use_container_width=True)

elif page == "Project Guide":
    st.subheader("Project documentation")
    st.markdown("""
### Problem statement
Traditional Top-K product search can return highly similar or brand-concentrated results. DiversiShop lets a user specify minimum brand representation and uses constrained query refinement to produce a more varied result set.

### DBMS concepts demonstrated
- Relational schema, primary keys and foreign keys
- One-to-many relationships (brands/categories to products)
- SQL joins, filtering, sorting, grouping and aggregate functions
- Views, indexes and triggers
- Transactions and audit/history tables
- Parameterized SQL queries

### Run locally
1. Install Python 3.10 or later.
2. Open a terminal in this project folder.
3. Run `pip install -r requirements.txt`.
4. Run `streamlit run app.py`.
5. Open the local URL printed by Streamlit.

### Database
The SQLite database is created automatically from `sql/schema.sql` and seeded from `data/products.csv` on first run.
""")
    st.subheader("ER relationship summary")
    st.code("brands (1) ─── (many) products (many) ─── (1) categories\\nusers (1) ─── (many) searches\\nusers (1) ─── (many) recommendation_runs\\nrecommendation_runs (1) ─── (many) recommendation_items", language="text")

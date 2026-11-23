import pandas as pd

def optimize_recommendations(products, original_cap, top_k, requirements, max_relaxation, ranking):
    """
    Educational MILP query-refinement model:
    choose one allowed price-cap level per required brand, minimizing total
    price-cap relaxation, subject to each brand having enough eligible products.
    The refined SQL is then executed by the app against the relational database.
    """
    try:
        import pulp
    except ImportError:
        return {"success":False,"message":"PuLP is not installed. Run: pip install -r requirements.txt"}
    if products.empty:
        return {"success":False,"message":"No in-stock products match the selected category and minimum rating."}
    levels=sorted(set([0, max_relaxation//4, max_relaxation//2, (3*max_relaxation)//4, max_relaxation]))
    levels=sorted(set(int(x) for x in levels))
    model=pulp.LpProblem("DiversiShop_Query_Refinement",pulp.LpMinimize)
    choices={}
    for brand,minimum in requirements.items():
        if minimum<=0: continue
        for level in levels:
            choices[(brand,level)]=pulp.LpVariable(f"choose_{len(choices)}",cat="Binary")
        model += pulp.lpSum(choices[(brand,l)] for l in levels)==1
        # At the selected brand-specific cap, at least the required number must qualify.
        for level in levels:
            available=int(((products.brand==brand)&(products.price<=original_cap+level)).sum())
            # Big-M implication: if level is selected, availability must meet requirement.
            model += available + top_k*(1-choices[(brand,level)]) >= int(minimum)
    model += pulp.lpSum(level*choices[(brand,level)] for brand,minimum in requirements.items()
                        if minimum>0 for level in levels)
    status=model.solve(pulp.PULP_CBC_CMD(msg=False))
    if pulp.LpStatus[status]!="Optimal":
        return {"success":False,"message":"No feasible refinement found within the allowed price relaxation. Increase the relaxation or reduce minimum brand counts."}
    brand_caps={}
    for brand,minimum in requirements.items():
        if minimum<=0: continue
        chosen=next(l for l in levels if pulp.value(choices[(brand,l)])>0.5)
        brand_caps[brand]=int(original_cap+chosen)
    # Query refinement is represented as brand-specific price predicates.
    # Products from required brands use their optimized caps; other brands retain original cap.
    conditions=[]
    params=[]
    for brand,cap in brand_caps.items():
        conditions.append("(b.brand_name=? AND p.price<=?)")
        params.extend([brand,cap])
    other_exclusion=",".join(["?"]*len(brand_caps))
    if brand_caps:
        conditions.append(f"(b.brand_name NOT IN ({other_exclusion}) AND p.price<=?)")
        params.extend(list(brand_caps.keys()))
        params.append(int(original_cap))
    else:
        conditions.append("(p.price<=?)"); params.append(int(original_cap))
    where=" OR ".join(conditions)
    order_col=ranking if ranking in ("rating","popularity","value_score") else "rating"
    # The app computes value_score on the returned frame; SQL uses rating/popularity for DB ordering.
    sql=f"""SELECT p.product_id,p.product_name,b.brand_name AS brand,c.category_name AS category,
    p.price,p.rating,p.popularity,p.stock FROM products p
    JOIN brands b ON p.brand_id=b.brand_id JOIN categories c ON p.category_id=c.category_id
    WHERE c.category_name=? AND p.rating>=? AND p.stock>0 AND ({where})
    ORDER BY p.{order_col if order_col!='value_score' else 'rating'} DESC,p.popularity DESC
    LIMIT {int(top_k)}"""
    # Reorder parameters to match category/rating before WHERE placeholders.
    sql_params=[products.iloc[0]["category"], float(products["rating"].min())]+params
    # Candidate result frame follows same predicates; this avoids DB round-trip and uses SQL-equivalent filtering.
    mask=pd.Series(False,index=products.index)
    for brand,cap in brand_caps.items():
        mask |= (products.brand==brand)&(products.price<=cap)
    mask |= (~products.brand.isin(list(brand_caps.keys())))&(products.price<=original_cap)
    candidates=products[mask].copy()
    if ranking=="value_score" and "value_score" in candidates:
        candidates=candidates.sort_values(["value_score","popularity"],ascending=False)
    else:
        candidates=candidates.sort_values([ranking,"popularity"],ascending=False)
    results=candidates.head(int(top_k)).copy()
    # Check actual Top-K outcome constraints, not just candidate availability.
    counts=results.brand.value_counts().to_dict()
    failed={b:n for b,n in requirements.items() if n>0 and counts.get(b,0)<n}
    if failed:
        return {"success":False,"message":"The refined query has enough eligible candidates, but the ranked Top-K output does not satisfy every minimum. Try a larger price relaxation, a lower minimum rating, or smaller group minimums."}
    return {"success":True,"message":"A feasible refined query was found and its Top-K results satisfy the requested brand constraints.",
            "results":results,"refined_cap":max(brand_caps.values()) if brand_caps else int(original_cap),
            "brand_caps":brand_caps,"refined_sql":sql}

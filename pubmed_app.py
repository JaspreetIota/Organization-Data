import streamlit as st
import asyncio
import aiohttp
import requests
import yfinance as yf
import pandas as pd
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
import random
import time

# -------------------------
# GLOBAL SETTINGS
# -------------------------
CACHE = {}
HEADERS = {"User-Agent": "Free-Company-Intelligence/1.0"}
SEMAPHORE = asyncio.Semaphore(5)  # Limit concurrent async requests
MAX_RETRIES = 5

# -------------------------
# HELPER FUNCTIONS
# -------------------------
def normalize_name(name):
    name = name.lower()
    name = re.sub(r"(ltd|limited|inc|corp|llc|pvt|plc)", "", name)
    return re.sub(r"\s+", " ", name).strip().title()

def run_async(coro):
    """Safe async runner for Streamlit"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        return asyncio.create_task(coro)
    else:
        return asyncio.run(coro)

async def fetch_with_retry(session, url, params=None, headers=None):
    """Async GET with retries and backoff"""
    for attempt in range(1, MAX_RETRIES + 1):
        async with SEMAPHORE:
            try:
                async with session.get(url, params=params, headers=headers, timeout=20) as r:
                    if r.status == 429:
                        wait = 2 ** attempt + random.random()
                        await asyncio.sleep(wait)
                        continue
                    r.raise_for_status()
                    try:
                        return await r.json()
                    except:
                        return await r.text()
            except:
                wait = 2 ** attempt + random.random()
                await asyncio.sleep(wait)
    return {}

# -------------------------
# OPEN CORPORATES
# -------------------------
async def fetch_opencorporates(session, name):
    key = f"oc:{name}"
    if key in CACHE:
        return CACHE[key]
    url = "https://api.opencorporates.com/v0.4/companies/search"
    resp = await fetch_with_retry(session, url, params={"q": name})
    companies = resp.get("results", {}).get("companies", []) if isinstance(resp, dict) else []
    if not companies:
        return {}
    c = companies[0]["company"]
    result = {
        "company_type": c.get("company_type"),
        "jurisdiction": c.get("jurisdiction_code"),
        "incorporation_date": c.get("incorporation_date"),
        "company_status": c.get("current_status"),
        "cin": c.get("company_number"),
        "registry_url": c.get("registry_url")
    }
    CACHE[key] = result
    return result

# -------------------------
# WIKIDATA
# -------------------------
def fetch_wikidata(name):
    key = f"wd:{name}"
    if key in CACHE:
        return CACHE[key]
    try:
        search = requests.get(
            "https://www.wikidata.org/w/api.php",
            params={
                "action": "wbsearchentities",
                "search": name,
                "language": "en",
                "format": "json",
                "limit": 1
            },
            headers=HEADERS,
            timeout=10
        ).json()
        if not search.get("search"):
            return {}
        entity_id = search["search"][0]["id"]
        entity = requests.get(
            f"https://www.wikidata.org/wiki/Special:EntityData/{entity_id}.json",
            headers=HEADERS,
            timeout=10
        ).json()
        claims = entity["entities"][entity_id]["claims"]
        def claim(pid):
            try:
                val = claims[pid][0]["mainsnak"]["datavalue"]["value"]
                if isinstance(val, dict) and "time" in val:
                    return val["time"][1:5]
                return val
            except:
                return None
        result = {
            "website": claim("P856"),
            "founding_year": claim("P571"),
            "headquarters": claim("P159")
        }
        CACHE[key] = result
        return result
    except:
        return {}

# -------------------------
# WIKIPEDIA
# -------------------------
async def fetch_wikipedia(session, name):
    key = f"wiki:{name}"
    if key in CACHE:
        return CACHE[key]
    url = f"https://en.wikipedia.org/wiki/{name.replace(' ', '_')}"
    resp = await fetch_with_retry(session, url)
    result = {}
    if resp:
        soup = BeautifulSoup(resp if isinstance(resp, str) else "", "html.parser")
        infobox = soup.select_one(".infobox")
        if infobox:
            for row in infobox.select("tr"):
                h, d = row.find("th"), row.find("td")
                if not h or not d:
                    continue
                if "Founded" in h.text:
                    yrs = re.findall(r"\d{4}", d.text)
                    if yrs:
                        result["founding_year"] = yrs[0]
                if "Headquarters" in h.text:
                    result["headquarters"] = d.text.strip()
    CACHE[key] = result
    return result

# -------------------------
# YAHOO FINANCE (Optional / Batched)
# -------------------------
def fetch_yfinance(name, retries=5):
    key = f"yf:{name}"
    if key in CACHE:
        return CACHE[key]
    for attempt in range(retries):
        try:
            t = yf.Ticker(name)
            i = t.info
            result = {
                "annual_revenue": i.get("totalRevenue"),
                "market_cap": i.get("marketCap"),
                "industry": i.get("industry"),
                "country": i.get("country"),
                "is_public": i.get("quoteType") == "EQUITY"
            }
            CACHE[key] = result
            time.sleep(random.uniform(1,2))  # small delay to reduce 429
            return result
        except:
            time.sleep(2 ** attempt + random.random())
    return {}

# -------------------------
# GAP-FILL MERGE
# -------------------------
def merge(base, incoming):
    for k, v in incoming.items():
        if not base.get(k):
            base[k] = v
    return base

# -------------------------
# ENRICH COMPANY
# -------------------------
async def enrich_company(name, fetch_yf=False):
    await asyncio.sleep(random.uniform(0.05,0.2))
    name = normalize_name(name)
    result = {"company_name": name}
    async with aiohttp.ClientSession() as session:
        result = merge(result, await fetch_opencorporates(session, name))
        result = merge(result, fetch_wikidata(name))
        result = merge(result, await fetch_wikipedia(session, name))
        if fetch_yf:
            result = merge(result, fetch_yfinance(name))
    return result

async def enrich_all(companies, batch_size=20, fetch_yf=False):
    enriched = []
    for i in range(0, len(companies), batch_size):
        batch = companies[i:i+batch_size]
        enriched.extend(await asyncio.gather(*(enrich_company(c, fetch_yf) for c in batch)))
    return enriched

# -------------------------
# COMPETITOR MAP
# -------------------------
def build_competitor_map(df, top_n=5):
    df["industry"] = df.get("industry", "")
    df["country"] = df.get("country", "")
    df["profile"] = (df["industry"] + " " + df["country"]).str.strip()
    df_nonempty = df[df["profile"] != ""]
    if df_nonempty.empty:
        return {name: [] for name in df["company_name"]}
    tfidf = TfidfVectorizer(stop_words="english")
    matrix = tfidf.fit_transform(df_nonempty["profile"])
    similarity = cosine_similarity(matrix)
    competitor_map = {}
    for idx, name in enumerate(df_nonempty["company_name"]):
        scores = sorted(list(enumerate(similarity[idx])), key=lambda x: x[1], reverse=True)[1:top_n+1]
        competitor_map[name] = [df_nonempty.iloc[j]["company_name"] for j, _ in scores]
    for name in df["company_name"]:
        if name not in competitor_map:
            competitor_map[name] = []
    return competitor_map

# -------------------------
# EXCEL EXPORT (Safe)
# -------------------------
def export_to_excel(data, filename="company_intelligence.xlsx"):
    df = pd.DataFrame(data)
    required_columns = ["company_name","website","founding_year","headquarters",
                        "company_type","jurisdiction","is_public",
                        "cin","company_status","incorporation_date","registry_url",
                        "annual_revenue","market_cap","industry","country"]
    for col in required_columns:
        if col not in df.columns:
            df[col] = None
    with pd.ExcelWriter(filename, engine="openpyxl") as writer:
        df[["company_name","website","founding_year","headquarters",
            "company_type","jurisdiction","is_public"]].to_excel(writer, "Companies_Master", index=False)
        df[["company_name","cin","company_status","incorporation_date","registry_url"]].to_excel(writer, "India_MCA_Legal", index=False)
        df[["company_name","annual_revenue","market_cap"]].to_excel(writer, "Financials_Public", index=False)
        df[["company_name","industry","country"]].to_excel(writer, "Market_Info", index=False)
    st.success(f"✅ Excel exported: {filename}")

# -------------------------
# STREAMLIT UI
# -------------------------
st.set_page_config(page_title="Free Company Intelligence", layout="wide")
st.title("📊 Free Company Intelligence Dashboard")

uploaded_file = st.file_uploader("Upload CSV with 'company_name'", type=["csv"])
manual_input = st.text_area("Or enter company names manually (one per line)", height=150)

company_names = []
if uploaded_file:
    df_upload = pd.read_csv(uploaded_file)
    if "company_name" in df_upload.columns:
        company_names = df_upload["company_name"].dropna().unique().tolist()
    else:
        st.error("CSV must have 'company_name' column!")

if manual_input:
    manual_names = [x.strip() for x in manual_input.split("\n") if x.strip()]
    company_names.extend(manual_names)

company_names = list(set(company_names))

fetch_yf_option = st.checkbox("Fetch Yahoo Finance data (may be slow / limited)", value=False)

if st.button("Enrich Companies") and company_names:
    with st.spinner("⏳ Fetching company data..."):
        data_future = run_async(enrich_all(company_names, fetch_yf=fetch_yf_option))
        if asyncio.isfuture(data_future):
            data = asyncio.get_event_loop().run_until_complete(data_future)
        else:
            data = data_future

        if not data:
            st.warning("No data fetched.")
        else:
            df = pd.DataFrame(data)
            competitors = build_competitor_map(df)
            df["potential_competitors"] = df["company_name"].map(competitors)

            st.success("✅ Data fetched successfully!")
            st.dataframe(df)

            # Download Excel
            output_file = "company_intelligence.xlsx"
            export_to_excel(df.to_dict("records"), filename=output_file)
            with open(output_file, "rb") as f:
                st.download_button(
                    label="⬇ Download Excel Report",
                    data=f,
                    file_name=output_file,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

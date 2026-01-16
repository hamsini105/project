import streamlit as st
import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import urllib.robotparser
import re
import json
import time
import hashlib
from collections import Counter

# ----------------- Streamlit Config -----------------
st.set_page_config(page_title="AI SEO Analyzer Pro (Groq)", layout="wide")

# ----------------- HTTP Session -----------------
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "AI-SEO-Analyzer/6.0"})


# ----------------- GROQ Chat (OpenAI-Compatible) -----------------
def groq_chat(prompt: str, temperature: float = 0.3) -> str:
    """
    Groq OpenAI-compatible endpoint:
    POST https://api.groq.com/openai/v1/chat/completions
    """
    try:
        if "groq_key" not in st.secrets:
            return "❌ Missing groq_key in .streamlit/secrets.toml"

        api_key = st.secrets["groq_key"]
        base_url = st.secrets.get("groq_base", "https://api.groq.com/openai/v1").rstrip("/")
        model = st.secrets.get("groq_model", "llama-3.1-8b-instant")

        # IMPORTANT: trim prompt to avoid token overload causing 400
        prompt = prompt.strip()
        if len(prompt) > 12000:
            prompt = prompt[:12000] + "\n\n[TRUNCATED]"

        url = f"{base_url}/chat/completions"

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are an expert SEO auditor and technical SEO specialist."},
                {"role": "user", "content": prompt},
            ],
            "temperature": float(temperature),
            "max_tokens": 800,  # IMPORTANT: prevents huge output / request failures
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        r = requests.post(url, headers=headers, json=payload, timeout=40)

        # Show Groq's real error details (instead of generic 400)
        if r.status_code != 200:
            try:
                return f"❌ Groq API error {r.status_code}: {r.json()}"
            except Exception:
                return f"❌ Groq API error {r.status_code}: {r.text}"

        data = r.json()
        return data["choices"][0]["message"]["content"].strip()

    except Exception as e:
        return f"❌ Groq API error: {str(e)}"

# ----------------- Helpers -----------------
def validate_url(url: str) -> str | None:
    if not url:
        return None
    url = url.strip()
    parsed = urlparse(url)
    if not parsed.scheme:
        url = "https://" + url
        parsed = urlparse(url)
    if not parsed.netloc:
        return None
    return url


@st.cache_data(ttl=3600, show_spinner=False)
def allowed_by_robots(url: str, user_agent="*") -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = urllib.robotparser.RobotFileParser()
    try:
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(user_agent, url)
    except Exception:
        return True


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_page(url: str, timeout=12) -> dict:
    try:
        t0 = time.perf_counter()
        resp = SESSION.get(url, timeout=timeout, allow_redirects=True, stream=True)
        t_headers = time.perf_counter()
        content = resp.content
        t1 = time.perf_counter()

        return {
            "final_url": resp.url,
            "html": content.decode(resp.encoding or "utf-8", errors="ignore"),
            "status_code": resp.status_code,
            "ttfb_ms": round((t_headers - t0) * 1000, 2),
            "total_ms": round((t1 - t0) * 1000, 2),
            "bytes": len(content),
            "history_urls": [h.url for h in resp.history],
            "history_statuses": [h.status_code for h in resp.history],
        }
    except Exception as e:
        return {
            "final_url": None,
            "html": None,
            "status_code": None,
            "ttfb_ms": None,
            "total_ms": None,
            "bytes": None,
            "history_urls": [],
            "history_statuses": [],
            "error": str(e),
        }


def soup_from_html(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def get_clean_text(soup: BeautifulSoup) -> str:
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    text = re.sub(r"\n\s*\n+", "\n\n", text).strip()
    return text


def extract_json_ld(soup: BeautifulSoup):
    scripts = soup.find_all("script", type="application/ld+json")
    out = []
    for s in scripts:
        if not s.string:
            continue
        try:
            out.append(json.loads(s.string))
        except Exception:
            pass
    return out


def detect_faq_from_jsonld(jsonlds) -> bool:
    def check_obj(obj):
        if isinstance(obj, dict):
            t = obj.get("@type") or obj.get("type")
            if t and ("FAQ" in str(t) or "Question" in str(t)):
                return True
            for v in obj.values():
                if check_obj(v):
                    return True
        elif isinstance(obj, list):
            for item in obj:
                if check_obj(item):
                    return True
        return False
    return check_obj(jsonlds)


def top_terms(text: str, n=12):
    stop = {
        "the","and","is","in","to","a","of","for","that","on","with","as","are",
        "this","it","by","an","at","from","or","be","was","were","can","will"
    }
    words = re.findall(r"\w+", text.lower())
    words = [w for w in words if len(w) > 2 and w not in stop and not w.isdigit()]
    return Counter(words).most_common(n)


def get_meta(soup: BeautifulSoup, name=None, prop=None):
    if name:
        tag = soup.find("meta", attrs={"name": name})
        if tag and tag.get("content"):
            return tag.get("content").strip()
    if prop:
        tag = soup.find("meta", attrs={"property": prop})
        if tag and tag.get("content"):
            return tag.get("content").strip()
    return ""


def get_canonical(soup: BeautifulSoup) -> str:
    link = soup.find("link", attrs={"rel": "canonical"})
    if link and link.get("href"):
        return link.get("href").strip()
    return ""


def get_hreflang(soup: BeautifulSoup):
    tags = soup.find_all("link", attrs={"rel": "alternate"})
    hreflangs = []
    for t in tags:
        if t.get("hreflang") and t.get("href"):
            hreflangs.append({"hreflang": t.get("hreflang"), "href": t.get("href")})
    return hreflangs


def canonical_mismatch(final_url: str, canonical_url: str) -> bool:
    if not canonical_url:
        return False
    canon_abs = urljoin(final_url, canonical_url)
    return canon_abs.rstrip("/") != final_url.rstrip("/")


def get_links(final_url: str, soup: BeautifulSoup):
    links = []
    for a in soup.find_all("a", href=True):
        href = a.get("href")
        if not href:
            continue
        abs_url = urljoin(final_url, href)
        links.append(abs_url)
    return list(dict.fromkeys(links))


def check_broken_links(links, max_links=40) -> dict:
    links = links[:max_links]
    broken = []
    ok = 0

    for u in links:
        try:
            r = SESSION.head(u, timeout=8, allow_redirects=True)
            code = r.status_code
            if code >= 400:
                broken.append({"url": u, "status": code})
            else:
                ok += 1
        except Exception:
            broken.append({"url": u, "status": "error"})

    return {"checked": len(links), "ok": ok, "broken": broken}


def redirect_chain_info(url: str) -> dict:
    try:
        r = SESSION.get(url, timeout=10, allow_redirects=True)
        chain = [{"url": h.url, "status": h.status_code} for h in r.history]
        chain.append({"url": r.url, "status": r.status_code})
        return {"chain": chain, "hops": len(r.history)}
    except Exception:
        return {"chain": [], "hops": 0}


def heading_structure_score(soup: BeautifulSoup) -> dict:
    counts = {f"h{i}": len(soup.find_all(f"h{i}")) for i in range(1, 7)}
    score = 100

    if counts["h1"] == 0:
        score -= 35
    elif counts["h1"] > 1:
        score -= 15

    if counts["h3"] > 0 and counts["h2"] == 0:
        score -= 15
    if counts["h4"] > 0 and counts["h3"] == 0:
        score -= 10
    if counts["h5"] > 0 and counts["h4"] == 0:
        score -= 5

    score = max(0, min(100, score))
    return {"score": score, "counts": counts}


def answer_block_detection(soup: BeautifulSoup) -> dict:
    paras = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
    paras = [p for p in paras if len(p.split()) >= 8]

    top_para = paras[0] if paras else ""
    is_short_answer = bool(top_para and len(top_para) <= 450)

    qa_patterns = 0
    for p in paras[:12]:
        if re.search(r"^(what|why|how|when|where|who)\b", p.lower()):
            qa_patterns += 1

    return {
        "has_answer_block": is_short_answer or qa_patterns >= 2,
        "top_paragraph_chars": len(top_para),
        "qa_like_paragraphs": qa_patterns,
        "top_paragraph_preview": top_para[:280] + ("..." if len(top_para) > 280 else ""),
    }


def estimate_image_weight(final_url: str, soup: BeautifulSoup, max_images=12) -> dict:
    imgs = soup.find_all("img")
    img_urls = []
    for im in imgs:
        src = im.get("src") or ""
        if not src:
            continue
        img_urls.append(urljoin(final_url, src))

    img_urls = img_urls[:max_images]
    total_bytes = 0
    checked = []

    for u in img_urls:
        try:
            r = SESSION.head(u, timeout=8, allow_redirects=True)
            size = int(r.headers.get("Content-Length", "0"))
            total_bytes += size
            checked.append({"url": u, "bytes": size})
        except Exception:
            checked.append({"url": u, "bytes": None})

    return {
        "checked_count": len(checked),
        "total_estimated_bytes": total_bytes,
        "images": checked,
    }


def compute_duplicate_hash(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text.strip().lower())
    return hashlib.sha256(cleaned[:20000].encode("utf-8")).hexdigest()


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_sitemap_urls(site_url: str, limit=50):
    parsed = urlparse(site_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    candidates = [base + "/sitemap.xml", base + "/sitemap_index.xml"]

    urls = []
    found_sitemap = None

    for sm in candidates:
        try:
            r = SESSION.get(sm, timeout=12)
            if r.status_code != 200:
                continue
            xml = r.text
            locs = re.findall(r"<loc>(.*?)</loc>", xml, flags=re.IGNORECASE)
            if locs:
                found_sitemap = sm
                urls.extend(locs)
                break
        except Exception:
            continue

    urls = [u.strip() for u in urls if u.strip().startswith("http")]
    urls = list(dict.fromkeys(urls))[:limit]
    return {"sitemap": found_sitemap, "urls": urls}


def quick_page_score(features: dict) -> float:
    score = 0
    if features.get("https"):
        score += 15
    if features.get("status_code") == 200:
        score += 10
    if features.get("title_len", 0) >= 30:
        score += 10
    if 50 <= features.get("meta_len", 0) <= 160:
        score += 10
    if features.get("h1_count", 0) >= 1:
        score += 10
    if features.get("canonical_present"):
        score += 10
    if features.get("viewport_present"):
        score += 10
    if features.get("has_json_ld"):
        score += 10
    if features.get("has_faq"):
        score += 5
    if features.get("heading_score", 0) >= 80:
        score += 10
    return round(min(100, score), 2)


# ----------------- Groq-powered SEO Features -----------------
def intent_classification_and_keywords(text: str, top_terms_list) -> str:
    prompt = f"""
Extract SEO keywords and classify search intent.

Rules:
- Output JSON only.
- Keep it concise.

Page text (truncated):
{text[:5000]}

Top terms:
{top_terms_list}

Return JSON with keys:
- primary_keywords: list of 5
- secondary_keywords: list of 10
- intent: one of ["informational","commercial","transactional","navigational","mixed"]
- suggested_questions: list of 6 user questions
"""
    return groq_chat(prompt, temperature=0.2)


def content_gap_ideas(title: str, text: str, keywords_json: str) -> str:
    prompt = f"""
You are an SEO content strategist.

Page title: {title}

Keyword/intent data:
{keywords_json}

Content excerpt:
{text[:4500]}

Return:
- 10 missing subtopics (content gaps)
- 5 FAQ questions we should add
- 5 internal link anchor text ideas
"""
    return groq_chat(prompt, temperature=0.4)


def rewrite_title_meta(title: str, meta: str, intent_json: str) -> str:
    prompt = f"""
Rewrite title and meta description for higher CTR and SEO.

Current title: {title}
Current meta: {meta}

Intent/keywords:
{intent_json}

Return:
1) 3 improved titles (<=60 chars)
2) 3 improved meta descriptions (<=155 chars)
3) Best pick (title + meta)
"""
    return groq_chat(prompt, temperature=0.4)


def generate_faq_schema(title: str, text: str) -> str:
    prompt = f"""
Generate FAQ schema for this page.

Page title: {title}

Content excerpt:
{text[:4500]}

Return ONLY valid JSON-LD FAQPage schema (no markdown, no explanation).
Must include 5-8 Q&A items.
"""
    return groq_chat(prompt, temperature=0.3)


def schema_validation_suggestions(jsonlds, title: str, final_url: str) -> str:
    prompt = f"""
Validate and improve JSON-LD structured data for SEO.

Page title: {title}
URL: {final_url}

Existing JSON-LD objects:
{json.dumps(jsonlds, indent=2)[:8000]}

Return:
1) Issues found (bullet list)
2) Suggested improved JSON-LD (only if needed)
3) Best schema types recommended for this page
"""
    return groq_chat(prompt, temperature=0.2)


def detect_duplicate_content_groq(text_a: str, text_b: str) -> str:
    prompt = f"""
Compare two page texts and detect if they are duplicate or near-duplicate.

Return JSON only:
{{
  "duplicate": true/false,
  "similarity_reason": "...",
  "suggested_changes": ["...", "...", "..."]
}}

Text A:
{text_a[:3500]}

Text B:
{text_b[:3500]}
"""
    return groq_chat(prompt, temperature=0.2)


# ----------------- UI -----------------
st.title("⚡ AI SEO Analyzer Pro (Groq)")
st.caption("All SEO features powered by Groq API (no Google PSI).")

with st.sidebar:
    st.subheader("Options")
    max_links_check = st.slider("Max links to check", 10, 100, 40, 5)
    sitemap_limit = st.slider("Sitemap crawl limit", 10, 150, 50, 10)
    max_images_weight = st.slider("Max images for image weight estimate", 5, 30, 12, 1)
    st.divider()

    if "groq_key" in st.secrets:
        st.success("Groq key loaded ✅")
    else:
        st.error("Missing groq_key in secrets.toml ❌")

url = st.text_input("Enter URL", placeholder="https://example.com/page")
analyze = st.button("Analyze", type="primary")

if analyze:
    url = validate_url(url)
    if not url:
        st.error("Enter a valid URL.")
        st.stop()

    robots_ok = allowed_by_robots(url)
    if not robots_ok:
        st.warning("robots.txt may disallow crawling this URL.")

    with st.spinner("Fetching page..."):
        fetch = fetch_page(url)

    if not fetch["html"]:
        st.error("Failed to fetch page.")
        st.code(fetch.get("error", "Unknown error"))
        st.stop()

    final_url = fetch["final_url"]
    html = fetch["html"]
    status_code = fetch["status_code"]
    soup = soup_from_html(html)

    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    meta_desc = get_meta(soup, name="description") or get_meta(soup, prop="og:description")
    canonical = get_canonical(soup)
    hreflangs = get_hreflang(soup)

    og_title = get_meta(soup, prop="og:title")
    og_desc = get_meta(soup, prop="og:description")
    og_image = get_meta(soup, prop="og:image")
    tw_title = get_meta(soup, name="twitter:title")
    tw_desc = get_meta(soup, name="twitter:description")
    tw_image = get_meta(soup, name="twitter:image")

    h_score = heading_structure_score(soup)
    jsonlds = extract_json_ld(soup)
    text = get_clean_text(soup)
    terms = top_terms(text, 12)
    dup_hash = compute_duplicate_hash(text)

    links = get_links(final_url, soup)
    redirect_chain = redirect_chain_info(url)
    broken = check_broken_links(links, max_links=max_links_check)
    img_weight = estimate_image_weight(final_url, soup, max_images=max_images_weight)

    canon_mismatch = canonical_mismatch(final_url, canonical)

    kb = round((fetch["bytes"] or 0) / 1024, 2)
    perf_grade = "Good"
    if fetch["total_ms"] and fetch["total_ms"] > 3500:
        perf_grade = "Slow"
    elif fetch["total_ms"] and fetch["total_ms"] > 1800:
        perf_grade = "Okay"

    with st.spinner("Checking sitemap..."):
        sm = fetch_sitemap_urls(final_url, limit=sitemap_limit)

    sitemap_scores = []
    if sm["urls"]:
        with st.spinner("Scoring sitemap pages (light)..."):
            for u in sm["urls"]:
                f = fetch_page(u, timeout=10)
                if not f["html"]:
                    sitemap_scores.append({"url": u, "score": 0, "status": "fetch_failed"})
                    continue
                sp = soup_from_html(f["html"])
                t = sp.title.string.strip() if sp.title and sp.title.string else ""
                md = get_meta(sp, name="description") or get_meta(sp, prop="og:description")
                can = get_canonical(sp)
                vp = bool(sp.find("meta", attrs={"name": "viewport"}))
                hs = heading_structure_score(sp)
                jsonld2 = extract_json_ld(sp)
                hasfaq2 = detect_faq_from_jsonld(jsonld2)

                features2 = {
                    "https": urlparse(f["final_url"]).scheme == "https",
                    "status_code": f["status_code"],
                    "title_len": len(t),
                    "meta_len": len(md),
                    "h1_count": len(sp.find_all("h1")),
                    "canonical_present": bool(can),
                    "viewport_present": vp,
                    "has_json_ld": len(jsonld2) > 0,
                    "has_faq": hasfaq2,
                    "heading_score": hs["score"],
                }
                sitemap_scores.append({"url": f["final_url"], "score": quick_page_score(features2), "status": f["status_code"]})

    st.subheader("📊 Summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Status", status_code)
    c2.metric("TTFB (ms)", fetch["ttfb_ms"])
    c3.metric("Total Load (ms)", fetch["total_ms"])
    c4.metric("Page Size (KB)", kb)

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Technical SEO", "Content SEO", "AEO / Featured Snippets", "Performance", "Export"]
    )

    with tab1:
        st.subheader("✅ Technical SEO")
        st.write("**Redirect Chain Detector**")
        st.write(f"Hops: **{redirect_chain['hops']}**")
        st.json(redirect_chain["chain"])

        st.write("**Canonical**")
        st.write(f"Canonical tag: `{canonical or 'None'}`")
        if canon_mismatch:
            st.error("Canonical mismatch detected.")
        else:
            st.success("No canonical mismatch detected (or no canonical).")

        st.write("**Hreflang Detection**")
        if hreflangs:
            st.table(hreflangs)
        else:
            st.info("No hreflang tags found.")

        st.write("**OpenGraph / Twitter Preview**")
        colA, colB = st.columns(2)
        with colA:
            st.markdown("**OpenGraph**")
            st.write("og:title:", og_title or "(missing)")
            st.write("og:description:", og_desc or "(missing)")
            st.write("og:image:", og_image or "(missing)")
        with colB:
            st.markdown("**Twitter Card**")
            st.write("twitter:title:", tw_title or "(missing)")
            st.write("twitter:description:", tw_desc or "(missing)")
            st.write("twitter:image:", tw_image or "(missing)")

        st.write("**Broken Links Checker (404)**")
        st.write(f"Checked: {broken['checked']} | OK: {broken['ok']} | Broken: {len(broken['broken'])}")
        if broken["broken"]:
            st.error("Broken links found:")
            st.table(broken["broken"])
        else:
            st.success("No broken links found in checked links.")

        st.write("**Sitemap Crawl + Page Scoring**")
        if sm["sitemap"]:
            st.success(f"Sitemap found: {sm['sitemap']}")
        else:
            st.warning("No sitemap found at /sitemap.xml or /sitemap_index.xml")

        if sitemap_scores:
            sitemap_scores_sorted = sorted(sitemap_scores, key=lambda x: x["score"])
            st.table(sitemap_scores_sorted[:25])
        else:
            st.info("No sitemap URLs scored.")

    with tab2:
        st.subheader("🔥 Content SEO")
        st.write("**Heading Structure Quality Score**")
        st.metric("Heading Score", h_score["score"])
        st.json(h_score["counts"])

        st.write("**Top Terms**")
        st.write(", ".join([f"{t}({c})" for t, c in terms]))

        st.write("**Keyword extraction + intent classification (Groq)**")
        intent_json = intent_classification_and_keywords(text, terms)
        st.code(intent_json)

        st.write("**Title/meta rewrite generator (Groq)**")
        rewrite = rewrite_title_meta(title, meta_desc, intent_json)
        st.write(rewrite)

        st.write("**Content gap ideas (Groq)**")
        gaps = content_gap_ideas(title, text, intent_json)
        st.write(gaps)

        st.write("**Duplicate content detection**")
        compare_url = st.text_input("Compare with another URL", placeholder="https://example.com/other-page")
        if compare_url:
            compare_url = validate_url(compare_url)
            if compare_url:
                with st.spinner("Fetching comparison page..."):
                    comp = fetch_page(compare_url)
                if comp["html"]:
                    comp_text = get_clean_text(soup_from_html(comp["html"]))
                    hash_b = compute_duplicate_hash(comp_text)

                    st.write("Hash A:", dup_hash[:16] + "...")
                    st.write("Hash B:", hash_b[:16] + "...")

                    if dup_hash == hash_b:
                        st.error("Exact duplicate detected (hash match).")
                    else:
                        st.warning("Checking similarity using Groq...")
                        dup_ai = detect_duplicate_content_groq(text, comp_text)
                        st.code(dup_ai)
                else:
                    st.error("Failed to fetch comparison URL.")

    with tab3:
        st.subheader("AEO / Featured Snippets")
        ans = answer_block_detection(soup)
        if ans["has_answer_block"]:
            st.success("Answer-like block detected.")
        else:
            st.warning("No strong answer block detected.")
        st.json(ans)

        st.write("**FAQ Schema Generator (Groq)**")
        if st.button("Generate FAQ JSON-LD", type="primary"):
            faq_schema = generate_faq_schema(title, text)
            st.code(faq_schema)

        st.write("**Schema Validation + Suggestions (Groq)**")
        if st.button("Validate / Improve Schema with Groq"):
            schema_report = schema_validation_suggestions(jsonlds, title, final_url)
            st.write(schema_report)

    with tab4:
        st.subheader("⚡ Performance (No Google PSI)")
        st.metric("Performance Grade", perf_grade)
        st.metric("TTFB (ms)", fetch["ttfb_ms"])
        st.metric("Total Load (ms)", fetch["total_ms"])
        st.metric("HTML KB", kb)

        st.write("**Image weight estimation**")
        st.metric("Images Checked", img_weight["checked_count"])
        st.metric("Estimated Total Image Bytes", img_weight["total_estimated_bytes"])
        if img_weight["images"]:
            st.table(img_weight["images"])

    with tab5:
        st.subheader("⬇️ Export")
        report = {
            "url": final_url,
            "status_code": status_code,
            "robots_ok": robots_ok,
            "timing": {
                "ttfb_ms": fetch["ttfb_ms"],
                "total_ms": fetch["total_ms"],
                "bytes": fetch["bytes"],
            },
            "technical": {
                "redirect_chain": redirect_chain,
                "canonical": canonical,
                "canonical_mismatch": canon_mismatch,
                "hreflang": hreflangs,
                "og": {"title": og_title, "description": og_desc, "image": og_image},
                "twitter": {"title": tw_title, "description": tw_desc, "image": tw_image},
                "broken_links": broken,
                "sitemap": sm,
                "sitemap_scores": sitemap_scores[:200],
            },
            "content": {
                "title": title,
                "meta_description": meta_desc,
                "heading_score": h_score,
                "top_terms": terms,
                "text_hash": dup_hash,
            },
            "schema": {"jsonld_count": len(jsonlds), "jsonlds": jsonlds},
            "performance": {"grade": perf_grade, "image_weight_estimate": img_weight},
        }

        st.download_button(
            "Download JSON Report",
            data=json.dumps(report, indent=2),
            file_name="seo_report.json",
            mime="application/json",
        )

st.markdown("---")
st.caption("Powered by Groq • Streamlit SEO Analyzer")

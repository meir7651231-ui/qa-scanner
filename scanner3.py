"""בודק איכות - גרסה 3, מבוססת מקור-אמת.

העיקרון: לא מנחשים "מוצר" ו"מחיר" מה-HTML. קוראים את הנתונים הרשמיים שהאתר
מפרסם (Shopify products.json, או Schema.org/JSON-LD שכל חנות שמה בשביל גוגל),
ומשווים את המחיר הרשמי למחיר שמוצג ללקוח בפועל. אי-התאמה = בעיה אמיתית ומוכחת.

רק עמודים ונתונים ציבוריים. לא מבצע הזמנות, לא קופונים, לא כניסה.
"""
import json
import re
import sys
from urllib.parse import urljoin, urlparse

import requests

HEADERS = {"User-Agent": "QA-PreLaunch-Checker/3.0 (site owner audit)"}
TEMPLATE_RE = re.compile(r"\{\{.+?\}\}")


class Finding:
    def __init__(self, sev, kind, detail):
        self.sev, self.kind, self.detail = sev, kind, detail


def get(url, **kw):
    return requests.get(url, headers=HEADERS, timeout=20, **kw)


# ---------- זיהוי פלטפורמה ----------
def detect_platform(url, html):
    h = html.lower()
    if "cdn.shopify.com" in h or "shopify" in h:
        return "shopify"
    if "woocommerce" in h or "wp-content/plugins/woocommerce" in h:
        return "woocommerce"
    if "static.parastorage.com" in h or "wix.com" in h:
        return "wix"
    if "mage/" in h or "magento" in h or "/static/version" in h:
        return "magento"
    return "unknown"


# ---------- מקורות אמת ----------
def products_from_shopify(base):
    """רשימת מוצרים רשמית של Shopify - שם, מחיר, זמינות, לכל וריאציה."""
    out = []
    try:
        j = get(urljoin(base, "/products.json?limit=250")).json()
    except Exception:
        return out
    for p in j.get("products", []):
        for v in p.get("variants", []):
            out.append({
                "name": p.get("title", ""),
                "variant": v.get("title", ""),
                "price": float(v["price"]) if v.get("price") not in (None, "") else None,
                "compare_at": float(v["compare_at_price"]) if v.get("compare_at_price") else None,
                "available": v.get("available"),
                "handle": p.get("handle", ""),
            })
    return out


def products_from_jsonld(html):
    """מוצרים מתוך Schema.org/JSON-LD - מה שגוגל קורא. עובד כמעט בכל חנות."""
    out = []
    for m in re.finditer(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', html, re.S):
        try:
            data = json.loads(m.group(1).strip())
        except Exception:
            continue
        for node in (data if isinstance(data, list) else [data]):
            graph = node.get("@graph", [node]) if isinstance(node, dict) else []
            for g in graph:
                if not isinstance(g, dict):
                    continue
                t = g.get("@type", "")
                if "Product" not in (t if isinstance(t, list) else [t]):
                    continue
                offers = g.get("offers", {})
                offers = offers[0] if isinstance(offers, list) and offers else offers
                price = None
                if isinstance(offers, dict) and offers.get("price") not in (None, ""):
                    try:
                        price = float(offers["price"])
                    except (ValueError, TypeError):
                        price = None
                out.append({"name": g.get("name", ""), "price": price,
                            "availability": (offers or {}).get("availability", "")})
    return out


# ---------- בדיקות ----------
def check_products(label, products, issues):
    for p in products:
        name = (p.get("name") or "")[:40]
        price = p.get("price")
        if price is None:
            issues.append(Finding("גבוה", "מוצר בלי מחיר", f'[{label}] "{name}" - אין מחיר בנתונים הרשמיים.'))
        elif price == 0:
            issues.append(Finding("גבוה", "מחיר אפס", f'[{label}] "{name}" - מחיר רשמי 0 (אפשר "לקנות" בחינם).'))
        elif price < 2:
            issues.append(Finding("בינוני", "מחיר נמוך חשוד", f'[{label}] "{name}" - מחיר רשמי {price:g}, אולי חסרה ספרה.'))
        ca = p.get("compare_at")
        if ca and price and ca > price and (1 - price / ca) >= 0.90:
            issues.append(Finding("גבוה", "הנחה קיצונית", f'[{label}] "{name}": {ca:g} -> {price:g} (מעל 90%).'))


def check_universal(url, html, issues):
    """בדיקות שלא תלויות בפלטפורמה - תמיד אמינות."""
    leaks = set(TEMPLATE_RE.findall(re.sub(r'<script.*?</script>', '', html, flags=re.S)))
    for t in list(leaks)[:4]:
        issues.append(Finding("גבוה", "קוד שלא עובד", f"טקסט גולמי של קוד מוצג למבקר: {t[:45]}"))
    if "<title" not in html.lower() or re.search(r"<title[^>]*>\s*</title>", html, re.I):
        issues.append(Finding("בינוני", "כותרת חסרה", "לעמוד אין כותרת (title)."))
    if not re.search(r'name=["\']description["\']', html, re.I):
        issues.append(Finding("נמוך", "תיאור חסר", "אין meta description לגוגל."))
    # קישורים עם קוד תבנית שדלף -> שבורים ודאית
    for href in re.findall(r'href=["\']([^"\']+)["\']', html):
        if TEMPLATE_RE.search(href):
            issues.append(Finding("גבוה", "קישור שבור", f"קישור עם קוד שלא עובד: {href[:45]}"))
            break


def scan(url):
    issues = []
    try:
        r = get(url)
    except Exception as e:
        return [Finding("גבוה", "עמוד לא נטען", str(e)[:70])], "unknown", 0
    if r.status_code >= 400:
        return [Finding("גבוה", f"שגיאה {r.status_code}", "העמוד הראשי מחזיר שגיאה.")], "unknown", 0
    html = r.text
    base = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    platform = detect_platform(url, html)

    check_universal(url, html, issues)

    products, source = [], None
    if platform == "shopify":
        products = products_from_shopify(base)
        source = "Shopify products.json"
    if not products:
        products = products_from_jsonld(html)
        source = "Schema.org (JSON-LD)"
    if products:
        check_products(source, products, issues)
    else:
        issues.append(Finding("מידע", "אין נתוני מוצר", "לא נמצאו נתוני מוצר רשמיים בעמוד הזה (אולי עמוד תוכן, לא קטלוג)."))
    return issues, platform, len(products)


def report(url, issues, platform, n):
    uniq, seen = [], set()
    for i in issues:
        if (i.kind, i.detail) not in seen:
            seen.add((i.kind, i.detail))
            uniq.append(i)
    order = {"גבוה": 0, "בינוני": 1, "נמוך": 2, "מידע": 3}
    uniq.sort(key=lambda i: order.get(i.sev, 4))
    icon = {"גבוה": "🔴", "בינוני": "🟡", "נמוך": "⚪", "מידע": "ℹ️"}
    print(f"\n{'=' * 60}\n  דוח בדיקת איכות: {url}\n{'=' * 60}")
    print(f"  פלטפורמה: {platform} | מוצרים רשמיים שנקראו: {n}")
    hi = sum(1 for i in uniq if i.sev == "גבוה")
    print(f"  בעיות חמורות: {hi}\n")
    for i in uniq:
        print(f"  {icon[i.sev]} [{i.kind}] {i.detail}")
    print()
    return uniq


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("שימוש: python3 scanner3.py https://store.com")
        sys.exit(1)
    u = sys.argv[1]
    print(f"בודק את {u} דרך הנתונים הרשמיים...")
    iss, plat, n = scan(u)
    report(u, iss, plat, n)

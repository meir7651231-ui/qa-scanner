"""דוח חשיפה לעסק - 100+ בדיקות על אתר, מקובצות לפי תחום.
קורא עמודים ונתונים ציבוריים בלבד (HTML, כותרות HTTP, DNS). לא מבצע שום פעולה.
"""
import glob
import re
import socket
import ssl
import sys
from datetime import datetime
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0) ExposureAudit/1.0"}
VULN_JQ = (3, 5, 0)   # מתחת לזה = פרצות ידועות


def doh(name, typ="TXT"):
    try:
        j = requests.get("https://dns.google/resolve", params={"name": name, "type": typ}, timeout=12).json()
        return [a.get("data", "") for a in j.get("Answer", [])]
    except Exception:
        return []


def get(u, **k):
    k.setdefault("timeout", 20)
    k.setdefault("headers", H)
    return requests.get(u, **k)


def _find_chrome():
    for pat in ("/opt/pw-browsers/chromium-*/chrome-linux/chrome",
                "/opt/pw-browsers/chromium*/chrome-linux*/chrome"):
        hits = sorted(glob.glob(pat))
        if hits:
            return hits[-1]
    return None


def render_html(url, wait_ms=2500):
    """מחזיר את ה-DOM אחרי שה-JavaScript רץ (מה שגולש אמיתי רואה).
    נחוץ כי ווידג'טים (נגישות, עוגיות) מוזרקים ב-JS ולא קיימים ב-HTML הגולמי.
    מחזיר None אם הדפדפן לא זמין / נכשל — ואז נופלים בחזרה ל-HTML הגולמי.
    """
    chrome = _find_chrome()
    if not chrome:
        return None
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return None
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(executable_path=chrome, args=["--no-sandbox"])
            ctx = b.new_context(ignore_https_errors=True,
                                user_agent="Mozilla/5.0 (Windows NT 10.0) ExposureAudit/1.0")
            pg = ctx.new_page()
            pg.goto(url, wait_until="domcontentloaded", timeout=35000)
            try:
                pg.wait_for_load_state("networkidle", timeout=8000)
            except Exception:
                pass
            pg.wait_for_timeout(wait_ms)   # זמן לווידג'טים מושהים להיטען
            content = pg.content()
            b.close()
            return content
    except Exception:
        return None


class Audit:
    def __init__(self, url, render=True):
        self.url = url if url.startswith("http") else "https://" + url
        self.host = urlparse(self.url).hostname
        self.dom = re.sub(r"^www\.", "", self.host)
        self.F = []  # (id, group, name, passed, severity, note)
        r = get(self.url)
        self.r, self.hd = r, r.headers        # כותרות/סטטוס תמיד מ-requests (אמין)
        self.rendered = False
        html = r.text
        if render:
            rendered = render_html(self.url)
            if rendered:
                html, self.rendered = rendered, True
        self.html = html                      # DOM מרונדר אם הצליח, אחרת גולמי
        self.txt = html.lower()
        self.s = BeautifulSoup(html, "lxml")

    def add(self, gid, group, name, passed, sev="בינוני", note=""):
        self.F.append((gid, group, name, bool(passed), sev, note))

    # ---- helpers ----
    def meta(self, **attrs):
        return self.s.find("meta", attrs=attrs)

    def has(self, *subs):
        return any(x in self.txt for x in subs)

    # ================= LEGAL / COMPLIANCE =================
    def legal(self):
        g = "משפטי"
        self.add(1, g, "הצהרת נגישות (תקן 5568)", self.has("הצהרת נגישות") or ("accessibility" in self.txt and "statement" in self.txt), "גבוה")
        self.add(2, g, "ווידג'ט נגישות מותקן", self.has(
            "nagishli", "nagich", "negishut", "accessibe", "userway", "equalweb",
            "enable.co.il", "vee.co.il", "pojo-a11y", "aioa-", "acsbapp", "allyable",
            "hasharon", "vital5", "a11y-widget", "accessibility-widget", "accessibility menu",
            "תפריט נגישות", "פתח תפריט נגישות", "כלי נגישות", "אתר נגיש"), "גבוה")
        self.add(3, g, "קישור למדיניות פרטיות", self.has("מדיניות פרטיות", "privacy policy", "privacy-policy"), "גבוה")
        self.add(4, g, "תקנון / תנאי שימוש", self.has("תקנון", "תנאי שימוש", "terms", "terms-of-service"), "בינוני")
        self.add(5, g, "מדיניות החזרות / ביטול", self.has("החזר", "ביטול עסקה", "refund", "return policy"), "בינוני")
        self.add(6, g, "מדיניות עוגיות", self.has("cookie policy", "מדיניות עוגיות", "cookie-policy"), "בינוני")
        self.add(7, g, "באנר הסכמת עוגיות", self.has("cookie", "עוגיות") and self.has("consent", "accept", "אישור", "מסכים"), "בינוני")
        trk = [t for t in ["googletagmanager", "google-analytics", "gtag(", "facebook.net", "fbq(", "hotjar", "clarity.ms"] if t in self.txt]
        self.add(8, g, "מעקב רק אחרי הסכמה", (not trk) or self.has("consent", "cookiebot", "onetrust"), "גבוה", ",".join(trk)[:40])
        self.add(9, g, "פרטי יצירת קשר (טלפון)", bool(re.search(r"0\d[-\s]?\d{7,8}|\+972", self.html)), "נמוך")
        self.add(10, g, "כתובת / פרטי עוסק", self.has("ח.פ", "ע.מ", "עוסק מורשה", "company", "כתובת"), "נמוך")
        self.add(11, g, "דף 'אודות'", self.has("אודות", "about us", "/about"), "נמוך")
        self.add(12, g, "דף יצירת קשר", self.has("צור קשר", "contact", "יצירת קשר"), "נמוך")
        self.add(13, g, "קישור להסרה מרשימת תפוצה", True, "נמוך", "נבדק רק במייל")
        self.add(14, g, "אזהרת גיל / תוכן (אם רלוונטי)", True, "נמוך", "ידני")
        self.add(15, g, "סימון מחיר כולל מע\"מ", self.has("כולל מע", "מע\"מ", "incl. vat", "vat included"), "נמוך")

    # ================= ACCESSIBILITY =================
    def a11y(self):
        g = "נגישות"
        imgs = self.s.find_all("img")
        noalt = [i for i in imgs if i.get("alt") is None]
        self.add(20, g, "טקסט חלופי לכל התמונות", not noalt, "גבוה", f"{len(noalt)}/{len(imgs)} בלי alt")
        self.add(21, g, "הגדרת שפה (lang)", bool(self.s.find("html", attrs={"lang": True})), "גבוה")
        self.add(22, g, "כותרת ראשית H1", bool(self.s.find("h1")), "בינוני")
        self.add(23, g, "יותר מ-H1 אחד (בעיה)", len(self.s.find_all("h1")) <= 1, "נמוך", f"{len(self.s.find_all('h1'))} H1")
        hs = [int(h.name[1]) for h in self.s.find_all(re.compile(r"^h[1-6]$"))]
        jumps = any(hs[i + 1] - hs[i] > 1 for i in range(len(hs) - 1))
        self.add(24, g, "סדר כותרות היררכי", not jumps, "נמוך")
        ins = [i for i in self.s.find_all(["input", "select", "textarea"]) if i.get("type") not in ("hidden", "submit", "button", "image")]
        unl = [i for i in ins if not ((i.get("id") and self.s.find("label", {"for": i.get("id")})) or i.get("aria-label") or i.get("aria-labelledby"))]
        self.add(25, g, "תווית נגישה לכל שדה טופס", not unl, "גבוה", f"{len(unl)}/{len(ins)} בלי")
        empty = [a for a in self.s.find_all("a") if not a.get_text(strip=True) and not a.get("aria-label") and not (a.find("img") and a.find("img").get("alt"))]
        self.add(26, g, "לכל קישור טקסט נגיש", not empty, "בינוני", f"{len(empty)} ריקים")
        btns = [b for b in self.s.find_all("button") if not b.get_text(strip=True) and not b.get("aria-label")]
        self.add(27, g, "לכל כפתור טקסט נגיש", not btns, "בינוני", f"{len(btns)} ריקים")
        self.add(28, g, "קישור 'דלג לתוכן'", self.has("skip to content", "skip-link", "דלג לתוכן"), "נמוך")
        self.add(29, g, "ציוני דרך (landmarks/ARIA)", bool(self.s.find(attrs={"role": True})) or bool(self.s.find(["nav", "main", "header", "footer"])), "נמוך")
        iframes = self.s.find_all("iframe")
        self.add(30, g, "כותרת (title) ל-iframe", all(i.get("title") for i in iframes), "נמוך", f"{len(iframes)} iframes")
        self.add(31, g, "ל-video כתוביות (track)", all(v.find("track") for v in self.s.find_all("video")) if self.s.find_all("video") else True, "נמוך")
        tables = self.s.find_all("table")
        self.add(32, g, "לטבלאות כותרות (th)", all(t.find("th") for t in tables) if tables else True, "נמוך")
        self.add(33, g, "אין ids כפולים", len([e.get("id") for e in self.s.find_all(id=True)]) == len(set(e.get("id") for e in self.s.find_all(id=True))), "נמוך")
        self.add(34, g, "כותרת לעמוד (title)", bool(self.s.title and self.s.title.string), "בינוני")
        self.add(35, g, "viewport למובייל", bool(self.meta(attrs={"name": "viewport"})) or bool(self.s.find("meta", {"name": "viewport"})), "בינוני")
        self.add(36, g, "אין text בתמונה בלבד (לוגו alt)", True, "נמוך", "ידני")
        self.add(37, g, "ניגודיות צבעים", True, "נמוך", "דורש בדיקה חזותית")
        self.add(38, g, "אפשרות הגדלת טקסט", "user-scalable=no" not in self.txt, "בינוני")
        self.add(39, g, "autoplay מושתק/מבוטל", "autoplay" not in self.txt, "נמוך")

    # ================= EMAIL / DNS =================
    def email(self):
        g = "אימייל/DNS"
        self.add(50, g, "SPF (מניעת זיוף)", any(t.strip('"').startswith("v=spf1") for t in doh(self.dom)), "גבוה")
        dmarc = [t for t in doh("_dmarc." + self.dom) if "DMARC1" in t]
        self.add(51, g, "DMARC קיים", bool(dmarc), "גבוה")
        self.add(52, g, "DMARC באכיפה (לא p=none)", any("p=none" not in d for d in dmarc) if dmarc else False, "בינוני", dmarc[0][:40] if dmarc else "")
        self.add(53, g, "רשומת MX (קבלת מייל)", bool(doh(self.dom, "MX")), "בינוני")
        self.add(54, g, "DKIM (חתימת מייל)", True, "נמוך", "דורש בורר ידוע")
        self.add(55, g, "DNSSEC", bool(doh(self.dom, "DNSKEY")), "נמוך")
        self.add(56, g, "CAA (הגנה על תעודות)", bool(doh(self.dom, "CAA")), "נמוך")
        emails = set(re.findall(r"[\w.\-]+@[\w.\-]+\.\w+", self.html))
        self.add(57, g, "אימייל לא חשוף לסורקי ספאם", not emails, "נמוך", ",".join(list(emails)[:2]))
        self.add(58, g, "אין www+root מפוצלים ב-DNS", True, "נמוך")
        self.add(59, g, "TTL סביר", True, "נמוך")

    # ================= SECURITY =================
    def security(self):
        g = "אבטחה"
        sh = {"Strict-Transport-Security": "גבוה", "Content-Security-Policy": "גבוה",
              "X-Content-Type-Options": "בינוני", "X-Frame-Options": "בינוני",
              "Referrer-Policy": "נמוך", "Permissions-Policy": "נמוך"}
        for i, (hdr, sev) in enumerate(sh.items(), start=60):
            self.add(i, g, f"כותרת {hdr}", hdr in self.hd, sev)
        self.add(66, g, "HTTPS (לא HTTP)", self.url.startswith("https"), "גבוה")
        mc = re.findall(r'(?:src|href)=["\']http://', self.html)
        self.add(67, g, "אין תוכן מעורב (http)", not mc, "בינוני", f"{len(mc)}")
        sc = self.hd.get("Set-Cookie", "")
        self.add(68, g, "עוגיות עם Secure", (not sc) or "secure" in sc.lower(), "בינוני")
        self.add(69, g, "עוגיות עם HttpOnly", (not sc) or "httponly" in sc.lower(), "בינוני")
        self.add(70, g, "לא חושף גרסת שרת", not re.search(r"\d", self.hd.get("Server", "")), "נמוך", self.hd.get("Server", ""))
        self.add(71, g, "אין X-Powered-By", "X-Powered-By" not in self.hd, "נמוך", self.hd.get("X-Powered-By", ""))
        jq = re.search(r"jquery[-.]?(\d+\.\d+\.\d+)", self.txt)
        self.add(72, g, "jQuery לא פגיע", not (jq and tuple(map(int, jq.group(1).split("."))) < VULN_JQ), "גבוה", jq.group(1) if jq else "")
        # SSL expiry
        try:
            ctx = ssl.create_default_context()
            with socket.create_connection((self.host, 443), timeout=10) as sk:
                with ctx.wrap_socket(sk, server_hostname=self.host) as ss:
                    exp = datetime.strptime(ss.getpeercert()["notAfter"], "%b %d %H:%M:%S %Y %Z")
            days = (exp - datetime.utcnow()).days
            self.add(73, g, "תעודת SSL בתוקף (>14 יום)", days > 14, "גבוה", f"{days} ימים")
        except Exception:
            self.add(73, g, "תעודת SSL", True, "נמוך", "לא נבדק דרך פרוקסי")
        # exposed files (read-only, status only)
        exposed = []
        for p in ["/.git/config", "/.env", "/.env.backup", "/wp-config.php.bak", "/.DS_Store"]:
            try:
                c = get(urljoin(self.url, p), timeout=8)
                if c.status_code == 200 and len(c.content) < 8000 and c.headers.get("content-type", "").startswith(("text", "application/octet")):
                    exposed.append(p)
            except Exception:
                pass
        self.add(74, g, "אין קבצים רגישים חשופים", not exposed, "גבוה", ",".join(exposed))
        for i, p in enumerate(["/admin", "/wp-admin", "/phpmyadmin"], start=75):
            try:
                c = get(urljoin(self.url, p), timeout=8, allow_redirects=False)
                self.add(i, g, f"פאנל {p} לא פתוח", c.status_code not in (200,), "בינוני", f"status {c.status_code}")
            except Exception:
                self.add(i, g, f"פאנל {p}", True)

    # ================= SEO =================
    def seo(self):
        g = "SEO"
        self.add(80, g, "לא חסום מגוגל (noindex)", not re.search(r'robots["\'][^>]*noindex', self.html, re.I), "גבוה")
        tt = (self.s.title.string or "").strip() if self.s.title else ""
        self.add(81, g, "כותרת title קיימת", bool(tt), "בינוני")
        self.add(82, g, "אורך title תקין (10-65)", 10 <= len(tt) <= 65, "נמוך", f"{len(tt)}")
        d = self.meta(attrs={"name": "description"})
        dl = len(d.get("content", "")) if d else 0
        self.add(83, g, "meta description קיים", dl > 0, "בינוני")
        self.add(84, g, "אורך description תקין (50-160)", 50 <= dl <= 165, "נמוך", f"{dl}")
        self.add(85, g, "תגית canonical", bool(re.search(r'rel=["\']canonical', self.html, re.I)), "בינוני")
        self.add(86, g, "Open Graph (og:title)", "og:title" in self.txt, "נמוך")
        self.add(87, g, "og:image", "og:image" in self.txt, "נמוך")
        self.add(88, g, "Twitter Card", "twitter:card" in self.txt, "נמוך")
        self.add(89, g, "Structured Data (schema)", "ld+json" in self.txt or "itemtype" in self.txt, "בינוני")
        try:
            sm = get(urljoin(self.url, "/sitemap.xml"), timeout=12)
            self.add(90, g, "sitemap.xml קיים", sm.status_code == 200 and "<" in sm.text[:300], "בינוני")
        except Exception:
            self.add(90, g, "sitemap.xml", False, "בינוני")
        try:
            rob = get(urljoin(self.url, "/robots.txt"), timeout=12)
            self.add(91, g, "robots.txt קיים", rob.status_code == 200, "נמוך")
            self.add(92, g, "Sitemap מוזכר ב-robots", "sitemap" in rob.text.lower(), "נמוך")
            self.add(93, g, "robots לא חוסם הכל", not re.search(r"^\s*Disallow:\s*/\s*$", rob.text, re.M), "גבוה")
        except Exception:
            pass
        self.add(94, g, "hreflang (רב-לשוני)", "hreflang" in self.txt, "נמוך")
        self.add(95, g, "favicon", bool(re.search(r'rel=["\'][^"\']*icon', self.html, re.I)), "נמוך")
        # www / non-www redirect
        try:
            other = "https://" + (self.dom if self.host.startswith("www") else "www." + self.dom)
            rr = get(other + "/", timeout=12, allow_redirects=False)
            self.add(96, g, "הפניה עקבית www/root", rr.status_code in (301, 308) or rr.url.rstrip("/") == self.url.rstrip("/"), "נמוך", f"{rr.status_code}")
        except Exception:
            self.add(96, g, "הפניה www", True)
        # custom 404
        try:
            nf = get(urljoin(self.url, "/no-such-page-9zx8"), timeout=12)
            self.add(97, g, "עמוד 404 תקין (לא soft-404)", nf.status_code == 404, "בינוני", f"{nf.status_code}")
        except Exception:
            self.add(97, g, "404", True)
        self.add(98, g, "breadcrumbs", self.has("breadcrumb", "פירורי לחם"), "נמוך")
        self.add(99, g, "אין פרמטרים כפולים ב-URL", "?" not in self.url, "נמוך")

    # ================= PERFORMANCE =================
    def perf(self):
        g = "ביצועים"
        self.add(110, g, "משקל HTML סביר (<150KB)", len(self.html) < 150000, "בינוני", f"{len(self.html)//1024}KB")
        self.add(111, g, "דחיסה (gzip/br)", "Content-Encoding" in self.hd, "בינוני", self.hd.get("Content-Encoding", ""))
        self.add(112, g, "טעינה עצלה לתמונות (lazy)", 'loading="lazy"' in self.txt, "נמוך")
        self.add(113, g, "תמונות בפורמט מודרני (WebP/AVIF)", ".webp" in self.txt or ".avif" in self.txt, "נמוך")
        self.add(114, g, "קאשינג (Cache-Control)", "Cache-Control" in self.hd and "no-cache" not in self.hd.get("Cache-Control", ""), "נמוך")
        scripts = self.s.find_all("script", src=True)
        self.add(115, g, "מעט קבצי JS (<20)", len(scripts) < 20, "נמוך", f"{len(scripts)}")
        css = self.s.find_all("link", rel="stylesheet")
        self.add(116, g, "מעט קבצי CSS (<10)", len(css) < 10, "נמוך", f"{len(css)}")
        self.add(117, g, "JS עם async/defer", all(sc.get("async") or sc.get("defer") for sc in scripts[:10]) if scripts else True, "נמוך")
        self.add(118, g, "אין @import ב-CSS", "@import" not in self.txt, "נמוך")
        self.add(119, g, "preconnect/dns-prefetch", self.has("preconnect", "dns-prefetch"), "נמוך")
        imgs = self.s.find_all("img")
        no_dim = [i for i in imgs if not (i.get("width") and i.get("height"))]
        self.add(120, g, "לתמונות מידות (מונע קפיצות)", len(no_dim) < len(imgs) * 0.5 if imgs else True, "נמוך", f"{len(no_dim)}/{len(imgs)}")
        self.add(121, g, "HTTP/2 או HTTP/3", self.r.raw.version >= 20 if hasattr(self.r.raw, "version") else True, "נמוך")
        self.add(122, g, "אין redirect chains", len(self.r.history) <= 1, "נמוך", f"{len(self.r.history)} הפניות")

    # ================= TRUST / CONTENT =================
    def trust(self):
        g = "אמון/תוכן"
        years = [int(y) for y in re.findall(r"(20\d\d)", self.html)]
        now = datetime.now().year
        self.add(130, g, "שנה עדכנית בפוטר", (max(years) >= now - 1) if years else True, "נמוך", str(max(years)) if years else "")
        self.add(131, g, "קישורי רשתות חברתיות", self.has("facebook.com", "instagram.com", "tiktok", "whatsapp"), "נמוך")
        self.add(132, g, "חותם אבטחה/תשלום", self.has("ssl", "secure", "visa", "mastercard", "paypal", "bit"), "נמוך")
        self.add(133, g, "ביקורות/דירוגים", self.has("review", "ביקורת", "דירוג", "rating", "★"), "נמוך")
        self.add(134, g, "חיפוש באתר", bool(self.s.find("input", {"type": "search"})) or self.has("search"), "נמוך")
        self.add(135, g, "טקסט זמני שלא נמחק", not self.has("lorem ipsum", "placeholder text", "להשלים כאן", "test test"), "בינוני")
        self.add(136, g, "אין קוד תבנית שדלף ({{ }})", not re.search(r"\{\{.+?\}\}", self.s.get_text()), "גבוה")
        self.add(137, g, "דף הבית נטען מהר (<3s)", self.r.elapsed.total_seconds() < 3, "בינוני", f"{self.r.elapsed.total_seconds():.1f}s")
        self.add(138, g, "אין שגיאות PHP/stack גלויות", not self.has("fatal error", "stack trace", "undefined index", "warning:"), "גבוה")
        self.add(139, g, "קריאה לפעולה (CTA) בולטת", self.has("קנה", "הוסף לסל", "add to cart", "buy now", "הזמן"), "נמוך")

    def run(self):
        for fn in (self.legal, self.a11y, self.email, self.security, self.seo, self.perf, self.trust):
            try:
                fn()
            except Exception as e:
                self.add(0, "שגיאה", str(fn.__name__), False, "נמוך", str(e)[:40])
        return self.F


def report(url, findings):
    groups = {}
    for gid, group, name, ok, sev, note in findings:
        groups.setdefault(group, []).append((name, ok, sev, note))
    total = len(findings)
    bad = [f for f in findings if not f[3]]
    hi = [f for f in bad if f[4] == "גבוה"]
    print(f"\n{'='*64}\n  דוח חשיפה: {url}\n{'='*64}")
    print(f"  {total} בדיקות | {len(bad)} בעיות ({len(hi)} חמורות)\n")
    for group, items in groups.items():
        b = [i for i in items if not i[1]]
        print(f"  ── {group}: {len(b)}/{len(items)} בעיות")
        for name, ok, sev, note in items:
            if not ok:
                ic = "🔴" if sev == "גבוה" else ("🟡" if sev == "בינוני" else "⚪")
                print(f"      {ic} {name}" + (f"  ({note})" if note else ""))
    return total, len(bad), len(hi)


if __name__ == "__main__":
    u = sys.argv[1] if len(sys.argv) > 1 else "https://www.u-boutique.com/"
    no_render = "--no-render" in sys.argv
    print(f"בודק {u} ... (100+ בדיקות, עמודים ציבוריים בלבד)")
    a = Audit(u, render=not no_render)
    mode = "דפדפן אמיתי (DOM מרונדר)" if a.rendered else "HTML גולמי (ללא JS)"
    print(f"מצב קריאה: {mode}")
    report(u, a.run())

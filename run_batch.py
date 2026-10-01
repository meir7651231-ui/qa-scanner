"""מריץ את מנוע מקור-האמת (scanner3) על רשימת אתרים ומפיק דוח מרוכז.
נועד לרוץ על GitHub Actions (אינטרנט נקי). קורא sites.txt, כותב ל-reports/.
"""
import sys
import time

import scanner3 as s


def main():
    sites_file = sys.argv[1] if len(sys.argv) > 1 else "sites.txt"
    with open(sites_file, encoding="utf-8") as fh:
        sites = [ln.strip() for ln in fh if ln.strip() and not ln.startswith("#")]

    import os
    os.makedirs("reports", exist_ok=True)
    suspects = []   # (url, high_findings)
    clean, errors = [], []
    for url in sites:
        print(f"scanning {url} ...")
        try:
            issues, platform, n = s.scan(url)
        except Exception as e:
            errors.append((url, str(e)[:60]))
            continue
        hi = [i for i in issues if i.sev == "גבוה"]
        # כתוב דוח מלא לכל אתר
        slug = url.split("//")[-1].strip("/").replace("/", "_").replace(":", "")[:50]
        with open(f"reports/{slug}.md", "w", encoding="utf-8") as fh:
            fh.write(f"# {url}\n\nפלטפורמה: {platform} | מוצרים רשמיים: {n}\n\n")
            for i in issues:
                fh.write(f"- [{i.sev}] **{i.kind}**: {i.detail}\n")
        if hi:
            suspects.append((url, platform, n, hi))
        elif any(i.kind == "אין נתוני מוצר" for i in issues) or n == 0:
            errors.append((url, "לא נמצאו נתוני מוצר (אולי לא Shopify/לא חנות)"))
        else:
            clean.append((url, n))
        time.sleep(1)

    # דוח מרוכז
    lines = ["# דוח מרוכז - חשודים בלבד\n",
             f"נבדקו {len(sites)} אתרים.\n",
             f"**חשודים (דורשים בדיקת אדם): {len(suspects)}** | תקינים: {len(clean)} | לא נבדקו: {len(errors)}\n", "---\n"]
    if suspects:
        for url, platform, n, hi in suspects:
            lines.append(f"\n## 🔎 {url}  ({n} מוצרים)")
            for i in hi:
                lines.append(f"- 🔴 **{i.kind}**: {i.detail}")
    else:
        lines.append("\nלא נמצאו חשודים חמורים בסבב הזה. (אתרים מסודרים = נורמלי. צריך לסרוק עוד.)")
    lines.append("\n---\n### תקינים")
    lines += [f"- ✅ {u} ({n} מוצרים)" for u, n in clean]
    if errors:
        lines.append("\n### לא נבדקו / לא חנות")
        lines += [f"- ⚠️ {u} — {why}" for u, why in errors]
    with open("reports/_SUMMARY.md", "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()

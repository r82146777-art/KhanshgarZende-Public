#!/usr/bin/env python3
"""v5.9b: fix customBaseUrl + TextViewer pageTurn injection."""
from pathlib import Path
import os, re, subprocess, sys

root = Path(__file__).resolve().parent
r = subprocess.run([sys.executable, str(root / "patch_v59.py")], check=False)
print("v59", r.returncode)

proj = Path(os.environ["PROJ"])
src = proj / "app/src/main/java/com/example/khanshgarzende"

prefs = src / "Prefs.kt"
pt = prefs.read_text(encoding="utf-8")
if "customBaseUrl" not in pt:
    idx = pt.rfind("}")
    pt = pt[:idx] + '''
    var customBaseUrl: String
        get() = sp.getString("custom_base_url", "") ?: ""
        set(v) = sp.edit().putString("custom_base_url", v).apply()
''' + pt[idx:]
    prefs.write_text(pt, encoding="utf-8")
    print("added customBaseUrl")
if "unifiedApiKey" not in pt:
    pt = prefs.read_text(encoding="utf-8")
    idx = pt.rfind("}")
    pt = pt[:idx] + '''
    var unifiedApiKey: String
        get() = sp.getString("unified_api_key", "") ?: ""
        set(v) = sp.edit().putString("unified_api_key", v).apply()
''' + pt[idx:]
    prefs.write_text(pt, encoding="utf-8")
    print("added unifiedApiKey")

tv = src / "TextViewerActivity.kt"
if tv.exists():
    tt = tv.read_text(encoding="utf-8")
    tt = re.sub(
        r'try \{ app\.speech\.pageTurnClick\(\) \} catch \(_: Throwable\) \{\}\s*\n\s*setLastPage\(',
        'setLastPage(',
        tt,
    )
    if "pageTurnClick" not in tt:
        if "currentPage =" in tt:
            tt = tt.replace(
                "currentPage =",
                "try { app.speech.pageTurnClick() } catch (_: Throwable) {}\n        currentPage =",
                1,
            )
            print("TextViewer: wired via currentPage =")
        elif "pageIndex =" in tt:
            tt = tt.replace(
                "pageIndex =",
                "try { app.speech.pageTurnClick() } catch (_: Throwable) {}\n        pageIndex =",
                1,
            )
            print("TextViewer: wired via pageIndex =")
        else:
            print("TextViewer: no safe injection point; skip pageTurn wire")
    else:
        print("TextViewer: pageTurn present after cleanup")
    tv.write_text(tt, encoding="utf-8")

sa = src / "SettingsActivity.kt"
sat = sa.read_text(encoding="utf-8")
sat = sat.replace(
    "findViewById<EditText?>(R.id.et_custom_base_url)?.setText(p.customBaseUrl)",
    "findViewById<EditText?>(R.id.et_custom_base_url)?.setText(try { p.customBaseUrl } catch (_: Throwable) { \"\" })",
)
sa.write_text(sat, encoding="utf-8")

bg = proj / "app/build.gradle.kts"
bt = bg.read_text(encoding="utf-8")
bt = re.sub(r"versionCode\s*=\s*\d+", "versionCode = 59", bt)
bt = re.sub(r'versionName\s*=\s*"[^"]*"', 'versionName = "5.9"', bt)
bg.write_text(bt, encoding="utf-8")
print("v5.9b DONE")

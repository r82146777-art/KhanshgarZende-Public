#!/usr/bin/env python3
"""v5.4c: fix ocr.recognize arity + gallery field names."""
from pathlib import Path
import os
import re

proj = Path(os.environ['PROJ'])
src = proj / 'app/src/main/java/com/example/khanshgarzende'

for name in ('CameraActivity.kt', 'BatchScanActivity.kt'):
    f = src / name
    if not f.exists():
        continue
    t = f.read_text(encoding='utf-8')
    t2 = re.sub(r'ocr\.recognize\(([^,\)]+)\)', r'ocr.recognize(\1, false)', t)
    t2 = t2.replace(', false, false)', ', false)')
    # Fix wrong field/method names from gallery inject
    t2 = t2.replace('lastText = cleaned', 'lastReadText = cleaned')
    t2 = t2.replace('showText(cleaned)',
                    'textView.text = cleaned; textView.visibility = android.view.View.VISIBLE; '
                    'scroll.visibility = android.view.View.VISIBLE; btnSave.isEnabled = true')
    t2 = t2.replace('findViewById<Button>(R.id.btn_save)?.isEnabled = true', 'btnSave.isEnabled = true')
    if t2 != t:
        f.write_text(t2, encoding='utf-8')
        print(name, 'fixed')
    else:
        print(name, 'no change')

print('v5.4c done')

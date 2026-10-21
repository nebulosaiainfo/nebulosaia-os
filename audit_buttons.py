import re

with open(r'D:\NEXO_CRM_BASE\frontend\public\index.html', encoding='utf-8') as f:
    text = f.read()

print("Modules found:", re.findall(r'id=["\'](module-[^"\']+)["\']', text))
print("Tab buttons found:", re.findall(r'id=["\'](tab-btn-[^"\']+)["\']', text))

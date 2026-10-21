import os
from pathlib import Path

# 1. Update main.py
main_py = Path(r"D:\NEXO_CRM_BASE\backend\app\main.py")
content = main_py.read_text(encoding="utf-8")
old_base = 'BASE_DIR = Path(r"D:\\NEXO_CRM_BASE")'
new_base = 'BASE_DIR = Path(__file__).resolve().parent.parent.parent'
if old_base in content:
    content = content.replace(old_base, new_base)
    main_py.write_text(content, encoding="utf-8")
    print("main.py updated!")
else:
    print("old_base not found or already replaced in main.py")

# 2. Update factura_pdf_service.py
factura_py = Path(r"D:\NEXO_CRM_BASE\backend\app\services\factura_pdf_service.py")
f_content = factura_py.read_text(encoding="utf-8")
old_f = 'PDF_OUTPUT_DIR = Path(r"D:\\NEXO_CRM_BASE\\01_Core_Facturacion\\facturas_pdf")'
new_f = 'PDF_OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent.parent / "01_Core_Facturacion" / "facturas_pdf"'
if old_f in f_content:
    f_content = f_content.replace(old_f, new_f)
    factura_py.write_text(f_content, encoding="utf-8")
    print("factura_pdf_service.py updated!")
else:
    print("factura_pdf_service already updated or not found")

# 3. Create requirements.txt
req_txt = Path(r"D:\NEXO_CRM_BASE\requirements.txt")
requirements = """fastapi>=0.110.0
uvicorn>=0.28.0
pydantic>=2.0.0
sqlalchemy>=2.0.0
python-multipart>=0.0.9
reportlab>=4.0.0
fpdf2>=2.7.0
openpyxl>=3.1.0
requests>=2.31.0
jinja2>=3.1.0
"""
req_txt.write_text(requirements, encoding="utf-8")
print("requirements.txt created!")

# 4. Create .gitignore
gitignore = Path(r"D:\NEXO_CRM_BASE\.gitignore")
git_ignore_content = """__pycache__/
*.py[cod]
*$py.class
*.so
.env
cloudflared.exe
mingit/
.git/
"""
gitignore.write_text(git_ignore_content, encoding="utf-8")
print(".gitignore created!")

# 5. Create render.yaml
render_yaml = Path(r"D:\NEXO_CRM_BASE\render.yaml")
yaml_content = """services:
  - type: web
    name: nebulosa-os
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
    plan: free
"""
render_yaml.write_text(yaml_content, encoding="utf-8")
print("render.yaml created!")

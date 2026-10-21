from pathlib import Path

# Create __init__.py files
for d in ["backend", "backend/app", "backend/app/services", "backend/app/models"]:
    init_path = Path(r"D:\NEXO_CRM_BASE") / d / "__init__.py"
    init_path.parent.mkdir(parents=True, exist_ok=True)
    if not init_path.exists():
        init_path.write_text("# package marker\n", encoding="utf-8")
        print(f"Created {init_path}")

# Update main.py
main_py = Path(r"D:\NEXO_CRM_BASE\backend\app\main.py")
content = main_py.read_text(encoding="utf-8")

# Add sys.path insertion right after BASE_DIR
target = 'DATA_DIR = BASE_DIR / "backend" / "data"'
addition = '''DATA_DIR = BASE_DIR / "backend" / "data"
import sys
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
if str(BASE_DIR / "backend") not in sys.path:
    sys.path.insert(0, str(BASE_DIR / "backend"))'''

if target in content and "sys.path.insert" not in content:
    content = content.replace(target, addition)
    print("Added sys.path to main.py")

old_imports = """from app.services.factura_pdf_service import generar_pdf_factura, enviar_factura_correo
from app.services.gemini_analytics_service import analizar_tendencias_wms_con_gemini
from app.services.reporte_excel_service import generar_reporte_excel_completo"""

new_imports = """try:
    from backend.app.services.factura_pdf_service import generar_pdf_factura, enviar_factura_correo
    from backend.app.services.gemini_analytics_service import analizar_tendencias_wms_con_gemini
    from backend.app.services.reporte_excel_service import generar_reporte_excel_completo
except ImportError:
    from app.services.factura_pdf_service import generar_pdf_factura, enviar_factura_correo
    from app.services.gemini_analytics_service import analizar_tendencias_wms_con_gemini
    from app.services.reporte_excel_service import generar_reporte_excel_completo"""

if old_imports in content:
    content = content.replace(old_imports, new_imports)
    print("Replaced app.services imports with robust imports")

main_py.write_text(content, encoding="utf-8")
print("Done fixing main.py")

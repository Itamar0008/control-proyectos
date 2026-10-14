# Control y seguimiento de proyectos — Streamlit

## Archivos
- `app.py`: aplicación Streamlit.
- `requirements.txt`: dependencias.

## Ejecutar localmente
1. Instala Python 3.11 o 3.12.
2. Abre una terminal dentro de esta carpeta.
3. Ejecuta:
   ```bash
   python -m venv .venv
   ```
4. Activa el entorno:
   - Windows: `.venv\Scripts\activate`
5. Instala dependencias:
   ```bash
   pip install -r requirements.txt
   ```
6. Inicia:
   ```bash
   streamlit run app.py
   ```

## Importante
La primera versión usa SQLite local para probar el flujo. No uses información institucional sensible ni despliegues esta versión tal cual en Community Cloud esperando que la base de datos local persista. Para producción, conecta una base de datos persistente aprobada por tu institución.

La app no sincroniza automáticamente con Planner ni OneNote; permite registrar enlaces y mantener una vista central.

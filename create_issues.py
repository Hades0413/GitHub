import requests
import json
import os
from dotenv import load_dotenv
from datetime import datetime

# Configuración visual
LINEA = "═" * 60
EMOJI = {
    "config": "⚙️",
    "error": "❌",
    "success": "✅",
    "warning": "⚠️",
    "issue": "📌",
    "progress": "🔄",
    "link": "🔗"
}

def print_header(text):
    print(f"\n{LINEA}")
    print(f"{text.center(60)}")
    print(f"{LINEA}")

def print_colored(text, color_code):
    print(f"\033[{color_code}m{text}\033[0m")

# Configuración
GITHUB_API_URL = 'https://api.github.com'

# Cargar variables de entorno
load_dotenv()

# Obtener variables
AUTH_TOKEN = os.getenv('GITHUB_TOKEN')
REPO_OWNER = os.getenv('REPO_OWNER')
REPO_NAME = os.getenv('REPO_NAME')

# Encabezado inicial
print_header("GITHUB ISSUE CREATOR v2.0")
print(f"{EMOJI['config']} Cargando configuración...")

# Validar variables de entorno
missing_vars = []
if not AUTH_TOKEN: missing_vars.append("GITHUB_TOKEN")
if not REPO_OWNER: missing_vars.append("REPO_OWNER")
if not REPO_NAME: missing_vars.append("REPO_NAME")

if missing_vars:
    print(f"\n{EMOJI['error']} Error en configuración:")
    for var in missing_vars:
        print(f" - Variable faltante: {var}")
    print(f"\n{EMOJI['warning']} Verifica tu archivo .env")
    exit()

# Mostrar configuración cargada
print(f"\n{EMOJI['success']} Configuración válida:")
print(f" - Repositorio: {REPO_OWNER}/{REPO_NAME}")
print(f" - Token: {AUTH_TOKEN[:4]}...{AUTH_TOKEN[-4:]}")

def create_issue(title, body, issue_num, total):
    try:
        # Configurar solicitud
        url = f"{GITHUB_API_URL}/repos/{REPO_OWNER}/{REPO_NAME}/issues"
        headers = {
            'Authorization': f'token {AUTH_TOKEN}',
            'Accept': 'application/vnd.github.v3+json'
        }
        data = {
            'title': title,
            'body': body
        }

        # Mostrar progreso
        progress = f"[{issue_num}/{total}]"
        print(f"\n{EMOJI['progress']} {progress} Creando issue: {title[:30]}...")
        
        # Enviar solicitud
        start_time = datetime.now()
        response = requests.post(url, headers=headers, json=data)
        elapsed = (datetime.now() - start_time).total_seconds()

        # Procesar respuesta
        if response.status_code == 201:
            issue = response.json()
            print(f"{EMOJI['success']} {progress} Issue creado en {elapsed:.2f}s")
            print(f"{EMOJI['link']} URL: {issue['html_url']}")
            return True
        else:
            print(f"{EMOJI['error']} {progress} Error {response.status_code}")
            print(f"Respuesta: {response.text[:200]}...")
            return False

    except Exception as e:
        print(f"{EMOJI['error']} {progress} Error crítico: {str(e)}")
        return False

# Creación de issues
total_issues = 20
success_count = 0
failed_count = 0

print_header(f"INICIANDO CREACIÓN DE {total_issues} ISSUES")

for i in range(1, total_issues + 1):
    title = f'Issue {i} - {datetime.now().strftime("%Y-%m-%d")}'
    body = f"""## Descripción del issue {i}
    
Este es un issue generado automáticamente el {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    
**Detalles:**
- Prioridad: Alta
- Tipo: Mejora
- Asignado: Equipo de desarrollo"""
    
    if create_issue(title, body, i, total_issues):
        success_count += 1
    else:
        failed_count += 1

# Resumen final
print_header("RESUMEN DE EJECUCIÓN")
print(f"{EMOJI['success']} Issues exitosos: {success_count}")
print(f"{EMOJI['error']} Issues fallidos: {failed_count}")
print(f"{EMOJI['issue']} Total procesados: {success_count + failed_count}")

if failed_count == 0:
    print_colored("\n¡TODOS LOS ISSUES SE CREARON EXITOSAMENTE!", "32")
else:
    print_colored(f"\n{EMOJI['warning']} ALGUNOS ISSUES TUVIERON PROBLEMAS", "33")

print_header("PROCESO COMPLETADO")
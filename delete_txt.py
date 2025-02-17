import os
import sys
import subprocess
import requests
from dotenv import load_dotenv
import json
from datetime import datetime

# Configuración visual
LINEA = "═" * 50
EMOJI = {
    "config": "⚙️",
    "error": "❌",
    "success": "✅",
    "warning": "⚠️",
    "file": "📄",
    "git": "🐙",
    "trash": "🗑️",
    "time": "⏱️"
}

def print_header(text):
    print(f"\n{LINEA}")
    print(f"{text.center(50)}")
    print(f"{LINEA}")

# Cargar variables de entorno
load_dotenv()

# Configuración
TOKEN = os.getenv('GITHUB_TOKEN')
REPO_OWNER = os.getenv('REPO_OWNER')
REPO_NAME = os.getenv('REPO_NAME')
BASE_BRANCH = os.getenv('BASE_BRANCH', 'main')

# Validar configuración
missing_vars = []
if not TOKEN: missing_vars.append("GITHUB_TOKEN")
if not REPO_OWNER: missing_vars.append("REPO_OWNER")
if not REPO_NAME: missing_vars.append("REPO_NAME")

if missing_vars:
    print_header("ERROR DE CONFIGURACIÓN")
    print(f"{EMOJI['error']} Variables faltantes en .env:")
    for var in missing_vars:
        print(f" - {var}")
    sys.exit(1)

# Mostrar información inicial
print_header("ELIMINADOR DE ARCHIVOS TXT")
print(f"{EMOJI['config']} Repositorio: {REPO_OWNER}/{REPO_NAME}")
print(f"{EMOJI['git']} Rama base: {BASE_BRANCH}")
print(f"{EMOJI['time']} Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

BASE_URL = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/'
headers = {
    'Authorization': f'token {TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

def get_all_files(url=BASE_URL):
    """Obtiene recursivamente todos los archivos .txt"""
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return []
        
        files = []
        for item in response.json():
            if item['type'] == 'dir':
                files.extend(get_all_files(item['url']))
            elif item['name'].endswith('.txt'):
                files.append(item['path'])
        return files
    except Exception as e:
        print(f"{EMOJI['error']} Error: {str(e)}")
        return []

def get_txt_files():
    print(f"\n{EMOJI['file']} Buscando archivos .txt...")
    files = get_all_files()
    for file in files:
        print(f" {EMOJI['file']} Encontrado: {file}")
    return files

def get_file_sha(file_path):
    try:
        response = requests.get(f'{BASE_URL}{file_path}', headers=headers)
        return response.json().get('sha') if response.status_code == 200 else None
    except Exception as e:
        print(f"{EMOJI['error']} Error obteniendo SHA: {str(e)}")
        return None

def delete_txt_files():
    txt_files = get_txt_files()
    if not txt_files:
        print(f"\n{EMOJI['warning']} No se encontraron archivos .txt")
        return 0, 0
    
    success = 0
    errors = 0
    print_header("PROCESO DE ELIMINACIÓN")
    
    for idx, file in enumerate(txt_files, 1):
        print(f"\n{EMOJI['trash']} [{idx}/{len(txt_files)}] Eliminando: {file}")
        
        sha = get_file_sha(file)
        if not sha:
            errors += 1
            continue
            
        data = {
            'message': f'Eliminación automática de {file}',
            'sha': sha
        }
        
        try:
            response = requests.delete(
                f'{BASE_URL}{file}',
                headers=headers,
                data=json.dumps(data)
            )
            
            if response.status_code == 200:
                print(f" {EMOJI['success']} Eliminado correctamente")
                success += 1
            else:
                print(f" {EMOJI['error']} Error {response.status_code}")
                errors += 1
        except Exception as e:
            print(f" {EMOJI['error']} Excepción: {str(e)}")
            errors += 1
    
    return success, errors

def git_operations():
    """Realiza operaciones Git solo si hay cambios"""
    print_header("OPERACIONES GIT")
    
    # Verificar cambios
    try:
        status = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True,
            text=True,
            check=True
        )
        if not status.stdout.strip():
            print(f"{EMOJI['warning']} No hay cambios para confirmar")
            return True
    except subprocess.CalledProcessError as e:
        print(f"{EMOJI['error']} Error verificando estado: {str(e)}")
        return False

    commands = [
        ("Sincronizando repositorio", ["git", "checkout", BASE_BRANCH]),
        ("Actualizando cambios", ["git", "pull", "origin", BASE_BRANCH]),
        ("Confirmando cambios", ["git", "add", "."]),
        ("Creando commit", ["git", "commit", "-m", "Eliminados archivos .txt"]),
        ("Enviando cambios", ["git", "push", "origin", BASE_BRANCH])
    ]
    
    for desc, cmd in commands:
        print(f"\n{EMOJI['git']} {desc}...")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f" {EMOJI['error']} Error:\n{result.stderr}")
                return False
            print(f" {EMOJI['success']} Éxito")
        except Exception as e:
            print(f" {EMOJI['error']} Excepción: {str(e)}")
            return False
    return True

def main():
    start_time = datetime.now()
    deleted, errors = delete_txt_files()
    
    if deleted > 0:
        print_header("CONFIRMACIÓN DE CAMBIOS")
        if not git_operations():
            print(f"\n{EMOJI['error']} Error al confirmar cambios")
    
    # Resumen final
    print_header("RESUMEN EJECUCIÓN")
    print(f"{EMOJI['success']} Archivos eliminados: {deleted}")
    print(f"{EMOJI['error']} Errores durante proceso: {errors}")
    print(f"{EMOJI['time']} Duración: {datetime.now() - start_time}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{EMOJI['error']} Proceso cancelado por el usuario")
        sys.exit(1)
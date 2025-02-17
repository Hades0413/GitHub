import os
import random
import subprocess
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Configuración desde .env
token = os.getenv('GITHUB_TOKEN')
repo_owner = os.getenv('REPO_OWNER')
repo_name = os.getenv('REPO_NAME')
base_branch = os.getenv('BASE_BRANCH')
user_email = os.getenv('USER_EMAIL')

CONFIG = {
    'prs_por_mes': 3,
    'año': 2022,
    'mes_inicio': 3,
    'mes_fin': 4,
    'hora_inicio': 9,
    'hora_fin': 18,
    'zona_horaria': '-0500'
}

if not all([token, repo_owner, repo_name, base_branch, user_email]):
    print("Error: Faltan variables en .env")
    exit()

env = os.environ.copy()
env['GITHUB_TOKEN'] = token

def run_git_command(command, print_output=True, custom_env=None):
    """Ejecuta comandos git con manejo de errores mejorado"""
    try:
        if print_output:
            print(f"Ejecutando: {command}")
        subprocess.run(
            command,
            shell=True,
            check=True,
            env=custom_env if custom_env else env,
            capture_output=not print_output
        )
    except subprocess.CalledProcessError as e:
        print(f"Error en comando: {command}")
        print(f"Detalles: {e.stderr.decode().strip()}")
        exit()

def generar_fecha_aleatoria(mes, año):
    """Genera fechas válidas considerando años bisiestos"""
    if mes == 2:
        bisiesto = (año % 4 == 0 and (año % 100 != 0 or año % 400 == 0))
        return random.randint(1, 29 if bisiesto else 28)
    dias_por_mes = {
        1: 31, 3: 31, 4: 30, 5: 31, 6: 30,
        7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31
    }
    return random.randint(1, dias_por_mes.get(mes, 30))

def crear_pr(datos_pr):
    """Crea un PR usando la API de GitHub"""
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        response = requests.post(url, json=datos_pr, headers=headers)
        response.raise_for_status()
        return response.json()['number']
    except requests.exceptions.RequestException as e:
        print(f"Error creando PR: {str(e)}")
        return None

def configurar_entorno_fechas(fecha):
    """Configura variables de entorno para fechas específicas"""
    fecha_str = fecha.strftime("%Y-%m-%d %H:%M:%S") + CONFIG['zona_horaria']
    return {
        'GIT_AUTHOR_DATE': fecha_str,
        'GIT_COMMITTER_DATE': fecha_str
    }

def crear_y_mergear_pr(mes, año, pr_num):
    """Crea y mergea un PR con fecha histórica"""
    dia = generar_fecha_aleatoria(mes, año)
    hora = random.randint(CONFIG['hora_inicio'], CONFIG['hora_fin'])
    minuto = random.randint(0, 59)
    fecha_commit = datetime(año, mes, dia, hora, minuto)
    
    # Configurar entorno con fechas
    env_commit = env.copy()
    env_commit.update(configurar_entorno_fechas(fecha_commit))
    
    branch_name = f"pr/{fecha_commit.strftime('%Y%m%d')}-{pr_num:03d}"
    
    try:
        # Configuración inicial
        run_git_command('git checkout main', False)
        run_git_command('git pull origin main', False)
        
        # Crear rama y commit
        run_git_command(f'git checkout -b {branch_name}', False, env_commit)
        with open('historial.txt', 'a') as f:
            f.write(f"PR {pr_num} - {fecha_commit.isoformat()}\n")
        
        run_git_command('git add historial.txt', False, env_commit)
        commit_msg = f"PR {pr_num} - {fecha_commit.strftime('%Y-%m-%d %H:%M')}"
        run_git_command(f'git commit -m "{commit_msg}"', False, env_commit)
        
        # Push con fecha histórica
        run_git_command(f'git push -u origin {branch_name}', False, env_commit)
        
        # Crear PR
        pr_data = {
            "title": f"PR {pr_num} - {fecha_commit.strftime('%Y-%m')}",
            "head": branch_name,
            "base": base_branch,
            "body": f"PR generado automáticamente\nFecha: {fecha_commit}"
        }
        pr_number = crear_pr(pr_data)
        
        if pr_number:
            # Merge con fecha histórica
            merge_env = env.copy()
            merge_env.update(configurar_entorno_fechas(fecha_commit))
            
            # Realizar merge local
            run_git_command('git checkout main', False, merge_env)
            merge_msg = f"Merge PR #{pr_number} ({fecha_commit.strftime('%Y-%m-%d')})"
            
            # Comando de merge corregido (sin --date)
            run_git_command(
                f'git merge --no-ff {branch_name} -m "{merge_msg}"',
                False,
                merge_env
            )
            
            # Push del merge con fecha correcta
            run_git_command('git push origin main', False, merge_env)

    finally:
        # Limpieza de ramas
        run_git_command('git checkout main', False)
        run_git_command(f'git branch -D {branch_name}', False)
        run_git_command(f'git push origin --delete {branch_name}', False)

# Ejecución principal
print("🏁 Iniciando generación y merge de PRs históricos")
for mes in range(CONFIG['mes_inicio'], CONFIG['mes_fin'] + 1):
    print(f"\n📅 Procesando {mes:02d}/{CONFIG['año']}")
    for pr_num in range(1, CONFIG['prs_por_mes'] + 1):
        print(f"🔄 Procesando PR {pr_num}/{CONFIG['prs_por_mes']}")
        crear_y_mergear_pr(mes, CONFIG['año'], pr_num)

print("\n✅ Todos los PRs han sido mergeados correctamente")
print("⚠️ Verifica en GitHub que los commits y merges muestren las fechas correctas")
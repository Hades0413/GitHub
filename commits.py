import os
import random
import subprocess
from dotenv import load_dotenv
from datetime import datetime

# Configuración visual
LINEA = "═" * 50
EMOJI = {
    "config": "⚙️",
    "commit": "📌",
    "mes": "📅",
    "progreso": "🔄",
    "exito": "✅",
    "error": "❌",
    "usuario": "👤",
    "push": "🚀"
}

def mostrar_titulo(texto):
    print(f"\n{LINEA}")
    print(f"{EMOJI['mes']} {texto.center(48)} {EMOJI['mes']}")
    print(f"{LINEA}\n")

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Obtener las variables desde el archivo .env
token = os.getenv('GITHUB_TOKEN')  
repo_owner = os.getenv('REPO_OWNER')  
repo_name = os.getenv('REPO_NAME')  
base_branch = os.getenv('BASE_BRANCH')  
user_email = os.getenv('USER_EMAIL')

# Verificar que todas las variables estén presentes
if not all([token, repo_owner, repo_name, base_branch, user_email]):
    print(f"\n{EMOJI['error']} Faltan variables de entorno en el archivo .env.")
    exit()

# Configurar el entorno para subprocess
env = os.environ.copy()
env['GITHUB_TOKEN'] = token

def run_git_command(command, print_output=True):
    """Ejecuta comandos git con manejo de errores"""
    try:
        if print_output:
            print(f"{EMOJI['progreso']} Ejecutando: {command}")
        resultado = subprocess.run(
            command, 
            shell=True, 
            check=True, 
            env=env,
            capture_output=True,
            text=True
        )
        if print_output and resultado.stdout:
            print(resultado.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n{EMOJI['error']} Error en comando: {command}")
        print(f"{EMOJI['error']} Detalles: {e.stderr.strip()}")
        exit()

# Configuración inicial
mostrar_titulo("INICIANDO PROCESO DE COMMITS")
print(f"{EMOJI['config']} Configurando entorno...")

# Sincronizar repositorio
print(f"\n{EMOJI['progreso']} Sincronizando con el repositorio remoto")
run_git_command(f'git pull https://{repo_owner}:{token}@github.com/{repo_owner}/{repo_name}.git {base_branch}', False)

# Configurar usuario Git
print(f"\n{EMOJI['usuario']} Configurando identidad Git:")
run_git_command(f'git config --local user.name "{repo_owner}"', False)
run_git_command(f'git config --local user.email "{user_email}"', False)

# Mostrar configuración
print(f"\n{EMOJI['config']} Configuración actual:")
run_git_command('git config user.name', True)
run_git_command('git config user.email', True)

# Función para generar fecha
def generar_fecha_aleatoria(mes, año):
    dias_por_mes = {
        1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30,
        7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31
    }
    return random.randint(1, dias_por_mes[mes])

# Función para crear commits
def crear_commit(mes, i, año):
    rand_day = generar_fecha_aleatoria(mes, año)
    commit_date = datetime(año, mes, rand_day, 17, 51)
    
    with open('test.txt', 'a') as file:
        file.write(f"Commit {(mes - 1) * commits_por_mes + i + 1}\n")
    
    # Mostrar progreso
    print(f"{EMOJI['progreso']} [{i+1}/{commits_por_mes}] Creando commit para {commit_date.strftime('%d/%m/%Y')}", end='\r')
    
    run_git_command(f'git add test.txt', False)
    run_git_command(f'git commit --date="{commit_date.isoformat()}" -m "Commit {(mes - 1) * commits_por_mes + i + 1}"', False)

# Parámetros de ejecución
commits_por_mes = 20      # Commits por mes
año = 2025               # Año objetivo
mes_inicio = 1           # Mes inicial (1-12)
mes_fin = 1              # Mes final (1-12)

# Validar rango de meses
if not (1 <= mes_inicio <= 12 and 1 <= mes_fin <= 12):
    print(f"\n{EMOJI['error']} Rango de meses inválido (debe ser entre 1-12)")
    exit()

# Proceso principal
try:
    total_meses = mes_fin - mes_inicio + 1
    commits_totales = commits_por_mes * total_meses
    
    mostrar_titulo(f"CONFIGURACIÓN INICIAL")
    print(f"{EMOJI['mes']} Rango seleccionado: {mes_inicio:02d}-{mes_fin:02d}/{año}")
    print(f"{EMOJI['commit']} Commits por mes: {commits_por_mes}")
    print(f"{EMOJI['exito']} Total estimado: {commits_totales} commits")

    for mes in range(mes_inicio, mes_fin + 1):
        mostrar_titulo(f"PROCESANDO MES {mes:02d}/{año}")
        
        for i in range(commits_por_mes):
            crear_commit(mes, i, año)
        
        print(f"\n{EMOJI['exito']} Mes {mes:02d} completado: {commits_por_mes} commits")

    # Push final
    mostrar_titulo("ENVIANDO CAMBIOS")
    print(f"{EMOJI['push']} Realizando push de {commits_totales} commits...")
    run_git_command(f'git push https://{repo_owner}:{token}@github.com/{repo_owner}/{repo_name}.git {base_branch}', True)
    
    # Confirmación final
    print(f"\n{LINEA}")
    print(f"{EMOJI['exito']} PUSH EXITOSO!".center(50))
    print(f"{LINEA}")
    print(f"🗓️  Rango de meses: {mes_inicio:02d}-{mes_fin:02d}/{año}")
    print(f"📌 Total commits: {commits_totales}")
    print(f"{EMOJI['usuario']} Autor: {repo_owner} <{user_email}>")
    print(f"🌐 Repositorio: github.com/{repo_owner}/{repo_name}")
    print(LINEA)

except KeyboardInterrupt:
    print(f"\n\n{EMOJI['error']} PROCESO CANCELADO POR EL USUARIO")
    exit()
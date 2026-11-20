import os
import random
import subprocess
import requests
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
from dotenv import load_dotenv

import theme

# Cargar variables de entorno si existen
load_dotenv()

class GitHubPRCreatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Generar PRs")
        self.geometry("800x880")
        self.minsize(640, 720)
        self.resizable(True, True)
        theme.apply_theme(self)
        self._create_widgets()
        self._load_env_if_exists()

    def _create_widgets(self):
        sp = theme.SPACE
        main_frame = ttk.Frame(self, padding=sp["lg"])
        main_frame.pack(fill=tk.BOTH, expand=True)

        config_frame = ttk.LabelFrame(main_frame, text="Repositorio", padding=sp["md"])
        config_frame.pack(fill=tk.X, pady=(0, sp["md"]))

        fields = [
            ("Token de GitHub", 'GITHUB_TOKEN'),
            ("Dueño del repo", 'REPO_OWNER'),
            ("Nombre del repo", 'REPO_NAME'),
            ("Rama base", 'BASE_BRANCH'),
            ("Email del usuario", 'USER_EMAIL')
        ]

        self.entries = {}
        for text, key in fields:
            row = ttk.Frame(config_frame)
            row.pack(fill=tk.X, pady=sp["xs"])
            ttk.Label(row, text=text, width=theme.LABEL_WIDTH).pack(side=tk.LEFT)
            entry = ttk.Entry(row)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.entries[key] = entry
        theme.mask_token(self.entries['GITHUB_TOKEN'])

        params_frame = ttk.LabelFrame(main_frame, text="PRs a generar", padding=sp["md"])
        params_frame.pack(fill=tk.X, pady=(0, sp["md"]))

        self.entries['PRS_POR_MES'] = self._create_spinbox(params_frame, "PRs por mes", 1, 10)
        self.entries['AÑO'] = self._create_spinbox(params_frame, "Año", 2008, 2025)
        self.entries['MES_INICIO'] = self._create_spinbox(params_frame, "Mes inicio", 1, 12)
        self.entries['MES_FIN'] = self._create_spinbox(params_frame, "Mes fin", 1, 12)
        self.entries['HORA_INICIO'] = self._create_spinbox(params_frame, "Hora inicio", 0, 23)
        self.entries['HORA_FIN'] = self._create_spinbox(params_frame, "Hora fin", 0, 23)

        exec_frame = ttk.Frame(main_frame)
        exec_frame.pack(fill=tk.X, pady=(0, sp["md"]))
        ttk.Button(exec_frame, text="Generar PRs", style="Accent.TButton",
                   command=self._execute).pack(side=tk.LEFT, padx=(0, sp["sm"]))
        ttk.Button(exec_frame, text="Limpiar consola", command=self.clear_console).pack(side=tk.LEFT)

        self.output = theme.make_console(
            main_frame, height=12,
            placeholder="Aquí verás cada PR, mes a mes, cuando pulses Generar PRs.")
        self.output.pack(fill=tk.BOTH, expand=True)

    def _create_spinbox(self, parent, label_text, from_, to):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=theme.SPACE["xs"])
        ttk.Label(frame, text=label_text, width=theme.SPIN_LABEL_WIDTH).pack(side=tk.LEFT)
        spinbox = ttk.Spinbox(frame, from_=from_, to=to, width=8)
        spinbox.pack(side=tk.LEFT)
        return spinbox

    def _load_env_if_exists(self):
        if os.path.exists('.env'):
            load_dotenv()
            for key in self.entries:
                if key in os.environ:
                    self.entries[key].insert(0, os.getenv(key))

    def _validate_inputs(self):
        try:
            data = {
                'prs_por_mes': int(self.entries['PRS_POR_MES'].get()),
                'año': int(self.entries['AÑO'].get()),
                'mes_inicio': int(self.entries['MES_INICIO'].get()),
                'mes_fin': int(self.entries['MES_FIN'].get()),
                'hora_inicio': int(self.entries['HORA_INICIO'].get()),
                'hora_fin': int(self.entries['HORA_FIN'].get())
            }

            if data['prs_por_mes'] < 1 or data['prs_por_mes'] > 10:
                messagebox.showerror("Revisa PRs por mes", "PRs por mes debe estar entre 1 y 10.")
                return None

            return data

        except ValueError:
            messagebox.showerror("Revisa los parámetros",
                                 "PRs por mes, Año, Mes inicio, Mes fin, Hora inicio y Hora fin "
                                 "deben ser números enteros.")
            return None

    def _execute(self):
        self.output.delete(1.0, tk.END)

        params = self._validate_inputs()
        if not params:
            return

        load_dotenv()
        token = os.getenv('GITHUB_TOKEN')
        repo_owner = os.getenv('REPO_OWNER')
        repo_name = os.getenv('REPO_NAME')
        base_branch = os.getenv('BASE_BRANCH')
        user_email = os.getenv('USER_EMAIL')

        if not all([token, repo_owner, repo_name, base_branch, user_email]):
            messagebox.showerror("Falta el archivo .env",
                                 "Esta ventana lee GITHUB_TOKEN, REPO_OWNER, REPO_NAME, BASE_BRANCH "
                                 "y USER_EMAIL desde .env. Créalo a partir de .env.example y vuelve a intentarlo.")
            return

        # Aquí empieza el proceso de creación y fusión de PRs, similar al script original
        print("🏁 Iniciando generación y merge de PRs históricos")
        for mes in range(params['mes_inicio'], params['mes_fin'] + 1):
            theme.log_section(self.output, f"Mes {mes:02d}/{params['año']}")
            for pr_num in range(1, params['prs_por_mes'] + 1):
                self.output_insert(f"🔄 Procesando PR {pr_num}/{params['prs_por_mes']}\n")
                self.crear_y_mergear_pr(mes, params['año'], pr_num)

        theme.log_section(self.output, "Resumen")
        self.output_insert("✅ Todos los PRs se crearon y se fusionaron.\n")
        self.output_insert("⚠️ Abre el repo en GitHub y comprueba que commits y merges muestran las fechas elegidas.\n")

    def output_insert(self, text: str):
        theme.log(self.output, text)

    def clear_console(self):
        """Limpiar el área de texto de la consola"""
        self.output.delete(1.0, tk.END)

    def run_git_command(self, command, print_output=True, custom_env=None):
        """Ejecuta comandos git con manejo de errores mejorado"""
        try:
            if print_output:
                self.output_insert(f"Ejecutando: {command}")
            subprocess.run(
                command,
                shell=True,
                check=True,
                env=custom_env if custom_env else os.environ,
                capture_output=not print_output
            )
        except subprocess.CalledProcessError as e:
            self.output_insert(f"❌ Falló el comando: {command}")
            self.output_insert(f"Detalles: {e.stderr.decode().strip()}")
            exit()

    def generar_fecha_aleatoria(self, mes, año):
        """Genera fechas válidas considerando años bisiestos"""
        if mes == 2:
            bisiesto = (año % 4 == 0 and (año % 100 != 0 or año % 400 == 0))
            return random.randint(1, 29 if bisiesto else 28)
        dias_por_mes = {
            1: 31, 3: 31, 4: 30, 5: 31, 6: 30,
            7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31
        }
        return random.randint(1, dias_por_mes.get(mes, 30))

    def crear_pr(self, datos_pr):
        """Crea un PR usando la API de GitHub"""
        url = f"https://api.github.com/repos/{os.getenv('REPO_OWNER')}/{os.getenv('REPO_NAME')}/pulls"
        headers = {
            "Authorization": f"token {os.getenv('GITHUB_TOKEN')}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        try:
            response = requests.post(url, json=datos_pr, headers=headers)
            response.raise_for_status()
            return response.json()['number']
        except requests.exceptions.RequestException as e:
            self.output_insert(f"❌ No se pudo crear el PR: {str(e)}")
            return None

    def configurar_entorno_fechas(self, fecha):
        """Configura variables de entorno para fechas específicas"""
        fecha_str = fecha.strftime("%Y-%m-%d %H:%M:%S") + "-0500"
        return {
            'GIT_AUTHOR_DATE': fecha_str,
            'GIT_COMMITTER_DATE': fecha_str
        }

    def crear_y_mergear_pr(self, mes, año, pr_num):
        """Crea y mergea un PR con fecha histórica"""
        dia = self.generar_fecha_aleatoria(mes, año)
        hora = random.randint(9, 18)
        minuto = random.randint(0, 59)
        fecha_commit = datetime(año, mes, dia, hora, minuto)
        
        # Configurar entorno con fechas
        env_commit = os.environ.copy()
        env_commit.update(self.configurar_entorno_fechas(fecha_commit))
        
        branch_name = f"pr/{fecha_commit.strftime('%Y%m%d')}-{pr_num:03d}"
        
        try:
            # Configuración inicial
            self.run_git_command('git checkout main', False)
            self.run_git_command('git pull origin main', False)
            
            # Crear rama y commit
            self.run_git_command(f'git checkout -b {branch_name}', False, env_commit)
            with open('historial.txt', 'a') as f:
                f.write(f"PR {pr_num} - {fecha_commit.isoformat()}\n")
            
            self.run_git_command('git add historial.txt', False, env_commit)
            commit_msg = f"PR {pr_num} - {fecha_commit.strftime('%Y-%m-%d %H:%M')}"
            self.run_git_command(f'git commit -m "{commit_msg}"', False, env_commit)
            
            # Push con fecha histórica
            self.run_git_command(f'git push -u origin {branch_name}', False, env_commit)
            
            # Crear PR
            pr_data = {
                "title": f"PR {pr_num} - {fecha_commit.strftime('%Y-%m')}",
                "head": branch_name,
                "base": os.getenv('BASE_BRANCH'),
                "body": f"PR generado automáticamente\nFecha: {fecha_commit}"
            }
            pr_number = self.crear_pr(pr_data)
            
            if pr_number:
                # Merge con fecha histórica
                merge_env = env_commit.copy()
                
                # Realizar merge local
                self.run_git_command('git checkout main', False, merge_env)
                merge_msg = f"Merge PR #{pr_number} ({fecha_commit.strftime('%Y-%m-%d')})"
                self.run_git_command(
                    f'git merge --no-ff {branch_name} -m "{merge_msg}"',
                    False,
                    merge_env
                )
                
                # Push del merge con fecha correcta
                self.run_git_command('git push origin main', False, merge_env)
        finally:
            # Limpieza de ramas
            self.run_git_command('git checkout main', False)
            self.run_git_command(f'git branch -D {branch_name}', False)
            self.run_git_command(f'git push origin --delete {branch_name}', False)


# Ejecutando la aplicación
if __name__ == "__main__":
    app = GitHubPRCreatorApp()
    app.mainloop()

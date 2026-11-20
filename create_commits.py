import os
import random
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from dotenv import load_dotenv
from datetime import datetime
from typing import Dict, Optional

import theme

LINEA = "═" * 50
EMOJI = {
    "config": "⚙️",
    "commit": "📌",
    "mes": "📅",
    "progreso": "🔄",
    "exito": "✅",
    "error": "❌",
    "usuario": "👤",
    "push": "🚀",
    "advertencia": "⚠️"
}

DIAS_POR_MES = {
    1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30,
    7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31
}

class GitManager:
    def __init__(self, env_vars: Dict[str, str], output_widget: scrolledtext.ScrolledText):
        self.env_vars = env_vars
        self.output = output_widget
        self.env = os.environ.copy()
        self.env.update({
            'GITHUB_TOKEN': env_vars['GITHUB_TOKEN'],
            'GIT_AUTHOR_DATE': '',
            'GIT_COMMITTER_DATE': ''
        })

    def run_command(self, command: str, show_output: bool = True) -> bool:
        try:
            self.output_insert(f"{EMOJI['progreso']} Ejecutando: {command}\n")
            result = subprocess.run(
                command,
                shell=True,
                check=True,
                env=self.env,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            if show_output and result.stdout:
                self.output_insert(f"{result.stdout}\n")
            return True
        except subprocess.CalledProcessError as e:
            self.output_insert(f"{EMOJI['error']} Error en comando: {command}\n")
            self.output_insert(f"{EMOJI['error']} Detalles: {e.stderr.strip()}\n")
            return False
        except Exception as e:
            self.output_insert(f"{EMOJI['error']} Error inesperado: {str(e)}\n")
            return False

    def output_insert(self, text: str):
        theme.log(self.output, text)

    def check_and_commit_changes(self):
        status_result = subprocess.run(
            "git status --porcelain",
            shell=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=self.env
        )

        if status_result.stdout:
            self.output_insert(f"{EMOJI['advertencia']} Hay cambios no confirmados. Confirmándolos...\n")
            self.run_command("git add -A", False)
            commit_message = f"commit automático {random.randint(1000, 9999)}"
            self.run_command(f'git commit -m "{commit_message}"', False)
            self.output_insert(f"{EMOJI['commit']} Cambios confirmados con mensaje: '{commit_message}'\n")


class CommitGeneratorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Generar commits")
        self.geometry("800x800")
        self.minsize(640, 700)
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

        params_frame = ttk.LabelFrame(main_frame, text="Commits a generar", padding=sp["md"])
        params_frame.pack(fill=tk.X, pady=(0, sp["md"]))

        self.entries['MES_INICIO'] = self._create_spinbox(params_frame, "Mes inicio", 1, 12)
        self.entries['MES_FIN'] = self._create_spinbox(params_frame, "Mes fin", 1, 12)
        self.entries['COMMITS_MES'] = self._create_spinbox(params_frame, "Commits por mes", 1, 1000)
        self.entries['ANO'] = self._create_spinbox(params_frame, "Año", 2000, datetime.now().year + 1)

        exec_frame = ttk.Frame(main_frame)
        exec_frame.pack(fill=tk.X, pady=(0, sp["md"]))
        ttk.Button(exec_frame, text="Generar commits", style="Accent.TButton",
                   command=self._execute).pack(side=tk.LEFT, padx=(0, sp["sm"]))
        ttk.Button(exec_frame, text="Limpiar consola", command=self._clear_output).pack(side=tk.LEFT)

        self.output = theme.make_console(
            main_frame, height=15,
            placeholder="Aquí verás cada commit cuando pulses Generar commits.")
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

    def _validate_inputs(self) -> Optional[Dict[str, int]]:
        try:
            data = {
                'mes_inicio': int(self.entries['MES_INICIO'].get()),
                'mes_fin': int(self.entries['MES_FIN'].get()),
                'commits_mes': int(self.entries['COMMITS_MES'].get()),
                'ano': int(self.entries['ANO'].get())
            }
            
            if data['mes_inicio'] > data['mes_fin']:
                messagebox.showerror("Revisa los meses",
                                     "Mes inicio no puede ser mayor que Mes fin. Por ejemplo: de 3 a 6.")
                return None

            current_year = datetime.now().year
            if not (1990 <= data['ano'] <= current_year + 1):
                messagebox.showerror("Revisa el año", f"Año debe estar entre 1990 y {current_year + 1}.")
                return None

            return data

        except ValueError:
            messagebox.showerror("Revisa los parámetros",
                                 "Mes inicio, Mes fin, Commits por mes y Año deben ser números enteros.")
            return None

    def _create_env_file(self):
        try:
            with open('.env', 'w') as f:
                for key in ['GITHUB_TOKEN', 'REPO_OWNER', 'REPO_NAME', 'BASE_BRANCH', 'USER_EMAIL']:
                    f.write(f"{key}={self.entries[key].get()}\n")
            messagebox.showinfo("Datos guardados", "Los datos del repositorio se guardaron en .env.")
            return True
        except Exception as e:
            messagebox.showerror("No se pudo guardar .env",
                                 f"{e}\n\nRevisa que tengas permiso de escritura en la carpeta del proyecto.")
            return False

    def _generate_commit_dates(self, mes: int, año: int, total_commits: int) -> list:
        max_days = DIAS_POR_MES[mes]
        if mes == 2 and (año % 4 == 0 and (año % 100 != 0 or año % 400 == 0)):
            max_days = 29
            
        return sorted(
            [
                datetime(
                    año, 
                    mes, 
                    random.randint(1, max_days),
                    random.randint(0, 23),
                    random.randint(0, 59)
                )
                for _ in range(total_commits)
            ],
            key=lambda x: x.timestamp()
        )

    def _show_section_title(self, text: str):
        theme.log_section(self.output, text)

    def _clear_output(self):
        self.output.delete(1.0, tk.END)

    def output_insert(self, text: str):
        theme.log(self.output, text)

    def _execute(self):
        self._clear_output()
        if not self._create_env_file():
            return
            
        params = self._validate_inputs()
        if not params:
            return
            
        # Lo escrito en el formulario manda. (load_dotenv() no sobrescribe
        # valores ya cargados, así que un token cambiado en el formulario
        # se ignoraba y se seguía usando el anterior.)
        env_vars = {key: self.entries[key].get().strip()
                    for key in ['GITHUB_TOKEN', 'REPO_OWNER', 'REPO_NAME', 'BASE_BRANCH', 'USER_EMAIL']}
        os.environ.update(env_vars)

        if not all(env_vars.values()):
            messagebox.showerror("Faltan datos del repositorio",
                                 "Completa token, dueño, nombre del repo, rama base y email.")
            return

        git = GitManager(env_vars, self.output)

        try:
            self._show_section_title("Preparando git")
            git.run_command('git config --local commit.gpgsign false', False)
            git.run_command('git config pull.rebase false', False)
            git.run_command(f'git config --local user.name "{env_vars["REPO_OWNER"]}"', False)
            git.run_command(f'git config --local user.email "{env_vars["USER_EMAIL"]}"', False)
            
            self._show_section_title("Sincronizando repositorio")
            repo_url = f'https://{env_vars["REPO_OWNER"]}:{env_vars["GITHUB_TOKEN"]}@github.com/{env_vars["REPO_OWNER"]}/{env_vars["REPO_NAME"]}.git'
            git.run_command(f'git pull --allow-unrelated-histories {repo_url} {env_vars["BASE_BRANCH"]}', True)
            
            git.check_and_commit_changes()
            
            total_commits = params['commits_mes'] * (params['mes_fin'] - params['mes_inicio'] + 1)
            self._show_section_title(f"Generando {total_commits} commits")
            
            for mes in range(params['mes_inicio'], params['mes_fin'] + 1):
                commit_dates = self._generate_commit_dates(mes, params['ano'], params['commits_mes'])
                self.output_insert(f"\n{EMOJI['mes']} Procesando mes {mes:02d}/{params['ano']}\n")
                
                for i, date in enumerate(commit_dates, 1):
                    with open('commits.log', 'a') as f:
                        f.write(f"Commit {date.isoformat()}\n")
                        
                    git.env['GIT_AUTHOR_DATE'] = date.isoformat()
                    git.env['GIT_COMMITTER_DATE'] = date.isoformat()
                    
                    git.run_command('git add -f commits.log', False)
                    if git.run_command(f'git commit -m "Commit del {date.strftime("%d/%m/%Y")}"', False):
                        self.output_insert(f"{EMOJI['commit']} Commit {i}/{len(commit_dates)} realizado en {date.strftime('%H:%M:%S %d/%m/%Y')}\n")
            
            # Push final
            self._show_section_title("Enviando al repositorio remoto")
            git.run_command(f'git pull --rebase {repo_url} {env_vars["BASE_BRANCH"]}', True)
            pushed = git.run_command(f'git push {repo_url} {env_vars["BASE_BRANCH"]}', True)

            if pushed:
                self.output_insert(f"\n{EMOJI['exito']} {total_commits} commits generados y enviados a {env_vars['BASE_BRANCH']}.\n")
            else:
                self.output_insert(
                    f"\n{EMOJI['advertencia']} {total_commits} commits creados en local, pero GitHub rechazó el push. "
                    "Revisa el error de arriba; los commits siguen en tu repo local.\n")
            
        except Exception as e:
            self.output_insert(f"{EMOJI['error']} Error general: {str(e)}\n")
            return

if __name__ == "__main__":
    app = CommitGeneratorApp()
    app.mainloop()

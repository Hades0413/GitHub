import os
import random
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from dotenv import load_dotenv
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import theme

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

MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio",
         "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

DIAS_POR_MES = {
    1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30,
    7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31
}

AÑO_MIN = 1990

# Tamaño máximo de cada push. Los envíos de miles de commits de golpe dejaron
# meses sin aparecer en el gráfico de contribuciones de GitHub.
MAX_COMMITS_POR_ENVIO = 1000


def meses_del_rango(mes_ini: int, año_ini: int, mes_fin: int, año_fin: int) -> List[Tuple[int, int]]:
    """Lista de (año, mes) desde el mes inicial hasta el final, ambos incluidos."""
    resultado = []
    año, mes = año_ini, mes_ini
    while (año, mes) <= (año_fin, mes_fin):
        resultado.append((año, mes))
        mes += 1
        if mes > 12:
            año, mes = año + 1, 1
    return resultado


def formato_miles(n: int) -> str:
    return f"{n:,}".replace(",", ".")


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

    def run_command(self, command: str, show_output: bool = True, echo: bool = True) -> bool:
        try:
            if echo:
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

    def head(self) -> str:
        result = subprocess.run("git rev-parse HEAD", shell=True, capture_output=True,
                                text=True, encoding="utf-8", env=self.env)
        return result.stdout.strip()

    def output_insert(self, text: str):
        theme.log(self.output, text)

    def warn_uncommitted_changes(self):
        """Avisa si hay archivos modificados. Ya no los confirma por su cuenta:
        antes se hacía `git add -A` y se subían cambios del proyecto como
        "commit automático" sin que nadie lo decidiera."""
        status = subprocess.run("git status --porcelain", shell=True, capture_output=True,
                                text=True, encoding="utf-8", env=self.env)
        if status.stdout.strip():
            self.output_insert(f"{EMOJI['advertencia']} Hay archivos modificados en la carpeta. "
                               "No se incluirán en los commits generados.\n")


class CommitGeneratorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Generar commits")
        self.geometry("800x820")
        self.minsize(640, 720)
        self.resizable(True, True)
        theme.apply_theme(self)
        self._create_widgets()
        self._load_env_if_exists()
        self._update_summary()

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

        año_pasado = datetime.now().year - 1
        self.mes_desde, self.año_desde = self._create_month_year_row(params_frame, "Desde", 1, año_pasado)
        self.mes_hasta, self.año_hasta = self._create_month_year_row(params_frame, "Hasta", 12, año_pasado)

        # Atajos para no tener que mover los meses uno por uno
        presets = ttk.Frame(params_frame)
        presets.pack(fill=tk.X, pady=(sp["xs"], sp["sm"]))
        ttk.Label(presets, text="", width=theme.SPIN_LABEL_WIDTH).pack(side=tk.LEFT)
        for texto, ini, fin in (("Año completo", 1, 12), ("1.er semestre", 1, 6), ("2.º semestre", 7, 12)):
            ttk.Button(presets, text=texto, style="Chip.TButton",
                       command=lambda i=ini, f=fin: self._apply_preset(i, f)).pack(side=tk.LEFT, padx=(0, sp["xs"]))

        row = ttk.Frame(params_frame)
        row.pack(fill=tk.X, pady=sp["xs"])
        ttk.Label(row, text="Commits por mes", width=theme.SPIN_LABEL_WIDTH).pack(side=tk.LEFT)
        # Sin tope: el máximo de las flechas es solo nominal; se puede escribir cualquier cantidad.
        self.commits_mes = ttk.Spinbox(row, from_=1, to=10**9, increment=10, width=8,
                                       command=self._update_summary)
        self.commits_mes.set(10)
        self.commits_mes.pack(side=tk.LEFT)
        self.commits_mes.bind("<KeyRelease>", lambda e: self._update_summary())

        self.summary = ttk.Label(params_frame, text="", style="Muted.TLabel")
        self.summary.pack(fill=tk.X, pady=(sp["sm"], 0))

        exec_frame = ttk.Frame(main_frame)
        exec_frame.pack(fill=tk.X, pady=(0, sp["md"]))
        ttk.Button(exec_frame, text="Generar commits", style="Accent.TButton",
                   command=self._execute).pack(side=tk.LEFT, padx=(0, sp["sm"]))
        ttk.Button(exec_frame, text="Limpiar consola", command=self._clear_output).pack(side=tk.LEFT)

        self.output = theme.make_console(
            main_frame, height=12,
            placeholder="Aquí verás cada mes y su envío cuando pulses Generar commits.")
        self.output.pack(fill=tk.BOTH, expand=True)

    def _create_month_year_row(self, parent, label_text, mes, año):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=theme.SPACE["xs"])
        ttk.Label(frame, text=label_text, width=theme.SPIN_LABEL_WIDTH).pack(side=tk.LEFT)
        mes_box = ttk.Spinbox(frame, values=MESES, wrap=True, state="readonly", width=12,
                              command=self._update_summary)
        mes_box.set(MESES[mes - 1])
        mes_box.pack(side=tk.LEFT, padx=(0, theme.SPACE["sm"]))
        año_box = ttk.Spinbox(frame, from_=AÑO_MIN, to=datetime.now().year + 1, width=6,
                              command=self._update_summary)
        año_box.set(año)
        año_box.pack(side=tk.LEFT)
        año_box.bind("<KeyRelease>", lambda e: self._update_summary())
        return mes_box, año_box

    def _apply_preset(self, mes_ini: int, mes_fin: int):
        """Aplica el atajo sobre el año de 'Desde'."""
        self.mes_desde.set(MESES[mes_ini - 1])
        self.mes_hasta.set(MESES[mes_fin - 1])
        self.año_hasta.set(self.año_desde.get())
        self._update_summary()

    def _read_range(self) -> Optional[Dict[str, int]]:
        try:
            return {
                'mes_inicio': MESES.index(self.mes_desde.get()) + 1,
                'ano_inicio': int(self.año_desde.get()),
                'mes_fin': MESES.index(self.mes_hasta.get()) + 1,
                'ano_fin': int(self.año_hasta.get()),
                'commits_mes': int(self.commits_mes.get()),
            }
        except ValueError:
            return None

    def _update_summary(self):
        data = self._read_range()
        if not data or data['commits_mes'] < 1:
            self.summary.configure(text="Escribe años y commits por mes como números enteros.")
            return
        meses = meses_del_rango(data['mes_inicio'], data['ano_inicio'], data['mes_fin'], data['ano_fin'])
        if not meses:
            self.summary.configure(text="«Desde» tiene que ser anterior o igual a «Hasta».")
            return
        hoy = datetime.now()
        if (data['ano_fin'], data['mes_fin']) > (hoy.year, hoy.month):
            self.summary.configure(
                text=f"«Hasta» no puede pasar de {MESES[hoy.month - 1].lower()} de {hoy.year}: "
                     "serían commits con fecha futura.")
            return
        total = len(meses) * data['commits_mes']
        por_mes = -(-data['commits_mes'] // MAX_COMMITS_POR_ENVIO)  # división hacia arriba
        n_envios = len(meses) * por_mes
        envios = "1 envío" if n_envios == 1 else f"{formato_miles(n_envios)} envíos de hasta {formato_miles(min(data['commits_mes'], MAX_COMMITS_POR_ENVIO))} commits"
        self.summary.configure(
            text=f"Se crearán {formato_miles(total)} commits entre "
                 f"{MESES[data['mes_inicio'] - 1].lower()} de {data['ano_inicio']} y "
                 f"{MESES[data['mes_fin'] - 1].lower()} de {data['ano_fin']}, en {envios}.")

    def _load_env_if_exists(self):
        if os.path.exists('.env'):
            load_dotenv()
            for key in self.entries:
                if key in os.environ:
                    self.entries[key].insert(0, os.getenv(key))

    def _validate_inputs(self) -> Optional[Dict[str, int]]:
        data = self._read_range()
        if not data:
            messagebox.showerror("Revisa los parámetros",
                                 "Los años y Commits por mes deben ser números enteros.")
            return None

        limite = datetime.now().year + 1
        for año in (data['ano_inicio'], data['ano_fin']):
            if not (AÑO_MIN <= año <= limite):
                messagebox.showerror("Revisa el año", f"El año debe estar entre {AÑO_MIN} y {limite}.")
                return None

        if (data['ano_inicio'], data['mes_inicio']) > (data['ano_fin'], data['mes_fin']):
            messagebox.showerror("Revisa el rango",
                                 "«Desde» tiene que ser anterior o igual a «Hasta». "
                                 "Por ejemplo: desde enero de 2023 hasta diciembre de 2024.")
            return None

        hoy = datetime.now()
        if (data['ano_fin'], data['mes_fin']) > (hoy.year, hoy.month):
            messagebox.showerror("Revisa «Hasta»",
                                 f"«Hasta» no puede pasar de {MESES[hoy.month - 1].lower()} de {hoy.year}; "
                                 "se crearían commits con fecha futura.")
            return None

        if data['commits_mes'] < 1:
            messagebox.showerror("Revisa Commits por mes", "Commits por mes debe ser 1 o más.")
            return None

        return data

    def _create_env_file(self):
        try:
            with open('.env', 'w') as f:
                for key in ['GITHUB_TOKEN', 'REPO_OWNER', 'REPO_NAME', 'BASE_BRANCH', 'USER_EMAIL']:
                    f.write(f"{key}={self.entries[key].get()}\n")
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
            datetime(año, mes, random.randint(1, max_days), random.randint(0, 23), random.randint(0, 59))
            for _ in range(total_commits)
        )

    def _show_section_title(self, text: str):
        theme.log_section(self.output, text)

    def _clear_output(self):
        self.output.delete(1.0, tk.END)

    def output_insert(self, text: str):
        theme.log(self.output, text)

    def _execute(self):
        self._clear_output()
        params = self._validate_inputs()
        if not params:
            return

        # Lo escrito en el formulario manda. (load_dotenv() no sobrescribe
        # valores ya cargados, así que un token cambiado en el formulario
        # se ignoraba y se seguía usando el anterior.)
        env_vars = {key: self.entries[key].get().strip()
                    for key in ['GITHUB_TOKEN', 'REPO_OWNER', 'REPO_NAME', 'BASE_BRANCH', 'USER_EMAIL']}
        if not all(env_vars.values()):
            messagebox.showerror("Faltan datos del repositorio",
                                 "Completa token, dueño, nombre del repo, rama base y email.")
            return
        os.environ.update(env_vars)
        if not self._create_env_file():
            return

        git = GitManager(env_vars, self.output)
        branch = env_vars["BASE_BRANCH"]
        meses = meses_del_rango(params['mes_inicio'], params['ano_inicio'], params['mes_fin'], params['ano_fin'])
        total_commits = len(meses) * params['commits_mes']

        try:
            self._show_section_title("Preparando git")
            git.run_command('git config --local commit.gpgsign false', False)
            git.run_command('git config pull.rebase false', False)
            git.run_command(f'git config --local user.name "{env_vars["REPO_OWNER"]}"', False)
            git.run_command(f'git config --local user.email "{env_vars["USER_EMAIL"]}"', False)

            self._show_section_title("Sincronizando repositorio")
            repo_url = f'https://{env_vars["REPO_OWNER"]}:{env_vars["GITHUB_TOKEN"]}@github.com/{env_vars["REPO_OWNER"]}/{env_vars["REPO_NAME"]}.git'
            if not git.run_command(f'git pull --allow-unrelated-histories {repo_url} {branch}', True):
                self.output_insert(f"{EMOJI['advertencia']} No se pudo sincronizar con GitHub. "
                                   "Revisa el error de arriba antes de generar commits.\n")
                return
            git.warn_uncommitted_changes()

            self._show_section_title(f"Generando {formato_miles(total_commits)} commits")
            cortes = []  # (etiqueta, commit en el que termina ese envío)
            for año, mes in meses:
                creados = 0
                etiqueta = f"{MESES[mes - 1].lower()} {año}"
                for date in self._generate_commit_dates(mes, año, params['commits_mes']):
                    git.env['GIT_AUTHOR_DATE'] = date.isoformat()
                    git.env['GIT_COMMITTER_DATE'] = date.isoformat()
                    # Commit vacío: no hace falta tocar ningún archivo
                    # (antes se añadía una línea a commits.log en cada commit).
                    if git.run_command(f'git commit --allow-empty -q -m "Commit del {date.strftime("%d/%m/%Y")}"',
                                       False, echo=False):
                        creados += 1
                        if creados % MAX_COMMITS_POR_ENVIO == 0:
                            cortes.append((f"{etiqueta} (hasta {formato_miles(creados)})", git.head()))
                    self.update_idletasks()
                self.output_insert(f"{EMOJI['commit']} {etiqueta.capitalize()}: {formato_miles(creados)} commits\n")
                if creados % MAX_COMMITS_POR_ENVIO:
                    cortes.append((etiqueta, git.head()))

            # Un push por mes: los envíos gigantes (miles de commits de golpe)
            # dejaron meses sin aparecer en el gráfico de contribuciones.
            self._show_section_title(f"Enviando a GitHub en {len(cortes)} partes")
            for n, (etiqueta, sha) in enumerate(cortes, 1):
                ok = git.run_command(f'git push -q {repo_url} {sha}:refs/heads/{branch}', True, echo=False)
                if not ok:
                    self.output_insert(
                        f"\n{EMOJI['advertencia']} Se enviaron {n - 1} de {len(cortes)} meses. "
                        f"Falló {etiqueta}; los commits restantes siguen en tu repo local.\n")
                    return
                self.output_insert(f"{EMOJI['push']} Enviado {etiqueta} ({n}/{len(cortes)})\n")
            git.run_command(f'git fetch -q {repo_url} {branch}:refs/remotes/origin/{branch}', False, echo=False)

            self.output_insert(f"\n{EMOJI['exito']} {formato_miles(total_commits)} commits generados y enviados a {branch}.\n")

        except Exception as e:
            self.output_insert(f"{EMOJI['error']} Error general: {str(e)}\n")
            return


if __name__ == "__main__":
    app = CommitGeneratorApp()
    app.mainloop()

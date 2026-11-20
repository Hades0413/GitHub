import requests
import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from dotenv import load_dotenv
from datetime import datetime

import theme

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

GITHUB_API_URL = 'https://api.github.com'

class GitHubIssueCreatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Crear issues")
        self.geometry("800x620")
        self.minsize(640, 540)
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
            ("Nombre del repo", 'REPO_NAME')
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

        params_frame = ttk.LabelFrame(main_frame, text="Issues a crear", padding=sp["md"])
        params_frame.pack(fill=tk.X, pady=(0, sp["md"]))

        self.entries['TOTAL_ISSUES'] = self._create_spinbox(params_frame, "Total de issues", 1, 100)

        exec_frame = ttk.Frame(main_frame)
        exec_frame.pack(fill=tk.X, pady=(0, sp["sm"]))
        ttk.Button(exec_frame, text="Crear issues", style="Accent.TButton",
                   command=self._execute).pack(side=tk.LEFT)

        # Botones para limpiar la consola y los campos
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, sp["md"]))
        ttk.Button(control_frame, text="Limpiar consola", command=self.clear_console).pack(side=tk.LEFT, padx=(0, sp["sm"]))
        ttk.Button(control_frame, text="Limpiar campos", command=self.clear_fields).pack(side=tk.LEFT)

        self.output = theme.make_console(
            main_frame, height=15,
            placeholder="Aquí verás cada issue y su enlace cuando pulses Crear issues.")
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
                'total_issues': int(self.entries['TOTAL_ISSUES'].get())
            }

            if data['total_issues'] < 1:
                messagebox.showerror("Revisa el total", "Total de issues debe ser 1 o más.")
                return None

            return data

        except ValueError:
            messagebox.showerror("Revisa el total", "Total de issues debe ser un número entero, por ejemplo 5.")
            return None

    def _create_issue(self, title, body, issue_num, total):
        try:
            url = f"{GITHUB_API_URL}/repos/{self.entries['REPO_OWNER'].get()}/{self.entries['REPO_NAME'].get()}/issues"
            headers = {
                'Authorization': f'token {self.entries["GITHUB_TOKEN"].get()}',
                'Accept': 'application/vnd.github.v3+json'
            }
            data = {
                'title': title,
                'body': body
            }

            progress = f"[{issue_num}/{total}]"
            self.output_insert(f"{EMOJI['progress']} {progress} Creando issue: {title[:30]}...\n")

            start_time = datetime.now()
            response = requests.post(url, headers=headers, json=data)
            elapsed = (datetime.now() - start_time).total_seconds()

            if response.status_code == 201:
                issue = response.json()
                self.output_insert(f"{EMOJI['success']} {progress} Issue creado en {elapsed:.2f}s\n")
                self.output_insert(f"{issue['html_url']}\n")
                return True
            else:
                self.output_insert(f"{EMOJI['error']} {progress} Error {response.status_code}\n")
                self.output_insert(f"Respuesta: {response.text[:200]}...\n")
                return False

        except Exception as e:
            self.output_insert(f"{EMOJI['error']} Error crítico: {str(e)}")
            return False

    def output_insert(self, text: str):
        theme.log(self.output, text)

    def clear_console(self):
        """Limpiar la consola de salida."""
        self.output.delete(1.0, tk.END)

    def clear_fields(self):
        """Limpiar los campos de entrada."""
        for key, entry in self.entries.items():
            entry.delete(0, tk.END)

    def _execute(self):
        self.output.delete(1.0, tk.END)

        params = self._validate_inputs()
        if not params:
            return

        # Lo escrito en el formulario manda; .env solo rellena lo que esté vacío.
        load_dotenv(override=False)
        for key in ('GITHUB_TOKEN', 'REPO_OWNER', 'REPO_NAME'):
            value = self.entries[key].get().strip()
            if value:
                os.environ[key] = value
        github_token = os.getenv('GITHUB_TOKEN')
        repo_owner = os.getenv('REPO_OWNER')
        repo_name = os.getenv('REPO_NAME')

        if not github_token or not repo_owner or not repo_name:
            messagebox.showerror("Faltan datos del repositorio",
                                 "Completa token, dueño y nombre del repo en el formulario (o en .env).")
            return

        total_issues = params['total_issues']
        success_count = 0
        failed_count = 0

        theme.log_section(self.output, f"Creando {total_issues} issues")

        for i in range(1, total_issues + 1):
            title = f'Issue {i} - {datetime.now().strftime("%Y-%m-%d")}'
            body = f"""## Descripción del issue {i}

Este es un issue generado automáticamente el {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

**Detalles:**
- Prioridad: Alta
- Tipo: Mejora
- Asignado: Equipo de desarrollo"""

            if self._create_issue(title, body, i, total_issues):
                success_count += 1
            else:
                failed_count += 1

        theme.log_section(self.output, "Resumen")
        self.output_insert(f"{EMOJI['success']} Creados: {success_count}\n")
        if failed_count:
            self.output_insert(f"{EMOJI['error']} Fallidos: {failed_count}\n")
            self.output_insert(f"{EMOJI['warning']} Revisa los errores de arriba: suele ser el token "
                               "sin permiso de issues o un repo mal escrito.\n")

if __name__ == "__main__":
    app = GitHubIssueCreatorApp()
    app.mainloop()

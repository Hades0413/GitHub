import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
from PIL import Image, ImageTk
import webbrowser
import os

import theme

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("RepoSetupToolDesktop 1.0")
        self.geometry("820x520")
        self.minsize(800, 500)
        theme.apply_theme(self)

        self.load_resources()
        self.setup_ui()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.setup_bindings()

    def load_resources(self):
        try:
            self.logo_image = ImageTk.PhotoImage(Image.open('logo.ico').resize((220, 80)))
            self.github_icon = ImageTk.PhotoImage(Image.open('hades.jpeg').resize((30, 30)))
        except FileNotFoundError:
            messagebox.showwarning("Recursos faltantes", 
                                   "Algunos archivos de imagen no se encontraron. Se usarán placeholders.")
            # Generar placeholders
            self.logo_image = ImageTk.PhotoImage(Image.new('RGB', (220, 80), '#16213e'))
            self.github_icon = ImageTk.PhotoImage(Image.new('RGB', (30, 30), '#e94560'))

    def setup_ui(self):
        # Header Section
        c = theme.COLORS
        header_frame = ttk.Frame(self, style='TFrame')
        header_frame.pack(fill='x', padx=20, pady=20)

        # Logo con marco de 1 px para que su fondo claro no choque con el tema
        logo_label = tk.Label(header_frame, image=self.logo_image, bd=0,
                              bg=c["bg"], highlightthickness=1,
                              highlightbackground=c["border"])
        logo_label.pack(side='left', padx=15)

        title_frame = ttk.Frame(header_frame, style='TFrame')
        title_frame.pack(side='left', padx=20)

        ttk.Label(title_frame, text="RepoSetupToolDesktop", style='Title.TLabel').pack(anchor='w')
        ttk.Label(title_frame, text="Commits, issues y PRs con las fechas que elijas",
                  style='Muted.TLabel').pack(anchor='w', pady=(theme.SPACE["xs"], 0))

        # Main Content
        main_frame = ttk.Frame(self, style='TFrame')
        main_frame.pack(expand=True, fill='both', padx=40, pady=20)

        # Acciones: mismo estilo para las tres, cada una dice qué hace
        actions = [
            ('Generar commits', 'Commits fechados por mes y año', self.open_commit_generator),
            ('Generar issues', 'Varios issues de una sola vez', self.open_issue_generator),
            ('Generar PRs', 'Rama, PR y merge por cada mes', self.open_pr_generator)
        ]

        for idx, (text, hint, command) in enumerate(actions):
            card = ttk.Frame(main_frame, style='TFrame')
            card.grid(row=0, column=idx, padx=15, pady=10, sticky='nsew')

            btn = ttk.Button(card, text=text, style='Action.TButton', command=command)
            btn.pack(expand=True, fill='both')

            ttk.Label(card, text=hint, style='Muted.TLabel').pack(pady=theme.SPACE["sm"])

        main_frame.columnconfigure([0,1,2], weight=1, uniform="acciones")

        # Status Bar
        self.status_bar = ttk.Frame(self, style='TFrame')
        self.status_bar.pack(fill='x', side='bottom', pady=10)

        self.status_label = ttk.Label(self.status_bar,
                                    text="Estado: Listo",
                                    style='Muted.TLabel')
        self.status_label.pack(side='left', padx=20)

        ttk.Button(self.status_bar,
                 image=self.github_icon,
                 command=self.open_docs,
                 style='Icon.TButton').pack(side='right', padx=10)

        # Setup Menu
        self.setup_menu()

    def setup_menu(self):
        menu_bar = tk.Menu(self)
        
        # Archivo Menu
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Nuevo Proyecto")
        file_menu.add_command(label="Abrir")
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.on_close)
        
        # Ayuda Menu
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="Documentación", command=self.open_docs)
        help_menu.add_command(label="Actualizaciones")
        help_menu.add_command(label="Acerca de", command=self.show_about)
        
        menu_bar.add_cascade(label="Archivo", menu=file_menu)
        menu_bar.add_cascade(label="Ayuda", menu=help_menu)
        
        self.config(menu=menu_bar)

    def setup_bindings(self):
        self.bind_all("<Control-q>", lambda e: self.on_close())
        self.bind_all("<F1>", lambda e: self.open_docs())

    def run_script(self, script_name):
        try:
            script_path = os.path.abspath(script_name)  # Get absolute path of the script
            process = subprocess.Popen([sys.executable, script_path],
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                self.update_status(f"{script_name} cerrado sin errores")
            else:
                raise subprocess.CalledProcessError(process.returncode, script_name, stderr)

        except subprocess.CalledProcessError as e:
            detalle = (e.stderr or b"").decode(errors="replace").strip().splitlines()
            ultima = detalle[-1] if detalle else f"código de salida {e.returncode}"
            messagebox.showerror(f"{script_name} terminó con un error",
                                 f"{ultima}\n\nRevisa la consola de esa ventana o ejecútalo con "
                                 f"python {script_name} para ver el detalle.")
            self.update_status(f"Error en {script_name}")
        except Exception as e:
            messagebox.showerror(f"No se pudo abrir {script_name}",
                                 f"{e}\n\nComprueba que el archivo está en la carpeta del proyecto.")
            self.update_status(f"Error en {script_name}")

    def update_status(self, message):
        self.status_label.config(text=f"Estado: {message}")
        self.after(3000, lambda: self.status_label.config(text="Estado: Listo"))

    def show_about(self):
        about_content = """
        RepoSetupToolDesktop 1.0
        
        Versión: 1.0.0
        Desarrollado por: Hades0413
        Licencia: MIT
        
        Características principales:
        - Generación automatizada de commits
        - Gestión de issues integrada
        - Sistema de PRs inteligente
        - Interfaz moderna y responsive
        """
        messagebox.showinfo("Acerca de", about_content)

    # Funciones para manejar los botones
    def open_commit_generator(self):
        self.run_script("create_commits.py")

    def open_issue_generator(self):
        self.run_script("create_issues.py")

    def open_pr_generator(self):
        self.run_script("create_pr.py")
    
    def open_docs(self):
        webbrowser.open("https://github.com/Hades0413/RepoSetupToolDesktop0413.git")

    def on_close(self):
        self.quit()

if __name__ == "__main__":
    app = App()
    app.mainloop()

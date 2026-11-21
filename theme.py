"""Tema visual compartido de RepoSetupToolDesktop.

Un solo lugar para colores, tipografía y espaciado. Las cuatro ventanas
llaman a apply_theme() y crean su consola con make_console(), así todas
se ven igual.

Principios:
1. Un solo color de acción (ámbar). Si es ámbar, se puede pulsar.
2. Los colores de diff (verde, rojo, azul) solo viven en la consola.
3. Textos en español, con mayúscula solo al inicio.
"""
import re
import tkinter as tk
from tkinter import ttk, font as tkfont, scrolledtext

# --- Tokens de color -------------------------------------------------------
COLORS = {
    "bg": "#22252A",          # Grafito: fondo de todas las ventanas
    "surface": "#2B2F36",     # Inputs, spinboxes y consola
    "surface_hover": "#353A42",
    "border": "#3D434C",      # Bordes de 1 px
    "border_strong": "#565E6A",  # Borde de los botones grandes de inicio
    "text": "#E6E8EB",
    "muted": "#9AA3AD",       # Ayudas y etiquetas secundarias (AA sobre bg)
    "accent": "#E3B341",      # Ámbar: acción principal y foco de teclado
    "accent_hover": "#EDC462",
    "accent_pressed": "#C99A2E",
    "ok": "#7EC699",          # Diff: añadido / éxito (solo consola)
    "err": "#F2777A",         # Diff: eliminado / error (solo consola)
    "info": "#79B8D6",        # Diff: cabecera / info (solo consola)
}

# --- Tokens de espaciado ---------------------------------------------------
SPACE = {"xs": 4, "sm": 8, "md": 12, "lg": 20, "xl": 32}

# Ancho (en caracteres) de las columnas de etiquetas, para que todo alinee.
LABEL_WIDTH = 17
SPIN_LABEL_WIDTH = 15

_UI_CANDIDATES = ("Ubuntu Sans", "Ubuntu", "Noto Sans", "DejaVu Sans")
_MONO_CANDIDATES = ("Ubuntu Sans Mono", "Ubuntu Mono", "DejaVu Sans Mono")


def _pick_family(root, candidates):
    available = set(tkfont.families(root))
    for family in candidates:
        if family in available:
            return family
    return "TkDefaultFont"


def fonts(root):
    """Escala tipográfica: 20 título / 13 interfaz / 11 ayudas y consola."""
    ui = _pick_family(root, _UI_CANDIDATES)
    mono = _pick_family(root, _MONO_CANDIDATES)
    return {
        "title": (ui, 20, "bold"),
        "ui": (ui, 11),
        "ui_bold": (ui, 11, "bold"),
        "action": (ui, 13, "bold"),
        "small": (ui, 10),
        "mono": (mono, 10),
        "mono_bold": (mono, 10, "bold"),
    }


def apply_theme(root):
    """Aplica el tema a una ventana raíz de Tk y devuelve las fuentes."""
    c = COLORS
    f = fonts(root)
    root.configure(bg=c["bg"])

    # Menús y diálogos nativos de Tk
    root.option_add("*Menu.background", c["surface"])
    root.option_add("*Menu.foreground", c["text"])
    root.option_add("*Menu.activeBackground", c["border"])
    root.option_add("*Menu.activeForeground", c["text"])
    root.option_add("*Menu.relief", "flat")
    root.option_add("*Menu.font", f["ui"])
    root.option_add("*Dialog.msg.font", f["ui"])

    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure(
        ".",
        background=c["bg"], foreground=c["text"], font=f["ui"],
        bordercolor=c["border"], lightcolor=c["bg"], darkcolor=c["bg"],
        troughcolor=c["bg"], focuscolor=c["accent"],
        selectbackground=c["accent"], selectforeground=c["bg"],
        insertcolor=c["text"],
    )

    style.configure("TFrame", background=c["bg"])
    style.configure("TLabel", background=c["bg"], foreground=c["text"])
    style.configure("Muted.TLabel", foreground=c["muted"], font=f["small"])
    style.configure("Title.TLabel", font=f["title"])

    # Secciones: borde de 1 px, sin sombra
    style.configure(
        "TLabelframe", background=c["bg"], bordercolor=c["border"],
        lightcolor=c["border"], darkcolor=c["border"],
        relief="solid", borderwidth=1,
    )
    style.configure(
        "TLabelframe.Label", background=c["bg"], foreground=c["muted"],
        font=f["ui_bold"],
    )

    # Campos de texto y spinboxes
    field = dict(
        fieldbackground=c["surface"], background=c["surface"],
        foreground=c["text"], insertcolor=c["text"],
        bordercolor=c["border"], lightcolor=c["surface"],
        darkcolor=c["surface"], padding=(8, 5),
    )
    focus_map = dict(
        bordercolor=[("focus", c["accent"])],
        lightcolor=[("focus", c["accent"])],
        darkcolor=[("focus", c["accent"])],
    )
    style.configure("TEntry", **field)
    style.map("TEntry", **focus_map)
    style.configure("TSpinbox", arrowcolor=c["muted"], arrowsize=12, **field)
    style.map(
        "TSpinbox", arrowcolor=[("active", c["accent"])],
        fieldbackground=[("readonly", c["surface"])],
        foreground=[("readonly", c["text"])],
        selectbackground=[("readonly", c["surface"])],
        selectforeground=[("readonly", c["text"])],
        **focus_map,
    )

    # Botón secundario (neutro)
    style.configure(
        "TButton", background=c["surface"], foreground=c["text"],
        bordercolor=c["border"], lightcolor=c["surface"],
        darkcolor=c["surface"], padding=(14, 7), relief="flat",
        font=f["ui"], focusthickness=0,
    )
    style.map(
        "TButton",
        background=[("pressed", c["border"]), ("active", c["surface_hover"])],
        lightcolor=[("pressed", c["border"]), ("active", c["surface_hover"])],
        darkcolor=[("pressed", c["border"]), ("active", c["surface_hover"])],
        bordercolor=[("focus", c["accent"])],
    )

    # Botón principal (ámbar): la única acción destacada de cada formulario
    style.configure(
        "Accent.TButton", background=c["accent"], foreground=c["bg"],
        bordercolor=c["accent"], lightcolor=c["accent"],
        darkcolor=c["accent"], font=f["ui_bold"],
    )
    style.map(
        "Accent.TButton",
        background=[("pressed", c["accent_pressed"]), ("active", c["accent_hover"])],
        lightcolor=[("pressed", c["accent_pressed"]), ("active", c["accent_hover"])],
        darkcolor=[("pressed", c["accent_pressed"]), ("active", c["accent_hover"])],
        bordercolor=[("focus", c["text"])],
    )

    # Botones grandes de la ventana principal: neutros, borde ámbar al pasar
    style.configure(
        "Action.TButton", font=f["action"], padding=(16, 14),
        background=c["surface"], bordercolor=c["border_strong"],
        relief="solid", borderwidth=1,
    )
    style.map(
        "Action.TButton",
        background=[("pressed", c["border"]), ("active", c["surface_hover"])],
        lightcolor=[("pressed", c["border"]), ("active", c["surface_hover"])],
        darkcolor=[("pressed", c["border"]), ("active", c["surface_hover"])],
        bordercolor=[("focus", c["accent"]), ("active", c["accent"])],
    )

    # Atajos pequeños (p. ej. "Año completo"): texto suave, borde fino
    style.configure(
        "Chip.TButton", font=f["small"], padding=(10, 3),
        foreground=c["muted"], background=c["bg"], bordercolor=c["border"],
        lightcolor=c["bg"], darkcolor=c["bg"], relief="solid", borderwidth=1,
    )
    style.map(
        "Chip.TButton",
        foreground=[("active", c["text"])],
        background=[("pressed", c["border"]), ("active", c["surface"])],
        lightcolor=[("active", c["surface"])], darkcolor=[("active", c["surface"])],
        bordercolor=[("focus", c["accent"]), ("active", c["border_strong"])],
    )

    # Barra de scroll
    style.configure(
        "Vertical.TScrollbar", background=c["surface"], troughcolor=c["bg"],
        bordercolor=c["bg"], lightcolor=c["surface"], darkcolor=c["surface"],
        arrowcolor=c["muted"], arrowsize=12, gripcount=0,
    )
    style.map(
        "Vertical.TScrollbar",
        background=[("active", c["border"])],
        arrowcolor=[("active", c["accent"])],
    )

    # Botón de icono sin marco
    style.configure(
        "Icon.TButton", background=c["bg"], bordercolor=c["bg"],
        lightcolor=c["bg"], darkcolor=c["bg"], padding=4,
    )
    style.map(
        "Icon.TButton",
        background=[("active", c["surface"])],
        bordercolor=[("focus", c["accent"]), ("active", c["border"])],
    )

    return f


# --- Consola tipo "git log" (elemento memorable) ---------------------------

_KINDS = {
    "✅": "ok", "🚀": "ok",
    "❌": "err",
    "⚠": "warn",
    "🔄": "info", "📌": "info", "📅": "info", "⚙": "info",
    "👤": "info", "🔗": "info", "🏁": "info",
}
_CMD_PREFIX = "Ejecutando: "
_EMOJI_RE = re.compile(r"^\s*(" + "|".join(map(re.escape, _KINDS)) + r")️?\s*")


_URL_CREDENTIALS_RE = re.compile(r"(https?://[^:/\s@]+:)[^@\s]+@")
_GH_TOKEN_RE = re.compile(r"\b(gh[pousr]_|github_pat_)[A-Za-z0-9_]{10,}")


def redact(text):
    """Oculta tokens y credenciales antes de mostrarlos en pantalla."""
    text = _URL_CREDENTIALS_RE.sub(r"\1***@", text)
    return _GH_TOKEN_RE.sub(r"\1***", text)


def make_console(parent, height=15, placeholder=None):
    """Crea la consola de salida con estilo de terminal y etiquetas de diff.

    placeholder: texto que se ve mientras la consola está vacía; se borra
    con la primera línea que se escriba.
    """
    c = COLORS
    f = fonts(parent)
    console = scrolledtext.ScrolledText(
        parent, wrap=tk.WORD, height=height,
        bg=c["surface"], fg=c["text"], insertbackground=c["text"],
        selectbackground=c["border"], selectforeground=c["text"],
        font=f["mono"], relief="flat", borderwidth=0,
        highlightthickness=1, highlightbackground=c["border"],
        highlightcolor=c["accent"], padx=SPACE["md"], pady=SPACE["sm"],
        spacing1=2, spacing3=2,
    )
    # Cambia la barra de scroll de Tk (gris claro) por una ttk con el tema
    # (ScrolledText redirige pack() a su marco, por eso se usa Tcl directo
    # para reordenar: la barra se empaqueta antes y no se recorta al encoger.)
    console.vbar.destroy()
    console.tk.call("pack", "forget", console._w)
    console.vbar = ttk.Scrollbar(console.frame, orient=tk.VERTICAL, command=console.yview)
    console.vbar.pack(side=tk.RIGHT, fill=tk.Y)
    console.tk.call("pack", console._w, "-side", "left", "-fill", "both", "-expand", "1")
    console.configure(yscrollcommand=console.vbar.set)
    for kind in ("ok", "err", "info"):
        console.tag_configure(f"dot_{kind}", foreground=c[kind])
    console.tag_configure("dot_warn", foreground=c["accent"])
    console.tag_configure("err_text", foreground=c["err"])
    console.tag_configure("muted", foreground=c["muted"])
    console.tag_configure(
        "section", foreground=c["text"], font=f["mono_bold"],
        spacing1=SPACE["md"], spacing3=SPACE["xs"],
    )
    console.tag_configure("placeholder", foreground=c["muted"], font=f["small"])
    if placeholder:
        console.insert("1.0", placeholder, "placeholder")
    return console


def _clear_placeholder(console):
    if console.tag_ranges("placeholder"):
        console.delete("1.0", tk.END)


def log(console, text):
    """Escribe en la consola como un git log: un punto de color por resultado.

    Los emojis que usan los scripts se traducen a un ● del color de su
    resultado; los comandos se muestran como "$ comando" en gris, y el resto
    (salida de git, respuestas de la API) va sangrado en gris.
    """
    _clear_placeholder(console)
    text = redact(text)
    for line in text.split("\n"):
        if not line.strip():
            continue  # el espaciado lo dan las cabeceras de sección
        if set(line.strip()) == {"═"}:
            continue  # separadores decorativos antiguos
        match = _EMOJI_RE.match(line)
        if match:
            kind = _KINDS[match.group(1)]
            body = line[match.end():]
            if body.startswith(_CMD_PREFIX):
                console.insert(tk.END, "  $ " + body[len(_CMD_PREFIX):] + "\n", "muted")
                continue
            console.insert(tk.END, "● ", f"dot_{kind}")
            console.insert(tk.END, body + "\n", "err_text" if kind == "err" else ())
        elif line.startswith(_CMD_PREFIX):
            console.insert(tk.END, "  $ " + line[len(_CMD_PREFIX):] + "\n", "muted")
        else:
            console.insert(tk.END, "  " + line.strip() + "\n", "muted")
    console.see(tk.END)
    console.update_idletasks()


def log_section(console, title):
    """Cabecera de etapa dentro de la consola."""
    _clear_placeholder(console)
    console.insert(tk.END, f"── {title}\n", "section")
    console.see(tk.END)


def mask_token(entry):
    """Oculta el token de GitHub sin mover el campo."""
    entry.configure(show="•")

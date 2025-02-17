# Configuración del Proyecto

Este proyecto está diseñado para interactuar con la API de GitHub y realizar diversas tareas automatizadas, como la creación y eliminación de issues, generación de PRs históricos y operaciones con Git.

## Resumen de los cambios

1. **Entorno Virtual**: Se detallan los pasos para crear y activar un entorno virtual de Python (`python3-venv`).
2. **Dependencias**: Se explica cómo crear e instalar las dependencias con `requirements.txt`.
3. **Archivo `.env`**: Se incluyen instrucciones para configurar las variables de entorno necesarias.
4. **Ejecución de Scripts**: Se proporcionan ejemplos para ejecutar cada script.
5. **Solución de Problemas**: Se agregan soluciones a problemas comunes.

Este README te guiará en la configuración y ejecución del proyecto sin inconvenientes.

---

## Requisitos Previos

Asegúrate de tener los siguientes programas instalados en tu sistema:

- **Python 3**: Para verificar la instalación, ejecuta:
  ```bash
  python3 --version
  ```
- **Git**: Para verificar la instalación de Git:
  ```bash
  git --version
  ```

## Instalación y Configuración

### 1. Clonar el Repositorio
Clona este repositorio en tu máquina local:
```bash
git clone https://github.com/tu_usuario/tu_repositorio.git
cd tu_repositorio
```

### 2. Crear un Entorno Virtual
Es recomendable usar un entorno virtual para gestionar las dependencias:
```bash
sudo apt update
sudo apt install python3-venv
python3 -m venv env
source env/bin/activate
```

### 3. Instalar Dependencias
Instala las dependencias necesarias:
```bash
pip install -r requirements.txt
```
Si `requirements.txt` no existe, crea uno con las dependencias necesarias.

### 4. Configuración del Proyecto

Crea un archivo `.env` en el directorio raíz y agrega las siguientes variables:
```ini
GITHUB_TOKEN=Tu_Token_Github
REPO_OWNER=Tu_Usuario_Github
REPO_NAME=Nombre_del_Repositorio
BASE_BRANCH=main
USER_EMAIL=Tu_Email
```
> **Nota:** Genera un token de GitHub con los permisos adecuados en [GitHub Tokens](https://github.com/settings/tokens).

### 5. Ejecutar los Scripts
Asegúrate de que el entorno virtual esté activo antes de ejecutar los scripts.

Ejemplo:
```bash
python commits.py  # Crear commits
python create_issues.py  # Crear issues
python pr.py             # Manejar PRs históricos
python delete_txt.py     # Eliminar archivos .txt
```

### 6. Desactivar el Entorno Virtual
Cuando termines de trabajar, puedes desactivar el entorno virtual:
```bash
deactivate
```

---

## Solución de Problemas (Troubleshooting)

### 1. Error con el token de GitHub
Si recibes un error de autenticación, revisa que el token sea válido y tenga los permisos correctos. Más detalles en [GitHub Token Permissions](https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token).

### 2. Problemas con dependencias
Si hay errores al instalar dependencias, asegúrate de que el entorno virtual esté activado y `requirements.txt` tenga las dependencias correctas.

### 3. Problemas con Git
Si Git no está configurado correctamente, ajústalo con los siguientes comandos:
```bash
git config --global user.name "Tu Nombre"
git config --global user.email "tu_email@dominio.com"
```

---

## Contribución

Si deseas contribuir a este proyecto, sigue estos pasos:
1. Realiza un fork del repositorio.
2. Crea una nueva rama: `git checkout -b feature/nueva-caracteristica`.
3. Realiza cambios y haz commit: `git commit -am 'Agrega nueva característica'`.
4. Sube tu rama: `git push origin feature/nueva-caracteristica`.
5. Crea un pull request para su revisión.

---

👍 **¡Gracias por contribuir!**


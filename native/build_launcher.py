"""Construye un lanzador nativo que ejecuta Python en el proceso de la app."""
from pathlib import Path
import shlex
import subprocess
root = Path(__file__).resolve().parents[1]
flags = subprocess.check_output(['python3.13-config', '--embed', '--cflags', '--ldflags'],text=True)
subprocess.run(['/usr/bin/clang', str(root/'native/launcher.c'), *[flag for flag in shlex.split(flags) if flag != '-g'], '-o', str(root/'OCI SSH Manager.app/Contents/MacOS/launch')], check=True)

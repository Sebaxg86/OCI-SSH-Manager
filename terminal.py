"""Abre sesiones independientes en pestañas de Terminal."""
import shlex
import subprocess
from pathlib import Path
from connection import prepare_key, ssh_command

SCRIPT = Path(__file__).with_name('terminal_tab.applescript')

def open_tab(command, profile='Pro'):
    result = subprocess.run(['/usr/bin/osascript', str(SCRIPT), command, profile],
                            capture_output=True, text=True, timeout=20)
    if result.returncode:
        detail = result.stderr.strip()
        if any(code in detail for code in ('-1743', '-25211', '1002')):
            detail += '\nRevisa Automatización y Accesibilidad en Ajustes del Sistema > Privacidad y seguridad.'
        raise RuntimeError(detail)

def connect_tab(machine, profile='Pro'):
    machine = dict(machine)
    machine['key'] = prepare_key(machine['key'])
    message = 'Verifica la huella SHA256 por un canal confiable antes de escribir yes.'
    command = 'printf "%s\\n" ' + shlex.quote(message) + '; ' + shlex.join(ssh_command(machine))
    open_tab(command, profile)

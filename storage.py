"""Registro local; nunca almacena el contenido de las llaves."""
import json
import os
import tempfile
from pathlib import Path

DATA_DIR = Path.home() / '.config' / 'oracle-ssh-cli'
REGISTRY = DATA_DIR / 'machines.json'

def validate(machine):
    import ipaddress
    import re
    if not isinstance(machine, dict):
        raise ValueError('Registro de máquina inválido.')
    for field in ('name', 'ip', 'os', 'user', 'key'):
        if not isinstance(machine.get(field), str) or not machine[field].strip():
            raise ValueError(f'Campo inválido: {field}')
    description = machine.get('description', '')
    if not isinstance(description, str) or any(ord(c) < 32 for c in description):
        raise ValueError('La descripción debe ser texto en una sola línea.')
    folder = machine.get('folder', '')
    if not isinstance(folder, str) or any(ord(c) < 32 for c in folder):
        raise ValueError('Carpeta inválida.')
    ipaddress.ip_address(machine['ip'])
    if not re.fullmatch(r'[a-zA-Z_][a-zA-Z0-9_.-]*', machine['user']):
        raise ValueError('Usuario SSH inválido.')
    if not Path(machine['key']).is_absolute():
        raise ValueError('La ruta de llave debe ser absoluta.')
    if type(machine.get('archived')) is not bool:
        raise ValueError('Estado de archivo inválido.')
    if any(ord(c) < 32 for c in machine['name'] + machine['os']):
        raise ValueError('Nombre o sistema con caracteres de control.')

def load():
    if not REGISTRY.exists():
        return []
    data = json.loads(REGISTRY.read_text(encoding='utf-8'))
    if not isinstance(data, list):
        raise ValueError('El registro debe ser una lista.')
    for machine in data:
        validate(machine)
    names = [m['name'].casefold() for m in data]
    if len(names) != len(set(names)):
        raise ValueError('Hay nombres duplicados en el registro.')
    return data

def save(machines):
    for machine in machines:
        validate(machine)
    write_json(REGISTRY, machines)

def write_json(path, data):
    DATA_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    DATA_DIR.chmod(0o700)
    fd, temporary = tempfile.mkstemp(dir=DATA_DIR, prefix='.machines-')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def load_folders():
    path = DATA_DIR / 'folders.json'
    folders = json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
    validate_folders(folders)
    # Conserva carpetas presentes en registros importados o anteriores.
    for machine in load():
        folder = machine.get('folder', '')
        if folder and folder not in folders: folders.append(folder)
    validate_folders(folders)
    return folders


def validate_folders(folders):
    if not isinstance(folders, list): raise ValueError('Registro de carpetas inválido.')
    for name in folders:
        if not isinstance(name, str) or not name.strip() or any(ord(c) < 32 for c in name):
            raise ValueError('Nombre de carpeta inválido.')
    if len({name.casefold() for name in folders}) != len(folders):
        raise ValueError('Hay carpetas con nombres duplicados.')


def save_folders(folders):
    validate_folders(folders)
    write_json(DATA_DIR / 'folders.json', folders)

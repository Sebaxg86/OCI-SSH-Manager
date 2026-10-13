"""Conexión con OpenSSH y confirmación nativa de huellas."""
import os
import stat
import subprocess
from pathlib import Path
from storage import validate

def prepare_key(raw):
    key = Path(raw).expanduser().resolve(strict=True)
    if not key.is_file() or key.stat().st_uid != os.getuid():
        raise ValueError('La llave debe ser un archivo de tu usuario.')
    key.chmod(0o600)
    return str(key)

def ssh_command(machine):
    validate(machine)
    return ['/usr/bin/ssh', '-F', '/dev/null',
            '-o', 'StrictHostKeyChecking=ask',
            '-o', 'FingerprintHash=sha256',
            '-o', 'UpdateHostKeys=no',
            '-o', 'VerifyHostKeyDNS=no',
            '-o', 'IdentitiesOnly=yes',
            '-o', 'ConnectTimeout=15',
            '-o', 'ForwardAgent=no',
            '-i', machine['key'], '-l', machine['user'], machine['ip']]

def connect(machine):
    machine = dict(machine)
    machine['key'] = prepare_key(machine['key'])
    print('\nSSH mostrará la huella SHA256 si el servidor es nuevo.')
    print('Compárala por un canal confiable antes de escribir yes.')
    print('Si la huella cambió, se bloqueará la conexión. No borres la anterior sin verificar.\n')
    result = subprocess.run(ssh_command(machine))
    if result.returncode:
        print(f'\nSSH terminó con código {result.returncode}. Revisa el mensaje anterior.')

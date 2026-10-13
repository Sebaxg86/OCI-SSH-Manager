#!/usr/bin/env python3
"""Menú de administración de conexiones SSH para macOS."""
from connection import connect, prepare_key
from storage import load, save, validate

DEFAULTS = {'1': ('Ubuntu', 'ubuntu'), '2': ('Oracle Linux', 'opc'),
            '3': ('Rocky', 'rocky'), '4': ('Otro', '')}

def ask(label, default=''):
    value = input(f'{label}' + (f' [{default}]' if default else '') + ': ').strip()
    return value or default

def choose(machines, archived=False):
    visible = [m for m in machines if m['archived'] == archived]
    if not visible:
        print('No hay máquinas en esta lista.')
        return None
    for index, machine in enumerate(visible, 1):
        print(f"{index}. {machine['name']} — {machine['user']}@{machine['ip']} ({machine['os']})")
    value = ask('Número (Enter cancela)')
    if not value:
        return None
    if not value.isdigit() or not 1 <= int(value) <= len(visible):
        raise ValueError('Elige un número de la lista.')
    return visible[int(value) - 1]

def register(machines):
    name = ask('Nombre')
    if any(m['name'].casefold() == name.casefold() for m in machines):
        raise ValueError('Ese nombre ya existe, incluso en archivadas.')
    ip = ask('IP pública IPv4 o IPv6')
    print('1. Ubuntu  2. Oracle Linux  3. Rocky  4. Otro')
    choice = ask('Sistema', '1')
    if choice not in DEFAULTS:
        raise ValueError('Sistema inválido.')
    system, default = DEFAULTS[choice]
    if choice == '4':
        system = ask('Nombre del sistema')
    user = ask('Usuario SSH (puedes editarlo)', default)
    raw = ask('Ruta de llave privada (sin comillas; acepta ~/ y espacios)')
    if not raw:
        raise ValueError('Falta la ruta de la llave.')
    from pathlib import Path
    machine = dict(name=name, ip=ip, os=system, user=user,
                   key=str(Path(raw).expanduser().absolute()), archived=False)
    validate(machine)
    print('Al guardar se aplicará chmod 600 a esta llave local.')
    if ask('Escribe GUARDAR para registrar') != 'GUARDAR':
        print('Cancelado.')
        return
    machine['key'] = prepare_key(raw)
    save(machines + [machine])
    print('Máquina registrada; llave con permisos 600.')

def main():
    while True:
        print('\nORACLE SSH — 1. Conectar  2. Registrar  3. Archivar  4. Restaurar  0. Salir')
        try:
            option = ask('Opción')
            if option == '0':
                return
            machines = load()
            if option == '1':
                machine = choose(machines)
                if machine:
                    connect(machine)
            elif option == '2':
                register(machines)
            elif option in ('3', '4'):
                machine = choose(machines, archived=(option == '4'))
                if machine:
                    machine['archived'] = option == '3'
                    save(machines)
                    print('Máquina archivada.' if option == '3' else 'Máquina restaurada.')
            else:
                print('Opción inválida.')
        except (ValueError, OSError) as error:
            print(f'No se completó la operación: {error}')
        except KeyboardInterrupt:
            print('\nOperación interrumpida; regresando al menú.')
        except EOFError:
            return

if __name__ == '__main__':
    main()

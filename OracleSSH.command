#!/bin/zsh
SCRIPT_DIR="${0:A:h}"
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
if ! command -v python3 >/dev/null 2>&1; then
  print 'Necesitas Python 3. Consulta LEEME.md dentro de esta carpeta.'
  read '?Presiona Enter para cerrar.'
  exit 1
fi
python3 "$SCRIPT_DIR/main.py"
status_code=$?
if (( status_code != 0 )); then
  print 'La aplicación terminó con un error.'
  read '?Presiona Enter para cerrar.'
fi
exit $status_code

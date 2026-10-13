# Interfaz gráfica

Abre `OCI SSH Manager.app` con doble clic. La guía de la interfaz gráfica y sus permisos está en `README.md`. El resto de este documento describe el menú de terminal original.

# Oracle SSH para macOS

## Instalación

Mantén juntos todos los archivos de esta carpeta y muévela a Documentos u otra ubicación permanente. Haz doble clic en `OracleSSH.command` para abrir el menú en Terminal. Ya tiene permisos de ejecución. Si los pierde al copiar, escribe `chmod +x ` en Terminal, arrastra el archivo a la ventana y pulsa Enter.

Requiere Python 3 (ya disponible en tu Mac) y OpenSSH. En otro equipo: https://www.python.org/downloads/macos/. No requiere paquetes adicionales.

## Uso

1. Registrar: introduce nombre, IP, sistema, usuario editable y ruta de llave privada, sin comillas. Acepta `~/` y espacios. Confirma con `GUARDAR`; aplica permisos 600 a la llave original, sin copiarla.
2. Conectar: selecciona una máquina. `exit` en el servidor devuelve al menú.
3. Archivar: oculta una máquina del listado de conexiones; no apaga ni elimina la instancia.
4. Restaurar: devuelve una máquina archivada al listado.
0. Salir.

Ubuntu sugiere `ubuntu`; Oracle Linux sugiere `opc`; Rocky sugiere `rocky`. Puedes editar el usuario al registrar.

## Huella del servidor

La primera conexión muestra la huella SHA256 y exige confirmación de OpenSSH. Compárala por un canal confiable antes de escribir `yes`. Por ejemplo, accede al servidor mediante la consola de OCI y ejecuta:

```sh
for key in /etc/ssh/ssh_host_*_key.pub; do
  ssh-keygen -lf "$key" -E sha256
done
```

Compara la huella del mismo tipo de clave indicado en Terminal. Escribe `no` si no puedes verificarla. La llave privada local autentica tu usuario; la clave del servidor identifica la máquina: son diferentes.

Se guardan las claves aceptadas en `~/.ssh/known_hosts`. Una clave cambiada bloquea la conexión. Verifica la causa y la nueva huella antes de modificar ese archivo; el programa no borra claves conocidas automáticamente.

La conexión usa `StrictHostKeyChecking=ask`, huellas SHA256, `UpdateHostKeys=no` y `VerifyHostKeyDNS=no`. No autoacepta claves nuevas. Ignora la configuración SSH personalizada mediante `-F /dev/null` y desactiva el reenvío del agente. Una llave cifrada puede pedir su contraseña.

Referencia: https://man.openbsd.org/ssh_config

## Diseño

- `OracleSSH.command`: lanzador independiente de la carpeta actual.
- `main.py`: menú y captura.
- `storage.py`: validación y registro JSON con escritura atómica.
- `connection.py`: permisos y conexión SSH sin ejecutar argumentos como código de shell.

Registro: `~/.config/oracle-ssh-cli/machines.json` (archivo 600, carpeta 700). Contiene nombre, IP, sistema, usuario, ruta local de llave y estado archivado. Nunca guarda el contenido de la llave. No modifica `~/.ssh/config`.

La llave debe existir y pertenecer a tu usuario. Se ajusta a 600 al registrar y antes de conectar. Un JSON dañado genera un error sin sustituirse por datos vacíos. No uses dos ventanas para modificar el registro simultáneamente: esta versión no coordina escrituras concurrentes.

## Alcance y validación

Administrador de SSH, no CLI oficial de OCI. Conexión directa por IP y puerto 22. No incluye bastiones, creación de instancias ni edición de registros desde el menú. La VM debe permitir SSH en sus reglas de red.

Se comprobaron persistencia, archivo/restauración, permisos, rechazo de entradas inválidas, opciones SSH, sintaxis del lanzador y salida del menú. Quedan pendientes el doble clic en Finder y una conexión real con tu VM y llave.

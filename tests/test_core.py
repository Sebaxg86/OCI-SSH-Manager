import sys
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
import shlex
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import storage
import terminal
from connection import prepare_key, ssh_command

class CoreTests(unittest.TestCase):
    def test_registry_permissions_and_archive(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with patch.object(storage, 'DATA_DIR', root/'data'), patch.object(storage, 'REGISTRY', root/'data'/'machines.json'):
                key = root/'key'; key.write_text('fixture')
                m = dict(name='VM',ip='192.0.2.1',os='Rocky',user='rocky',key=prepare_key(str(key)),archived=False)
                storage.save([m]); self.assertEqual(storage.load(), [m])
                self.assertEqual(key.stat().st_mode & 0o777,0o600)
                self.assertEqual(storage.REGISTRY.stat().st_mode & 0o777,0o600)
                for state in (True,False):
                    m['archived']=state; storage.save([m]); self.assertEqual(storage.load()[0]['archived'],state)
                storage.REGISTRY.write_text('{')
                with self.assertRaises(ValueError): storage.load()
                self.assertEqual(storage.REGISTRY.read_text(),'{')

    def test_terminal_shell_quoting_and_host_verification(self):
        with tempfile.TemporaryDirectory() as folder:
            key=Path(folder)/"key with spaces ' $(touch unexpected)"; key.write_text('fixture')
            m=dict(name='VM',ip='192.0.2.1',os='Ubuntu',user='ubuntu',key=str(key),archived=False)
            with patch.object(terminal, 'open_tab') as opened:
                terminal.connect_tab(m,'Pro')
            command,profile=opened.call_args.args
            argv=shlex.split(command.split('; ',1)[1])
            self.assertEqual(argv,ssh_command(dict(m,key=str(key.resolve()))))
            self.assertEqual(profile,'Pro')
            self.assertIn('StrictHostKeyChecking=ask',argv)
            self.assertIn('UpdateHostKeys=no',argv)
            self.assertFalse((Path(folder)/'unexpected').exists())

    def test_invalid_ip_user_are_rejected(self):
        m=dict(name='VM',ip='192.0.2.1',os='Ubuntu',user='ubuntu',key='/tmp/key',archived=False)
        for field in ('ip','user'):
            with self.subTest(field=field), self.assertRaises(ValueError):
                ssh_command(dict(m,**{field:'-oProxyCommand=bad'}))

if __name__=='__main__': unittest.main()

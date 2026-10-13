import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import storage

class FolderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.patchdir = patch.object(storage, 'DATA_DIR', self.root/'data')
        self.patchregistry = patch.object(storage, 'REGISTRY', self.root/'data'/'machines.json')
        self.patchdir.start(); self.patchregistry.start()

    def tearDown(self):
        self.patchdir.stop(); self.patchregistry.stop(); self.temp.cleanup()

    def test_empty_folders_persist_and_duplicate_does_not_overwrite(self):
        storage.save_folders(['Producción', 'Prácticas'])
        self.assertEqual(storage.load_folders(), ['Producción', 'Prácticas'])
        with self.assertRaises(ValueError): storage.save_folders(['Producción', 'producción'])
        self.assertEqual(storage.load_folders(), ['Producción', 'Prácticas'])
        self.assertEqual((storage.DATA_DIR/'folders.json').stat().st_mode & 0o777, 0o600)

    def test_old_registry_and_imported_folder(self):
        machine = dict(name='VM',ip='192.0.2.1',os='Ubuntu',user='ubuntu',key='/tmp/key',archived=False)
        storage.save([machine]); self.assertEqual(storage.load(),[machine])
        self.assertEqual(storage.load_folders(), [])
        machine['folder']='Importadas';storage.save([machine])
        self.assertEqual(storage.load_folders(), ['Importadas'])
        self.assertFalse(storage.load()[0]['archived'])

    def test_invalid_folder_is_rejected(self):
        for value in ('', '  ', 'Nombre\nOculto', 42):
            with self.subTest(value=value), self.assertRaises(ValueError): storage.save_folders([value])

if __name__ == '__main__': unittest.main()

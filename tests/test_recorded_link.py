import importlib.util
from pathlib import Path
import tempfile
import unittest


class RecordedLinkTests(unittest.TestCase):
    def load(self):
        path = Path(__file__).parents[1] / 'common/orbis-export/tools/recorded_link.py'
        spec = importlib.util.spec_from_file_location('recorded_link', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_relative_and_absolute_objects_use_build_directory(self):
        helper = self.load()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            relative = root / 'hotspot/variant-server/libjvm/objs/addnode.o'
            absolute = root / 'support/native/libjava/java.o'
            relative.parent.mkdir(parents=True)
            absolute.parent.mkdir(parents=True)
            relative.touch(); absolute.touch()
            result = helper.recorded_objects(['clang', str(relative.relative_to(root)), str(absolute), '-lc'], root)
            self.assertEqual(result, [relative, absolute])

    def test_response_file_paths_resolve_from_original_build_directory(self):
        helper = self.load()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            obj = root / 'support/native/with spaces/module.o'
            obj.parent.mkdir(parents=True)
            obj.touch()
            response = root / 'support/native/objects.txt'
            response.write_text('"support/native/with spaces/module.o"')
            self.assertEqual(helper.recorded_objects(['@support/native/objects.txt'], root), [obj])
            with self.assertRaises(ValueError):
                helper.recorded_objects(['hotspot/missing.o'], root)
            response.write_text('@support/native/objects.txt')
            with self.assertRaises(ValueError):
                helper.recorded_objects(['@support/native/objects.txt'], root)


if __name__ == '__main__':
    unittest.main()

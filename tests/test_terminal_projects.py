import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import tomllib
import unittest

from compose_application.projects import ProjectSpec, create_project, render_project
from compose_application.terminal_templates import TerminalProjectSpec


class TerminalProjectTests(unittest.TestCase):
    def test_passive_sources_select_independent_libraries(self):
        spec = TerminalProjectSpec('progress-desk')
        files = render_project(spec)
        metadata = tomllib.loads(files['pyproject.toml'])['project']
        self.assertEqual(metadata['dependencies'], list(spec.dependencies))
        self.assertEqual(spec.dependencies, ('carets==0.2.0', 'expose-interface==0.1.0'))
        self.assertNotIn('compose-application', ''.join(metadata['dependencies']))
        self.assertEqual(json.loads(files['reference-project.json']), spec.selection())
        for name, content in files.items():
            if name.endswith('.py'):
                compile(content, name, 'exec')
        # The existing web profile keeps its original immutable selection.
        self.assertEqual(ProjectSpec('progress-web', 'ui').selection()['profile'], 'ui')

    def test_repeat_preserves_owned_edits_and_mismatched_destinations_fail(self):
        with TemporaryDirectory() as directory:
            destination = Path(directory) / 'desk'
            spec = TerminalProjectSpec('progress-desk')
            self.assertTrue(create_project(spec, destination))
            app = destination / 'src/progress_desk/app.py'
            app.write_text('owner changes\n', encoding='utf-8')
            self.assertFalse(create_project(spec, destination))
            self.assertEqual(app.read_text(encoding='utf-8'), 'owner changes\n')
            with self.assertRaises(FileExistsError):
                create_project(TerminalProjectSpec('other-desk'), destination)
            with self.assertRaises(FileExistsError):
                create_project(ProjectSpec('progress-desk', 'ui'), destination)
        for name in ('carets', 'expose-interface', '../bad'):
            with self.assertRaises(ValueError):
                TerminalProjectSpec(name)

    @unittest.skipUnless(importlib.util.find_spec('carets') and importlib.util.find_spec('expose_interface'),
                         'optional terminal libraries are not installed')
    def test_generated_actual_command_reaches_shared_model_renderer_completion(self):
        with TemporaryDirectory() as directory:
            destination = Path(directory) / 'desk'
            create_project(TerminalProjectSpec('progress-desk'), destination)
            environment = dict(os.environ)
            environment['PYTHONPATH'] = os.pathsep.join([str(destination / 'src'), environment.get('PYTHONPATH', '')])
            result = subprocess.run([sys.executable, '-m', 'progress_desk', 'check'], cwd=directory,
                env=environment, text=True, capture_output=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            value = json.loads(result.stdout)
            self.assertEqual(value['status'], 'completed')
            self.assertGreaterEqual(value['frames'], 4)
            self.assertEqual(result.stderr, '')

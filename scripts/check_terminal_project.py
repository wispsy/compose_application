"""Install a generated terminal project outside the checkout and run its command."""
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

from compose_application.projects import create_project
from compose_application.terminal_templates import TerminalProjectSpec


def main():
    with TemporaryDirectory() as directory:
        outside = Path(directory)
        project = outside / 'project'
        create_project(TerminalProjectSpec('progress-desk'), project)
        environment = outside / 'env'
        subprocess.run(['uv', 'venv', str(environment), '--python', sys.executable], check=True)
        python = environment / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
        subprocess.run(['uv', 'pip', 'install', '--python', str(python), str(project)], check=True)
        process_environment = dict(os.environ)
        process_environment.pop('PYTHONPATH', None)
        result = subprocess.run([str(python), '-I', '-m', 'progress_desk', 'check'], cwd=outside,
            env=process_environment, capture_output=True, text=True, check=True, timeout=10)
        value = json.loads(result.stdout)
        assert value['status'] == 'completed' and value['frames'] >= 4 and not result.stderr
        command = environment / ('Scripts/progress-desk.exe' if sys.platform == 'win32' else 'bin/progress-desk')
        result = subprocess.run([str(command), 'check'], cwd=outside,
            env=process_environment, capture_output=True, text=True, check=True, timeout=10)
        assert json.loads(result.stdout)['status'] == 'completed' and not result.stderr
        subprocess.run(['uv', 'pip', 'check', '--python', str(python)], check=True)
        print(json.dumps({'schema': 1, 'selection': TerminalProjectSpec('progress-desk').selection(),
            'result': value, 'platform': sys.platform}, sort_keys=True))

if __name__ == '__main__':
    main()

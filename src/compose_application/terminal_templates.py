"""Application-owned terminal source; runtime libraries remain independent."""
from dataclasses import dataclass
import json

CARET_SOURCE = 'pypi:carets==0.2.0'
INTERFACE_SOURCE = 'pypi:expose-interface==0.1.0'


@dataclass(frozen=True)
class TerminalProjectSpec:
    """An explicit terminal profile selecting two independent library sources."""
    name: str

    def __post_init__(self):
        from .projects import ProjectSpec
        ProjectSpec(self.name, 'service')  # Reuse the existing safe name policy.
        if self.module in ('carets', 'expose_interface'):
            raise ValueError('Choose a project name that does not shadow a terminal dependency.')

    @property
    def module(self):
        return self.name.replace('-', '_')

    @property
    def profile(self):
        return 'terminal'

    @property
    def dependencies(self):
        return ('carets==0.2.0',
                'expose-interface==0.1.0')

    def selection(self):
        return {'format': 'terminal-project/1', 'name': self.name, 'profile': self.profile,
                'sources': {'carets': CARET_SOURCE, 'expose-interface': INTERFACE_SOURCE}}


APP = '''"""Owned domain model and Carets presentation for a finite offline workflow."""
import asyncio
from dataclasses import dataclass
import sys

from carets import (CellDiffRenderer, Command, CommandErrorMsg, KeyMsg, Msg, Program,
                    TerminalOptions, TerminalSession, WindowSizeMsg, truncate_ansi)
from carets.testing import SnapshotRenderer


@dataclass(frozen=True)
class Progress(Msg):
    stage: str


async def stages():
    # Replace this explicit finite source with your application service.
    for stage in ('prepare', 'run', 'completed'):
        yield Progress(stage)
        await asyncio.sleep(0)


class Application:
    def __init__(self, *, exit_on_completion=False):
        self.status, self.width, self.height = 'ready', 80, 24
        self.program = None
        self.exit_on_completion = exit_on_completion

    def update(self, message):
        if isinstance(message, WindowSizeMsg):
            self.width, self.height = max(1, message.width), max(1, message.height)
        elif isinstance(message, Progress):
            self.status = message.stage
            if self.status == 'completed' and self.exit_on_completion:
                self.program.stop()
        elif isinstance(message, CommandErrorMsg):
            self.status = 'failed'
            if self.exit_on_completion:
                self.program.stop()
        elif isinstance(message, KeyMsg) and message.key in ('q', 'ctrl-c'):
            self.program.stop()

    def view(self):
        lines = ['__PROJECT_NAME__', 'Status: ' + self.status, 'q quit']
        return '\\n'.join(truncate_ansi(line, self.width) for line in lines[:self.height])


class Renderer:
    def __init__(self, model):
        self.model, self.size, self.renderer = model, None, None

    def render(self, view):
        size = self.model.width, self.model.height
        if self.size != size:
            self.size, self.renderer = size, CellDiffRenderer(*size)
        return self.renderer.render(view)


async def check():
    model = Application(exit_on_completion=True)
    renderer = SnapshotRenderer()
    import io
    program = model.program = Program(model, renderer=renderer, output_stream=io.StringIO(), stream_buffer=2)
    await asyncio.wait_for(program.run([], stop_on_eof=False, commands=[Command.stream(stages)]), 2)
    if model.status != 'completed' or 'completed' not in renderer.latest:
        raise RuntimeError('Terminal reference did not reach verified completion')
    return {'schema': 1, 'status': model.status, 'frames': len(renderer.frames)}


async def terminal():
    session = TerminalSession(sys.stdin.buffer, sys.stderr, options=TerminalOptions(alternate_screen=True))
    if not session.capabilities.tty or not session.capabilities.raw:
        raise ValueError('Interactive mode requires a supported POSIX TTY')
    model = Application()
    program = model.program = Program(model, renderer=Renderer(model), terminal=session,
        input_stream=sys.stdin.buffer, output_stream=sys.stderr, stream_buffer=32)
    await program.run(commands=[Command.stream(stages)])
    return {'schema': 1, 'status': model.status}
'''

COMMAND = '''"""Typed Expose Interface commands over the same application."""
import contextlib
import json
import sys

from expose_interface import Interface, UsageError
from . import app as application


def main():
    interface = Interface('__PROJECT_NAME__', description='Application-owned terminal reference.')
    interface.command(name='check')(application.check)
    interface.command(name='terminal')(application.terminal)
    try:
        with contextlib.redirect_stdout(sys.stderr):
            result = interface.invoke()
        if result is not None:
            print(json.dumps(result, allow_nan=False))
            if result.get('status') != 'completed':
                raise SystemExit(1)
    except Exception as error:
        print(json.dumps({'schema': 1, 'status': 'failed', 'error': type(error).__name__}), file=sys.stderr)
        raise SystemExit(2 if isinstance(error, UsageError) else 1) from None


if __name__ == '__main__':
    main()
'''


def render_terminal_project(spec):
    metadata = f'''[project]
name = "{spec.name}"
version = "0.1.0"
requires-python = ">=3.14"
dependencies = {json.dumps(list(spec.dependencies))}

[project.scripts]
{spec.name} = "{spec.module}.__main__:main"

[build-system]
requires = ["uv_build>=0.12.19,<0.13.0"]
build-backend = "uv_build"
'''
    readme = f'''# {spec.name}

An application-owned terminal project using Expose Interface plus Carets.
Python 3.14+ and uv are required. Library versions are selected explicitly in
`reference-project.json`; no umbrella composition runtime is required.

```sh
uv sync
uv run {spec.name} check
uv run {spec.name} terminal
```

`check` runs the real message/model/renderer loop headlessly and prints one JSON
result. `terminal` opens a supported POSIX terminal, streams three finite offline
stages and waits for q to quit. One Program/TerminalSession owns input/output and
cleanup. Windows is qualified for headless behavior only. The domain source,
commands and presentation are yours in `src/{spec.module}/`; replace the finite
source with explicit application services and handle their outcomes/authority.

Generation installs nothing. A matching repeat preserves your edits and data;
a mismatched existing destination is refused. Existing service/ui/live project
profiles keep their qualified sources. Package publication and deployment are
separate concrete operations.
'''
    return {'pyproject.toml': metadata, 'README.md': readme,
            '.gitignore': '.venv/\n__pycache__/\n*.py[cod]\n.env\n',
            'reference-project.json': json.dumps(spec.selection(), sort_keys=True, indent=2) + '\n',
            f'src/{spec.module}/__init__.py': '"""Application-owned terminal project."""\n',
            f'src/{spec.module}/app.py': APP.replace('__PROJECT_NAME__', spec.name),
            f'src/{spec.module}/__main__.py': COMMAND.replace('__PROJECT_NAME__', spec.name)}

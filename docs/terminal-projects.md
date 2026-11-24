# Terminal application projects

The `terminal` generation profile composes Expose Interface and Carets directly.
It adds another application target to the existing optional API/web references.
No new CLI parser, terminal runtime or mandatory umbrella dependency is added.

```python
from compose_application.projects import create_project
from compose_application.terminal_templates import TerminalProjectSpec

create_project(TerminalProjectSpec('progress-desk'), './progress-desk')
```

The parent directory must exist. Selection receipts record the exact sources of
both libraries under `terminal-project/1`. `TerminalProjectSpec` is separate
from web `ProjectSpec` because terminal apps consume independent libraries;
they do not pretend the older fixed web reference contains a terminal extra.
The same safe publisher creates all profiles, publishes the receipt last,
refuses mismatches/symlinks, and preserves application-owned edits on repeats.
Generation performs no installation or activation.

The generated `app.py` owns a finite synthetic three-stage service and its Carets
model; `__main__.py` supplies typed commands. `check` consumes the real stream
through Program and a snapshot renderer outside a physical terminal. `terminal`
uses one TerminalSession/Program, handles resize and q/interrupt, then closes
background producers before restoration. Output goes to stderr; the command
prints a single JSON outcome on stdout. Replace the service with explicit
application behavior and preserve outcome/cancellation/authorization boundaries.

Source pins are a qualified development profile, not a published-release
promise. `scripts/check_terminal_project.py` installs a generated project outside
the checkout and executes both its module and console commands. CI runs this
on Linux/macOS/Windows; native interactive support remains POSIX-only. Optional
provider services and package publication/deployment retain their own decisions.

The [Cohesion Block B plan](https://github.com/wispsy/wispsy/blob/main/docs/cohesion-block-b/IMPLEMENTATION_PLAN.md)
tracks shared service/API composition, Carets design tokens and the later
Warewolf hub. Existing web/table/browser contracts and their queue remain intact.

The initial package preview generates exact index requirements
`carets==0.2.0` and `expose-interface==0.1.0`. Terminal applications remain
independent of the composition package at runtime. Existing source qualification
records retain their original library revisions.

# Live Python Compiler

A state-aware Python execution visualizer: type Python code, and watch the
program's *runtime state* — not just its console output — transform live as
each line executes.

```
CODE → EXECUTION → STATE CHANGE → VISUAL TRANSFORMATION
```

This is a real execution engine (Python's `sys.settrace`, not a fake/parsed
simulation), wired to a React + Monaco Editor frontend.

---

## What's inside

```
live-python-compiler/
  backend/
    app/
      main.py                 FastAPI app entrypoint
      models.py                Request/response schemas
      execution/
        tracer.py               sys.settrace-based line-by-line tracer
        engine.py                Compiles + runs code, builds the step timeline
        serialize.py             Turns arbitrary Python values into JSON-safe, type-tagged data
        diff.py                  Generic before/after diff between two variable snapshots
        transform.py             Builds the collapsed "Runtime" source view
      routes/execute.py         POST /api/execute
    requirements.txt
    Dockerfile
  frontend/
    src/
      App.jsx                   Top-level layout & state wiring
      components/
        EditorPanel.jsx          Monaco editor + Original/Runtime toggle
        VariablePanel.jsx         Expandable variable inspector
        Timeline.jsx               Play/pause/step/speed transport controls
        ConsolePanel.jsx           stdout + error display
        Header.jsx                  Brand bar + live-mode toggle
      hooks/
        useExecution.js           Debounced live-run + timeline playback state machine
        useDebounce.js
      services/api.js            Talks to the backend
      utils/renderValue.js       Renders the tagged value shape for display
    package.json / vite.config.js
    Dockerfile
  docker/
    executor/                  Placeholder for the production sandbox container (see Security below)
  docker-compose.yml
  .env.example
```

## How execution tracing works

1. The frontend POSTs `{ code }` to `POST /api/execute`.
2. `engine.py` compiles the code under a sentinel filename and runs it with
   `sys.settrace` active (`tracer.py`).
3. On every `line` / `call` / `return` / `exception` event inside the user's
   code, the tracer snapshots visible variables (`serialize.py`), captures the
   stdout produced since the last step, and records which source line just
   finished.
4. `diff.py` compares each step's variables to the previous step's and tags
   each variable `added` / `modified` / `removed` / `unchanged`, plus
   index-level hints for list/tuple/set changes so the UI can animate the
   right elements — generically, with **no special-casing of `.append()`,
   `.pop()`, etc.** Any statement that changes a variable's value is picked
   up the same way.
5. `transform.py` walks the AST once more to build the **Runtime** view: for
   every variable, it finds the *last* line that touched it and rewrites that
   line as `name = <final value>`, dropping the intermediate mutation lines
   from the transformed text. The **Original** source is never edited — both
   are always available via the toggle in the editor panel.

## Running it locally

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The Vite dev server proxies `/api/*` to
`http://localhost:8000` (see `frontend/vite.config.js`), so no extra env
config is needed for local dev. To point at a different backend host, copy
`.env.example` to `frontend/.env` and set `VITE_API_BASE_URL`.

### Docker Compose
```bash
docker compose up --build
```
Frontend on `:5173`, backend on `:8000`.

## Try it

Paste this into the editor (or use the sample that loads by default):

```python
lst = [10, 20, 30, 50]
lst.append(50)
print(lst)
```

- The **Runtime State** panel shows `lst` growing to `[10, 20, 30, 50, 50]`
  with the new element highlighted.
- The **Runtime** toggle in the editor collapses the source to
  `lst = [10, 20, 30, 50, 50]` / `print(lst)`.
- The **Console** shows `[10, 20, 30, 50, 50]`.
- The **Timeline** shows 3 steps you can scrub through with ⏮ / ▶ / ⏭, at
  0.5x–5x speed.

Other things worth trying: `x += 5`, `lst.pop()`, `lst[0] = 100`,
`d["age"] = 20`, a `for`/`while` loop, a function with `return`, and code
that raises `IndexError`/`KeyError`/`ZeroDivisionError` (click the error
card to jump the editor to the failing line).

## Live mode

The `LIVE EXECUTION` toggle in the header controls whether code re-runs
automatically. When on, edits are debounced ~500ms before executing; while
the code is syntactically invalid mid-edit, the app shows "Waiting for valid
Python…" instead of erroring. When off, use the ▶ button in the header to
run manually.

## Error handling

`SyntaxError`, `NameError`, `TypeError`, `IndexError`, `KeyError`,
`ValueError`, `ZeroDivisionError`, and other runtime exceptions are all
caught and returned with type, message, and offending line. Infinite loops
are stopped by both a wall-clock timeout (`timeout_seconds`, default 5s) and
a step-count cap (`max_steps`, default 2000) — whichever trips first.

## Security — read before deploying anywhere public

**The backend currently executes user code in-process with `exec()`.** That
is fine for local development on your own machine, but it is **not** a
sandbox: it does not stop someone from reading files, spawning processes, or
exhausting memory on the host. `docker/executor/` documents the intended
replacement:

- A separate, network-disabled container per execution (or a short-lived
  pool of pre-warmed ones)
- `--network none`, capped CPU/memory, `--pids-limit`, read-only filesystem,
  non-root user, `--cap-drop ALL`
- The host FastAPI process calls into that container instead of importing
  `engine.py` directly

`backend/app/execution/engine.py` is already isolated from the FastAPI route
layer specifically so this swap is a small, contained change — see the
Dockerfile comments in `docker/executor/` for the exact `docker run` flags to
use once you wire it up.

## Known limitations (MVP scope)

- Variable scoping inside function calls is shown as a merged view of
  globals + the active function's locals, rather than fully scope-isolated
  nested frames — fine for the supported feature set (single-level function
  calls, loops, conditionals), but deeply nested/recursive calls will show a
  flattened variable list rather than a call stack.
- The Runtime-view transform handles the common shapes described above
  (assignment, augmented assignment, subscript assignment, single mutating
  method calls). Highly dynamic code (e.g. `exec`-generated variable names,
  `globals()` manipulation) falls back to echoing the original source
  unchanged rather than guessing.

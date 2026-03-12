# CLAUDE.md — CharlotteLang Interpreter

## Project Overview

CharlotteLang is a dog-themed programming language interpreter written in Python. The entire interpreter lives in a single file (`charlotte.py`) with no external dependencies beyond Python 3.10+.

## Quick Commands

```bash
# Run a .bark file
python charlotte.py run <file.bark>

# Start interactive REPL
python charlotte.py repl

# Run the feature demo
python charlotte.py run examples/new_features.bark
```

## Architecture

The interpreter is a single-file design (`charlotte.py`) with these components:

1. **Exception classes** — `CharlotteError`, `CharlotteReturn`, `CharlotteBreak`, `CharlotteContinue`
2. **Tokenizer** — `Line` class + `parse_lines()` function. Line-based (not token-based). Strips blanks and comments, tracks indentation.
3. **Interpreter** — `Interpreter` class with:
   - `run(source)` — resets all state then calls `execute()`
   - `execute(source)` — runs source **without** resetting state (used by REPL for session continuity)
   - `_execute_block()` — main statement dispatcher
   - `_evaluate()` — recursive expression evaluator
   - `_handle_*()` methods for each statement type
   - `_call_function()` — calls user-defined functions with deep-copied scope isolation
   - `_validate_url()` / `_http_request()` — URL security validation and HTTP request execution
   - `_to_json_compatible()` — converts CharlotteLang values to JSON-serializable Python objects
   - `env_allowlist` constructor param — `None` (default blocklist) or a set of permitted env var names
   - `url_allowlist` constructor param — `None` (any http/https) or a set of permitted hostnames
   - `http_timeout` constructor param — request timeout in seconds (default 10, max 30)
4. **REPL** — `run_repl()` with buffer-based multi-line input; uses `execute()` so variables persist across `.run` commands
5. **CLI** — `main()` entry point with `run`, `repl`, `help` commands

## Language Keyword Mapping

| Keyword | Meaning |
|---------|---------|
| `bark` | print to stdout (`bark` alone prints blank line) |
| `howl` | print to stderr |
| `growl` | raise error |
| `fetch` | create variable |
| `sniff` | if (ends with `:`) or legacy comment (no colon) |
| `woof` | comment (always — preferred) |
| `else sniff` | elif |
| `else pout` | else |
| `zoomies` | loop (for/foreach/while) |
| `teach trick` | define function |
| `rollover` | return |
| `shake off` | break |
| `keep going` | continue |
| `careful` / `oops` | try / catch |
| `snag` | import (sandboxed to the source directory subtree) |
| `bunny[]` | array literal |
| `collar{}` | dictionary literal |
| `loyal` / `stranger` | true / false |
| `napping` | null/None |
| `squirrel()` | random number |
| `nap(s)` | sleep |
| `sniff_env(v)` | get environment variable (sensitive names blocked by default; see `env_allowlist`) |
| `beg(prompt)` | read user input from stdin (returns string) |
| `dig_up(url)` | HTTP GET → collar with `status`, `body`, `headers` (optional 2nd arg: headers collar) |
| `bury(url, data)` | HTTP POST → same collar (optional 3rd arg: headers collar) |
| `chew_json(s)` | parse JSON string into collar/bunny/value |
| `yap_json(v)` | serialize value to JSON string |
| `zoomies VAR through` | named foreach — `VAR` holds each item, `lap` holds index |
| `loyal(x)` | convert to bool |
| `abs(x)` | absolute value |
| `round(x, n)` | round a number |
| `min(...)` / `max(...)` | min/max of args or a list |
| `x ** y` | power/exponent |
| `"s" * n` | string repetition |
| `x not in collection` | negative membership test |
| `a > b` / `a < b` | symbolic greater/less-than (aliases for `is bigger than` / `is smaller than`) |

## Code Conventions

- All interpreter logic is in `charlotte.py` — keep it as a single file
- Dog-themed naming for all language keywords and error messages
- Error messages use the 🐾 emoji prefix and playful dog personality
- Example files use the `.bark` extension and live in `examples/`
- No external dependencies — stdlib only (`copy` for scope isolation, `json` for JSON serialization, `urllib` for HTTP requests)
- Python 3.10+ required (uses `match` statement type hints like `list[Line]`)

## Testing

Run the full test suite with pytest (418 tests):

```bash
python -m pytest tests/
```

Or run a specific class:

```bash
python -m pytest tests/ -k TestLoops -v
```

The test file is `tests/test_charlotte.py`. It covers tokenizer, I/O, variables, arithmetic, comparisons, control flow, loops, functions, arrays, dicts, strings, try/catch, imports, built-ins, slicing, escape sequences, and all recently added features (`woof` comments, escaped-quote arg parsing, `squirrel`/`nap`/`sniff_env`, `beg`, named `zoomies`, `bark` blank line, `howl` stderr, `>` / `<` operators, REPL state persistence, function scope isolation, collar colon-split with slices, bounded error wrapping, `sniff_env` allowlist/blocklist, `snag` path sandboxing, `dig_up`/`bury` HTTP requests, `chew_json`/`yap_json` JSON serialization, `url_allowlist` host restriction, parenthesized expression grouping, `**` operator precedence, `stranger` string truthiness). Example files are also smoke-tested.

To manually verify examples:

```bash
python charlotte.py run examples/hello.bark
python charlotte.py run examples/fizzbuzz.bark
python charlotte.py run examples/full_day.bark
python charlotte.py run examples/new_features.bark
```

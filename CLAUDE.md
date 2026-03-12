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
   - `_execute_block()` — main statement dispatcher
   - `_evaluate()` — recursive expression evaluator
   - `_handle_*()` methods for each statement type
   - `_call_function()` for user-defined function calls
4. **REPL** — `run_repl()` with buffer-based multi-line input
5. **CLI** — `main()` entry point with `run`, `repl`, `help` commands

## Language Keyword Mapping

| Keyword | Meaning |
|---------|---------|
| `bark` | print |
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
| `snag` | import |
| `bunny[]` | array literal |
| `collar{}` | dictionary literal |
| `loyal` / `stranger` | true / false |
| `napping` | null/None |
| `squirrel()` | random number |
| `nap(s)` | sleep |
| `sniff_env(v)` | get environment variable |
| `beg(prompt)` | read user input from stdin (returns string) |
| `zoomies VAR through` | named foreach — `VAR` holds each item, `lap` holds index |
| `loyal(x)` | convert to bool |
| `abs(x)` | absolute value |
| `round(x, n)` | round a number |
| `min(...)` / `max(...)` | min/max of args or a list |
| `x ** y` | power/exponent |
| `"s" * n` | string repetition |
| `x not in collection` | negative membership test |

## Code Conventions

- All interpreter logic is in `charlotte.py` — keep it as a single file
- Dog-themed naming for all language keywords and error messages
- Error messages use the 🐾 emoji prefix and playful dog personality
- Example files use the `.bark` extension and live in `examples/`
- No external dependencies — stdlib only
- Python 3.10+ required (uses `match` statement type hints like `list[Line]`)

## Testing

Run the full test suite with pytest (305 tests):

```bash
python -m pytest tests/
```

Or run a specific class:

```bash
python -m pytest tests/ -k TestLoops -v
```

The test file is `tests/test_charlotte.py`. It covers tokenizer, I/O, variables, arithmetic, comparisons, control flow, loops, functions, arrays, dicts, strings, try/catch, imports, built-ins, slicing, escape sequences, and all recently added features (`woof` comments, escaped-quote arg parsing, `squirrel`/`nap`/`sniff_env`, `beg`, named `zoomies`). Example files are also smoke-tested.

To manually verify examples:

```bash
python charlotte.py run examples/hello.bark
python charlotte.py run examples/fizzbuzz.bark
python charlotte.py run examples/full_day.bark
python charlotte.py run examples/new_features.bark
```

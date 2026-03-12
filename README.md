# 🐕 CharlotteLang v4.2

**A Pythonic programming language with chihuahua soul and pitbull energy.**

CharlotteLang is a fun, expressive programming language inspired by Charlotte — a chihuahua who thinks she's a pitbull, loves her stuffed animal Bunny, and demands belly scratches on her own terms.

It uses **Python-style indentation** for blocks, with Charlotte-flavored keywords that make coding feel like hanging out with a tiny, fearless dog.

## Installation

```bash
# Clone and install
cd charlottelang
pip install -e .

# Now you can use the charlotte command!
charlotte run examples/hello.bark
charlotte repl
```

**Or just run directly with Python:**

```bash
python charlotte.py run examples/hello.bark
python charlotte.py repl
```

## Quick Start

Create a file called `hello.bark`:

```
sniff My first Charlotte program!

bark "Yap yap! Hello World! 🐾"

fetch treats = 10
bark f"Charlotte has {treats} treats!"
```

Run it:

```bash
charlotte run hello.bark
```

## Language Reference

### I/O
| Charlotte | Python | Description |
|-----------|--------|-------------|
| `bark "hello"` | `print("hello")` | Print to stdout |
| `bark` | `print()` | Print a blank line |
| `howl "warning"` | `print("warning", file=sys.stderr)` | Print to stderr |
| `howl` | `print(file=sys.stderr)` | Print blank line to stderr |
| `growl "error"` | `raise Exception("error")` | Throw an error |

### Variables
| Charlotte | Python | Description |
|-----------|--------|-------------|
| `fetch x = 10` | `x = 10` | Create a variable |
| `x = 20` | `x = 20` | Reassign |
| `bunny[1, 2, 3]` | `[1, 2, 3]` | Array literal |
| `collar{"a": 1, "b": 2}` | `{"a": 1, "b": 2}` | Dictionary literal |
| `list.toys` | `len(list)` | Length (lists, strings, dicts) |
| `list.give("item")` | `list.append("item")` | Append to list |
| `loyal` / `stranger` | `True` / `False` | Booleans |
| `napping` | `None` | Null value |
| `f"hi {name}"` or `f'hi {name}'` | `f"hi {name}"` | F-string interpolation (double or single quotes) |
| `"line1\nline2"` | `"line1\nline2"` | Escape sequences (`\n` `\t` `\\` `\"`) |

### Arrays (Lists)
| Charlotte | Python | Description |
|-----------|--------|-------------|
| `bunny[1, 2, 3]` | `[1, 2, 3]` | Array literal |
| `arr[0]` | `arr[0]` | Index access |
| `arr[0][1]` | `arr[0][1]` | Chained / nested index access |
| `arr[-1]` | `arr[-1]` | Negative index (last element) |
| `arr[1:3]` | `arr[1:3]` | Slice `[start:stop:step]` |
| `arr.toys` | `len(arr)` | Length |
| `arr.give(val)` | `arr.append(val)` | Append |
| `arr.pop()` / `arr.pop(idx)` | `arr.pop()` | Remove and return element |
| `arr.sort()` | `arr.sort()` | Sort in-place |
| `arr.reverse()` | `arr.reverse()` | Reverse in-place |
| `arr.remove(val)` | `arr.remove(val)` | Remove first occurrence |
| `arr.index(val)` | `arr.index(val)` | Find position (-1 if missing) |
| `arr.join(",")` | `",".join(arr)` | Join elements to string |

### Dictionaries
| Charlotte | Python | Description |
|-----------|--------|-------------|
| `collar{"a": 1}` | `{"a": 1}` | Dictionary literal |
| `collar{}` | `{}` | Empty dictionary |
| `d["key"]` | `d["key"]` | Access value by key |
| `d["key"] = val` | `d["key"] = val` | Set value by key |
| `d.bury("key", val)` | `d["key"] = val` | Set value (method) |
| `d.dig("key")` | `del d["key"]` | Remove key |
| `d.keys` | `list(d.keys())` | Get keys as list |
| `d.values` | `list(d.values())` | Get values as list |
| `d.toys` | `len(d)` | Number of entries |
| `"key" in d` | `"key" in d` | Check key existence |

### Control Flow
| Charlotte | Python | Description |
|-----------|--------|-------------|
| `sniff x > 5:` | `if x > 5:` | If statement |
| `else sniff x == 3:` | `elif x == 3:` | Elif |
| `else pout:` | `else:` | Else |
| `zoomies 5 times:` | `for lap in range(5):` | For loop (`lap` = index) |
| `zoomies through list:` | `for toy in list:` | For-each (`toy` = item, `lap` = index) |
| `zoomies item through list:` | `for item in list:` | Named for-each (`item` = custom var, `lap` = index) |
| `zoomies while x > 0:` | `while x > 0:` | While loop |
| `shake off` | `break` | Break out of loop |
| `keep going` | `continue` | Skip to next iteration |

### Functions
| Charlotte | Python | Description |
|-----------|--------|-------------|
| `teach trick greet(who):` | `def greet(who):` | Define function |
| `rollover value` | `return value` | Return from function |

### Error Handling
| Charlotte | Python | Description |
|-----------|--------|-------------|
| `careful:` | `try:` | Start try block |
| `oops e:` | `except Exception as e:` | Catch errors (e = error message) |
| `oops:` | `except:` | Catch errors (no variable) |

```
careful:
  growl "something went wrong!"
oops e:
  bark f"Caught: {e}"
```

### Imports
| Charlotte | Python | Description |
|-----------|--------|-------------|
| `snag "helpers.bark"` | `import helpers` | Import and execute another .bark file |

Imports are resolved relative to the current file. Circular imports are automatically prevented.

**Security:** `snag` can only load files within the same directory as the running script (or its subdirectories). Attempts to escape via `../` or absolute paths outside the project directory are blocked.

```
snag "helpers.bark"
```

### Operators
| Charlotte | Python | Description |
|-----------|--------|-------------|
| `a ~ b` | `a + b` (strings) | String concatenation |
| `a equals b` or `a == b` | `a == b` | Equality |
| `a not equals b` or `a != b` | `a != b` | Inequality |
| `a is bigger than b` or `a > b` | `a > b` | Greater than |
| `a is smaller than b` or `a < b` | `a < b` | Less than |
| `and` / `or` / `not` | `and` / `or` / `not` | Logical operators |
| `item in list` | `item in list` | Membership test (lists, dicts, strings) |
| `item not in list` | `item not in list` | Negative membership test |
| `+ - * / // % **` | `+ - * / // % **` | Arithmetic (`**` = power/exponent) |
| `-x` | `-x` | Unary minus — negate any variable or expression |
| `"ha" * 3` | `"ha" * 3` | String repetition → `"hahaha"` |

### Built-in Functions
| Charlotte | Python | Description |
|-----------|--------|-------------|
| `howBig(x)` | `len(x)` | Length of list, string, or dict |
| `treat(x)` | `float(x)` | Convert to float |
| `goodBoy(x)` | `int(x)` | Convert to integer |
| `yap(x)` | `str(x)` | Convert to string |
| `breed(x)` | `type(x).__name__` | Get type name (`"number"`, `"string"`, `"bunny"`, `"collar"`, `"boolean"`, `"napping"`) |
| `squirrel()` | `random.random()` | Random float 0.0–1.0 |
| `squirrel(n)` | `random.randrange(n)` | Random int 0 to n-1 |
| `squirrel(a, b)` | `random.randint(a, b)` | Random int a to b inclusive |
| `nap(seconds)` | `time.sleep(seconds)` | Sleep for N seconds |
| `sniff_env("VAR")` | `os.environ.get("VAR")` | Get environment variable, or `napping` if unset. Sensitive names (containing `SECRET`, `PASSWORD`, `TOKEN`, `KEY`, etc.) are blocked by default. |
| `loyal(x)` | `bool(x)` | Convert to boolean |
| `abs(x)` | `abs(x)` | Absolute value |
| `round(x)` / `round(x, n)` | `round(x, n)` | Round a number |
| `min(a, b)` / `min(list)` | `min(a, b)` | Minimum value |
| `max(a, b)` / `max(list)` | `max(a, b)` | Maximum value |
| `beg("prompt")` | `input("prompt")` | Read user input from stdin |
| `floor(x)` | `math.floor(x)` | Round down to nearest integer |
| `ceil(x)` | `math.ceil(x)` | Round up to nearest integer |

### HTTP & JSON
| Charlotte | Python | Description |
|-----------|--------|-------------|
| `dig_up(url)` | `urllib.request.urlopen(url)` | HTTP GET — returns collar with `status`, `body`, `headers` |
| `dig_up(url, headers)` | *(with headers dict)* | HTTP GET with custom headers |
| `bury(url, data)` | *(POST request)* | HTTP POST — returns same response collar |
| `bury(url, data, headers)` | *(with headers dict)* | HTTP POST with custom headers |
| `chew_json(string)` | `json.loads(string)` | Parse JSON string → collar/bunny/value |
| `yap_json(value)` | `json.dumps(value)` | Serialize collar/bunny/value → JSON string |

**Response collar format:** Every `dig_up`/`bury` call returns a collar (dict) with three keys:
- `"status"` — HTTP status code (e.g. `200`, `404`)
- `"body"` — response body as a string
- `"headers"` — response headers as a collar

```
woof Fetch data from an API
fetch resp = dig_up("https://api.example.com/dogs")
sniff resp["status"] == 200:
  fetch dogs = chew_json(resp["body"])
  bark f"Found {dogs.toys} dogs!"

woof Post JSON data
fetch payload = yap_json(collar{"name": "Charlotte", "breed": "chihuahua"})
fetch result = bury("https://api.example.com/dogs", payload)
bark f"Created with status: {result['status']}"

woof Custom headers (e.g. auth)
fetch headers = collar{"Authorization": "Bearer my-token"}
fetch resp = dig_up("https://api.example.com/me", headers)

woof Error handling
careful:
  fetch resp = dig_up("https://unreachable.example.com")
oops e:
  bark f"Request failed: {e}"
```

### String Methods
| Charlotte | Python | Description |
|-----------|--------|-------------|
| `s.chew(",")` | `s.split(",")` | Split string into list |
| `s.trim()` | `s.strip()` | Remove leading/trailing whitespace |
| `s.upper()` | `s.upper()` | Convert to uppercase |
| `s.lower()` | `s.lower()` | Convert to lowercase |
| `s.replace("a","b")` | `s.replace("a","b")` | Replace occurrences |
| `s.find("sub")` | `s.find("sub")` | Find position (-1 if missing) |
| `s.startswith("x")` | `s.startswith("x")` | Check prefix (returns boolean) |
| `s.endswith("x")` | `s.endswith("x")` | Check suffix (returns boolean) |

### Comments
```
woof This is always a comment, even if it ends with a colon:
sniff This is also a comment — as long as it doesn't end with a colon
```

`woof` is the preferred comment syntax — it's unambiguous regardless of content. `sniff` without a trailing `:` also works for backward compatibility, but avoid ending `sniff` comments with `:` since that makes them look like `if` statements.

## REPL

Start the interactive REPL:

```bash
charlotte repl
```

REPL commands:
- `.run` — execute the buffer
- `.clear` — clear the buffer
- `.show` — show the buffer
- `.vars` — display all current variables and their values
- `.help` — quick reference card
- `.exit` — leave the REPL

The REPL supports up-arrow history (via `readline` when available).

Single-line statements auto-execute. Multi-line blocks (anything ending with `:`) are buffered until you type `.run`.

Variables and functions defined in one `.run` session persist for the next — the REPL maintains state across executions. Use `.vars` to inspect current state. To fully reset, restart the REPL.

## Examples

See the `examples/` directory:
- `hello.bark` — Hello World basics
- `fizzbuzz.bark` — FizzBuzz, Charlotte-style
- `full_day.bark` — A full day in Charlotte's life
- `new_features.bark` — Demo of v3.0 features (dicts, try/catch, imports, string methods, etc.)
- `helpers.bark` — Helper library used by new_features.bark (demonstrates imports)

## Security

CharlotteLang is designed for trusted personal use. Several protections are built in:

**`snag` sandbox** — import statements can only load `.bark` files within the same directory as the running script (or its subdirectories). Path traversal (`../`) and absolute paths outside the project tree are blocked.

**`sniff_env` blocklist** — environment variable names containing sensitive substrings (`SECRET`, `PASSWORD`, `TOKEN`, `API_KEY`, `ACCESS_KEY`, `CREDENTIAL`, `PRIVATE`, etc.) are blocked by default and raise a `CharlotteError`. This prevents `.bark` scripts from accidentally (or maliciously) leaking secrets from the process environment.

**HTTP restrictions** — `dig_up` and `bury` enforce several safeguards:
- **Scheme restriction** — only `http://` and `https://` URLs are allowed; `file://`, `ftp://`, etc. are blocked.
- **Timeout** — requests time out after 10 seconds by default (configurable, max 30s).
- **Response size cap** — responses are limited to 10 MB to prevent memory exhaustion.
- **Optional host allowlist** — restrict which hosts scripts can contact (see below).

For programmatic use, the `Interpreter` class accepts security parameters:

```python
# Only permit specific env vars; block everything else
interp = Interpreter(env_allowlist=["HOME", "PATH", "LANG"])

# Block all env access
interp = Interpreter(env_allowlist=[])

# Only allow HTTP to specific hosts
interp = Interpreter(url_allowlist=["api.example.com", "localhost"])

# Block all HTTP (empty allowlist)
interp = Interpreter(url_allowlist=[])

# Custom timeout (max 30 seconds)
interp = Interpreter(http_timeout=5)

# Default: non-sensitive env vars allowed, any http/https URL allowed
interp = Interpreter()
```

> **Note:** CharlotteLang has no process sandbox. Do not run untrusted `.bark` scripts with elevated privileges.

## The Philosophy

> "Small dog. Big bark. Pythonic syntax. Even bigger heart."

---

*Made with 🐾 and pitbull energy*

# 🐕 CharlotteLang v4.0

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
| `bark "hello"` | `print("hello")` | Print to console |
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
| `f"hi {name}"` | `f"hi {name}"` | F-string interpolation |
| `"line1\nline2"` | `"line1\nline2"` | Escape sequences (`\n` `\t` `\\` `\"`) |

### Arrays (Lists)
| Charlotte | Python | Description |
|-----------|--------|-------------|
| `bunny[1, 2, 3]` | `[1, 2, 3]` | Array literal |
| `arr[0]` | `arr[0]` | Index access |
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

```
snag "helpers.bark"
```

### Operators
| Charlotte | Python | Description |
|-----------|--------|-------------|
| `a ~ b` | `a + b` (strings) | String concatenation |
| `a equals b` or `a == b` | `a == b` | Equality |
| `a not equals b` or `a != b` | `a != b` | Inequality |
| `a is bigger than b` | `a > b` | Greater than |
| `a is smaller than b` | `a < b` | Less than |
| `and` / `or` / `not` | `and` / `or` / `not` | Logical operators |
| `item in list` | `item in list` | Membership test (lists, dicts, strings) |
| `+ - * / // %` | `+ - * / // %` | Arithmetic |

### Built-in Functions
| Charlotte | Python | Description |
|-----------|--------|-------------|
| `howBig(x)` | `len(x)` | Length of list, string, or dict |
| `treat(x)` | `float(x)` | Convert to float |
| `goodBoy(x)` | `int(x)` | Convert to integer |
| `yap(x)` | `str(x)` | Convert to string |
| `breed(x)` | `type(x).__name__` | Get type name (`"number"`, `"string"`, `"bunny"`, `"collar"`, `"boolean"`, `"napping"`) |

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
sniff This is a comment — Charlotte sniffs it and moves on
```

## REPL

Start the interactive REPL:

```bash
charlotte repl
```

REPL commands:
- `.run` — execute the buffer
- `.clear` — clear the buffer
- `.show` — show the buffer
- `.help` — quick reference card
- `.exit` — leave the REPL

Single-line statements auto-execute. Multi-line blocks (anything ending with `:`) are buffered until you type `.run`.

## Examples

See the `examples/` directory:
- `hello.bark` — Hello World basics
- `fizzbuzz.bark` — FizzBuzz, Charlotte-style
- `full_day.bark` — A full day in Charlotte's life
- `new_features.bark` — Demo of v3.0 features (dicts, try/catch, imports, string methods, etc.)
- `helpers.bark` — Helper library used by new_features.bark (demonstrates imports)

## The Philosophy

> "Small dog. Big bark. Pythonic syntax. Even bigger heart."

---

*Made with 🐾 and pitbull energy*

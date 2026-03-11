# 🐕 CharlotteLang v2.0

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
| `list.toys` | `len(list)` | Length |
| `list.give("item")` | `list.append("item")` | Append |
| `loyal` / `stranger` | `True` / `False` | Booleans |
| `napping` | `None` | Null value |
| `f"hi {name}"` | `f"hi {name}"` | F-string interpolation |

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

### Functions
| Charlotte | Python | Description |
|-----------|--------|-------------|
| `teach trick greet(who):` | `def greet(who):` | Define function |
| `rollover value` | `return value` | Return from function |

### Operators
| Charlotte | Python | Description |
|-----------|--------|-------------|
| `a ~ b` | `a + b` (strings) | String concatenation |
| `a equals b` or `a == b` | `a == b` | Equality |
| `a not equals b` or `a != b` | `a != b` | Inequality |
| `a is bigger than b` | `a > b` | Greater than |
| `a is smaller than b` | `a < b` | Less than |
| `and` / `or` / `not` | `and` / `or` / `not` | Logical operators |
| `item in list` | `item in list` | Membership test |
| `+ - * / // %` | `+ - * / // %` | Arithmetic |

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

## The Philosophy

> "Small dog. Big bark. Pythonic syntax. Even bigger heart."

---

*Made with 🐾 and pitbull energy*

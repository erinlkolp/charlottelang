#!/usr/bin/env python3
"""
CharlotteLang Interpreter v2.0
A Pythonic programming language with chihuahua soul and pitbull energy.

Usage:
    charlotte run <file.bark>
    charlotte repl
    charlotte --help
"""

import sys
import os


class CharlotteError(Exception):
    """Base error for CharlotteLang runtime errors."""
    def __init__(self, message, line_num=None):
        self.line_num = line_num
        prefix = f"Line {line_num}: " if line_num else ""
        super().__init__(f"🐾 {prefix}{message}")


class CharlotteReturn(Exception):
    """Used internally to handle rollover (return) statements."""
    def __init__(self, value):
        self.value = value


class CharlotteBreak(Exception):
    """Used internally to handle shake off (break) statements."""
    pass


# ─── TOKENIZER ─────────────────────────────────────────────

class Line:
    """A parsed line with its text content, indentation level, and source line number."""
    __slots__ = ("text", "indent", "line_num")

    def __init__(self, text: str, indent: int, line_num: int):
        self.text = text
        self.indent = indent
        self.line_num = line_num

    def __repr__(self):
        return f"Line({self.line_num}: {'  ' * (self.indent // 2)}{self.text})"


def parse_lines(source: str) -> list[Line]:
    """Parse source code into Line objects, stripping blanks and comments."""
    lines = []
    for i, raw in enumerate(source.split("\n"), start=1):
        stripped = raw.rstrip()
        if not stripped:
            continue
        trimmed = stripped.lstrip()
        # Comments: bare "sniff" lines without a trailing colon
        if trimmed.startswith("sniff ") and not trimmed.endswith(":"):
            continue
        if trimmed == "sniff":
            continue
        indent = len(stripped) - len(trimmed)
        lines.append(Line(trimmed, indent, i))
    return lines


# ─── INTERPRETER ───────────────────────────────────────────

class Interpreter:
    """The CharlotteLang interpreter engine."""

    MAX_LOOPS = 10_000

    def __init__(self, output_fn=None):
        self.variables: dict = {}
        self.functions: dict = {}
        self.output_fn = output_fn or (lambda text, kind="bark": print(text))

    def run(self, source: str):
        """Run a CharlotteLang program from source string."""
        self.variables = {}
        self.functions = {}
        lines = parse_lines(source)
        try:
            self._execute_block(lines)
        except CharlotteReturn:
            pass  # Top-level rollover is fine
        except CharlotteBreak:
            pass  # Top-level shake off is fine
        except CharlotteError as e:
            self.output_fn(str(e), "error")
        except Exception as e:
            self.output_fn(f"🐾 Unexpected error: {e}", "error")

    # ── Block execution ──

    def _get_block(self, lines: list[Line], start: int, parent_indent: int) -> tuple[list[Line], int]:
        """Extract an indented block starting at `start` with indent > parent_indent."""
        block = []
        i = start
        while i < len(lines) and lines[i].indent > parent_indent:
            block.append(lines[i])
            i += 1
        return block, i

    def _execute_block(self, lines: list[Line]):
        """Execute a sequence of lines."""
        i = 0
        while i < len(lines):
            line = lines[i]
            text = line.text
            indent = line.indent
            ln = line.line_num

            # ── teach trick (function definition) ──
            if text.startswith("teach trick "):
                i = self._handle_function_def(text, lines, i, indent, ln)
                continue

            # ── bark (print) ──
            if text.startswith("bark "):
                val = self._evaluate(text[5:], ln)
                self.output_fn(str(val), "bark")
                i += 1
                continue

            # ── growl (throw error) ──
            if text.startswith("growl "):
                msg = self._evaluate(text[6:], ln)
                raise CharlotteError(f"GRRR: {msg}", ln)

            # ── rollover (return) ──
            if text.startswith("rollover "):
                val = self._evaluate(text[9:], ln)
                raise CharlotteReturn(val)
            if text == "rollover":
                raise CharlotteReturn(None)

            # ── shake off (break) ──
            if text == "shake off":
                raise CharlotteBreak()

            # ── zoomies N times: (for-loop) ──
            if text.startswith("zoomies ") and text.endswith(" times:"):
                i = self._handle_for_loop(text, lines, i, indent, ln)
                continue

            # ── zoomies through: (for-each) ──
            if text.startswith("zoomies through ") and text.endswith(":"):
                i = self._handle_foreach(text, lines, i, indent, ln)
                continue

            # ── zoomies while: (while-loop) ──
            if text.startswith("zoomies while ") and text.endswith(":"):
                i = self._handle_while(text, lines, i, indent, ln)
                continue

            # ── sniff (conditional) ──
            if text.startswith("sniff ") and text.endswith(":"):
                i = self._handle_conditional(text, lines, i, indent, ln)
                continue

            # ── fetch (variable creation) ──
            if text.startswith("fetch "):
                i = self._handle_fetch(text, i, ln)
                continue

            # ── reassignment: name = expr ──
            if "=" in text and not text.startswith("fetch "):
                parts = text.split("=", 1)
                name = parts[0].strip()
                if name.isidentifier() and name in self.variables:
                    self.variables[name] = self._evaluate(parts[1].strip(), ln)
                    i += 1
                    continue

            # ── .give() (append) ──
            if ".give(" in text and text.endswith(")"):
                dot_pos = text.index(".give(")
                arr_name = text[:dot_pos]
                val_expr = text[dot_pos + 6:-1]
                if arr_name in self.variables and isinstance(self.variables[arr_name], list):
                    self.variables[arr_name].append(self._evaluate(val_expr, ln))
                    i += 1
                    continue

            # ── function call ──
            if "(" in text and text.endswith(")"):
                paren_pos = text.index("(")
                fname = text[:paren_pos]
                if fname in self.functions:
                    self._call_function(fname, text[paren_pos + 1:-1], ln)
                    i += 1
                    continue

            raise CharlotteError(
                f"*suspicious head tilt* Charlotte doesn't understand: \"{text}\"", ln
            )

    # ── Statement handlers ──

    def _handle_function_def(self, text, lines, i, indent, ln):
        import re
        match = re.match(r"^teach trick (\w+)\((.*?)\):$", text)
        if not match:
            raise CharlotteError("*confused head tilt* — Use: teach trick name(args):", ln)
        fname = match.group(1)
        params = [p.strip() for p in match.group(2).split(",") if p.strip()] if match.group(2).strip() else []
        block, next_idx = self._get_block(lines, i + 1, indent)
        if not block:
            raise CharlotteError("This trick has no steps! Indent the body.", ln)
        self.functions[fname] = {"params": params, "body": block}
        return next_idx

    def _handle_fetch(self, text, i, ln):
        import re
        match = re.match(r"^fetch (\w+) = (.+)$", text)
        if not match:
            raise CharlotteError("*drops ball* — Use: fetch name = value", ln)
        self.variables[match.group(1)] = self._evaluate(match.group(2), ln)
        return i + 1

    def _handle_for_loop(self, text, lines, i, indent, ln):
        expr = text[8:-7].strip()  # strip "zoomies " and " times:"
        times = int(self._evaluate(expr, ln))
        if times < 0 or times > self.MAX_LOOPS:
            raise CharlotteError(f"Too many zoomies! Max {self.MAX_LOOPS}.", ln)
        block, next_idx = self._get_block(lines, i + 1, indent)
        for z in range(times):
            self.variables["lap"] = z
            try:
                self._execute_block(block)
            except CharlotteBreak:
                break
        return next_idx

    def _handle_foreach(self, text, lines, i, indent, ln):
        arr_expr = text[16:-1].strip()  # strip "zoomies through " and ":"
        arr = self._evaluate(arr_expr, ln)
        if not isinstance(arr, list):
            raise CharlotteError("Can only zoom through a bunny (array)!", ln)
        block, next_idx = self._get_block(lines, i + 1, indent)
        for z, item in enumerate(arr):
            self.variables["lap"] = z
            self.variables["toy"] = item
            try:
                self._execute_block(block)
            except CharlotteBreak:
                break
        return next_idx

    def _handle_while(self, text, lines, i, indent, ln):
        cond_expr = text[14:-1].strip()  # strip "zoomies while " and ":"
        block, next_idx = self._get_block(lines, i + 1, indent)
        safety = 0
        while self._is_truthy(self._evaluate(cond_expr, ln)):
            safety += 1
            if safety > self.MAX_LOOPS:
                raise CharlotteError("Infinite zoomies! Charlotte collapsed.", ln)
            try:
                self._execute_block(block)
            except CharlotteBreak:
                break
        return next_idx

    def _handle_conditional(self, text, lines, i, indent, ln):
        cond_str = text[6:-1].strip()  # strip "sniff " and ":"
        cond_val = self._evaluate(cond_str, ln)
        true_block, after_true = self._get_block(lines, i + 1, indent)

        # Collect elif / else branches
        elifs = []
        else_block = []
        idx = after_true

        while idx < len(lines) and lines[idx].indent == indent:
            t = lines[idx].text
            if t == "else pout:":
                else_block, idx = self._get_block(lines, idx + 1, indent)
                break
            elif t.startswith("else sniff ") and t.endswith(":"):
                elif_cond = t[11:-1].strip()
                elif_block, idx = self._get_block(lines, idx + 1, indent)
                elifs.append((elif_cond, elif_block))
                continue
            else:
                break

        # Execute the matching branch
        if self._is_truthy(cond_val):
            self._execute_block(true_block)
        else:
            executed = False
            for elif_cond, elif_block in elifs:
                if self._is_truthy(self._evaluate(elif_cond, ln)):
                    self._execute_block(elif_block)
                    executed = True
                    break
            if not executed and else_block:
                self._execute_block(else_block)

        return idx

    # ── Function calls ──

    def _call_function(self, name: str, arg_str: str, ln: int):
        fn = self.functions[name]
        args = [self._evaluate(a.strip(), ln) for a in self._parse_args(arg_str)] if arg_str.strip() else []
        saved = self.variables.copy()
        for p, a in zip(fn["params"], args):
            self.variables[p] = a
        try:
            self._execute_block(fn["body"])
        except CharlotteReturn as ret:
            self.variables = saved
            return ret.value
        self.variables = saved
        return None

    def _parse_args(self, arg_str: str) -> list[str]:
        """Split arguments respecting parentheses and brackets."""
        args = []
        depth = 0
        current = ""
        for ch in arg_str:
            if ch in "([":
                depth += 1
            elif ch in ")]":
                depth -= 1
            if ch == "," and depth == 0:
                args.append(current)
                current = ""
                continue
            current += ch
        if current.strip():
            args.append(current)
        return args

    # ── Expression evaluator ──

    def _evaluate(self, expr: str, ln: int):
        expr = expr.strip()

        # String literals
        if (expr.startswith('"') and expr.endswith('"')) or \
           (expr.startswith("'") and expr.endswith("'")):
            return expr[1:-1]

        # f-strings
        if expr.startswith('f"') and expr.endswith('"'):
            import re
            inner = expr[2:-1]
            def replace_expr(m):
                return str(self._evaluate(m.group(1).strip(), ln))
            return re.sub(r"\{([^}]+)\}", replace_expr, inner)

        # Bunny (array) literal
        if expr.startswith("bunny[") and expr.endswith("]"):
            inner = expr[6:-1].strip()
            if not inner:
                return []
            return [self._evaluate(a.strip(), ln) for a in self._parse_args(inner)]

        # Boolean / null literals
        if expr == "loyal":
            return True
        if expr == "stranger":
            return False
        if expr == "napping":
            return None

        # Numeric literals
        try:
            if "." in expr:
                return float(expr)
            return int(expr)
        except ValueError:
            pass

        # Parenthesized expression
        if expr.startswith("(") and expr.endswith(")"):
            return self._evaluate(expr[1:-1], ln)

        # Bunny indexing: name[idx]
        if "[" in expr and expr.endswith("]") and not expr.startswith("bunny["):
            bracket_pos = expr.index("[")
            name = expr[:bracket_pos]
            if name in self.variables:
                idx = self._evaluate(expr[bracket_pos + 1:-1], ln)
                arr = self.variables[name]
                if isinstance(arr, list):
                    return arr[int(idx)]

        # .toys (length)
        if expr.endswith(".toys"):
            name = expr[:-5]
            if name in self.variables:
                val = self.variables[name]
                if isinstance(val, (list, str)):
                    return len(val)
            return 0

        # Logical NOT
        if expr.startswith("not "):
            return not self._is_truthy(self._evaluate(expr[4:], ln))

        # Logical AND / OR (scan left to right, respecting parens)
        for op, handler in [(" and ", "and"), (" or ", "or")]:
            idx = self._find_operator(expr, op)
            if idx != -1:
                left = self._evaluate(expr[:idx], ln)
                if handler == "and":
                    return self._evaluate(expr[idx + len(op):], ln) if self._is_truthy(left) else left
                else:
                    return left if self._is_truthy(left) else self._evaluate(expr[idx + len(op):], ln)

        # String concatenation ~
        if " ~ " in expr:
            parts = expr.split(" ~ ")
            return "".join(str(self._evaluate(p.strip(), ln)) for p in parts)

        # Comparisons
        comparisons = [
            (" is bigger than ", lambda a, b: a > b),
            (" is smaller than ", lambda a, b: a < b),
            (" >= ", lambda a, b: a >= b),
            (" <= ", lambda a, b: a <= b),
            (" not equals ", lambda a, b: a != b),
            (" equals ", lambda a, b: a == b),
            (" != ", lambda a, b: a != b),
            (" == ", lambda a, b: a == b),
            (" in ", lambda a, b: a in b if isinstance(b, list) else str(a) in str(b)),
        ]
        for op_str, op_fn in comparisons:
            idx = expr.find(op_str)
            if idx != -1:
                left = self._evaluate(expr[:idx], ln)
                right = self._evaluate(expr[idx + len(op_str):], ln)
                return op_fn(left, right)

        # Arithmetic: + - (scan right to left for correct precedence)
        for op in (" + ", " - "):
            idx = expr.rfind(op)
            if idx > 0:
                left = self._evaluate(expr[:idx], ln)
                right = self._evaluate(expr[idx + len(op):], ln)
                if op == " + ":
                    if isinstance(left, str) or isinstance(right, str):
                        return str(left) + str(right)
                    return left + right
                return left - right

        # Arithmetic: * / // %
        for op in (" // ", " / ", " * ", " % "):
            idx = expr.rfind(op)
            if idx > 0:
                left = self._evaluate(expr[:idx], ln)
                right = self._evaluate(expr[idx + len(op):], ln)
                if op in (" / ", " // ") and right == 0:
                    raise CharlotteError("Can't divide by zero — stranger danger!", ln)
                if op == " // ":
                    return left // right
                if op == " * ":
                    return left * right
                if op == " % ":
                    return left % right
                return left / right

        # Built-in functions
        if expr.startswith("howBig(") and expr.endswith(")"):
            val = self._evaluate(expr[7:-1], ln)
            return len(val) if isinstance(val, (list, str)) else len(str(val))

        if expr.startswith("treat(") and expr.endswith(")"):
            return float(self._evaluate(expr[6:-1], ln))

        if expr.startswith("yap(") and expr.endswith(")"):
            return str(self._evaluate(expr[4:-1], ln))

        # User function call
        if "(" in expr and expr.endswith(")"):
            paren_pos = expr.index("(")
            fname = expr[:paren_pos]
            if fname in self.functions:
                return self._call_function(fname, expr[paren_pos + 1:-1], ln)

        # Variable lookup
        if expr in self.variables:
            return self.variables[expr]

        raise CharlotteError(
            f"*sniffs suspiciously* Who is \"{expr}\"? Charlotte doesn't know this stranger!", ln
        )

    def _find_operator(self, expr: str, op: str) -> int:
        """Find operator position respecting parentheses/brackets."""
        depth = 0
        for i in range(len(expr) - len(op) + 1):
            if expr[i] in "([":
                depth += 1
            elif expr[i] in ")]":
                depth -= 1
            if depth == 0 and expr[i:i + len(op)] == op:
                return i
        return -1

    def _is_truthy(self, val) -> bool:
        if val is None or val is False or val == 0 or val == "" or val == "stranger":
            return False
        if isinstance(val, list) and len(val) == 0:
            return False
        return True


# ─── REPL ──────────────────────────────────────────────────

def run_repl():
    """Interactive CharlotteLang REPL."""
    print("🐕 CharlotteLang v2.0 REPL")
    print("   Type Charlotte code below. Commands:")
    print("   .run      — execute the buffer")
    print("   .clear    — clear the buffer")
    print("   .show     — show the buffer")
    print("   .exit     — leave the REPL")
    print("   .help     — show quick reference")
    print()

    interp = Interpreter()
    buffer = []

    while True:
        try:
            prompt = "🐾 " if not buffer else ".. "
            line = input(prompt)
        except (EOFError, KeyboardInterrupt):
            print("\n🐕 Bye bye! *tail wag*")
            break

        if line.strip() == ".exit":
            print("🐕 Bye bye! *tail wag*")
            break
        elif line.strip() == ".clear":
            buffer = []
            print("🐾 Buffer cleared!")
            continue
        elif line.strip() == ".show":
            if buffer:
                print("─── buffer ───")
                for b in buffer:
                    print(f"  {b}")
                print("──────────────")
            else:
                print("🐾 Buffer is empty")
            continue
        elif line.strip() == ".run":
            if buffer:
                source = "\n".join(buffer)
                interp.run(source)
                buffer = []
            else:
                print("🐾 Nothing to run!")
            continue
        elif line.strip() == ".help":
            print_quick_ref()
            continue
        else:
            buffer.append(line)
            # Auto-run single expressions that don't start blocks
            stripped = line.strip()
            if (stripped and
                not stripped.endswith(":") and
                not buffer[-1].startswith(" ") and
                len(buffer) == 1):
                interp.run(stripped)
                buffer = []


def print_quick_ref():
    """Print the CharlotteLang quick reference."""
    print("""
┌─────────────────────────────────────────────────────┐
│  🐕 CharlotteLang Quick Reference                   │
├─────────────────────────────────────────────────────┤
│  bark "hello"          → print                      │
│  fetch x = 10          → create variable             │
│  x = 20                → reassign variable           │
│  growl "error!"        → throw error                 │
│                                                      │
│  sniff x is bigger than 5:                           │
│    bark "big!"                                       │
│  else sniff x equals 5:                              │
│    bark "five!"                                      │
│  else pout:                                          │
│    bark "small"                                      │
│                                                      │
│  zoomies 5 times:      → for loop (lap = index)     │
│    bark f"lap {{lap}}"                               │
│                                                      │
│  zoomies through toys: → foreach (toy=item, lap=idx) │
│    bark toy                                          │
│                                                      │
│  zoomies while x > 0:  → while loop                 │
│    x = x - 1                                        │
│                                                      │
│  teach trick greet(who):                             │
│    bark f"hi {{who}}"                                │
│    rollover "done"     → return                      │
│                                                      │
│  shake off             → break                       │
│  bunny[1, 2, 3]        → array literal               │
│  list.toys             → length                      │
│  list.give("item")     → append                      │
│  loyal / stranger      → true / false                │
│  napping               → null/None                   │
│  sniff this is ignored → comment                     │
│  a ~ b                 → string concat               │
│  and / or / not / in   → logical ops                 │
│  + - * / // %          → arithmetic                  │
└─────────────────────────────────────────────────────┘
""")


# ─── CLI ENTRY POINT ───────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("🐕 CharlotteLang v2.0")
        print()
        print("Usage:")
        print("  charlotte run <file.bark>   Run a .bark file")
        print("  charlotte repl              Start interactive REPL")
        print("  charlotte help              Show quick reference")
        print()
        print("Examples:")
        print("  charlotte run hello.bark")
        print("  charlotte repl")
        sys.exit(0)

    command = sys.argv[1].lower()

    if command == "run":
        if len(sys.argv) < 3:
            print("🐾 *confused head tilt* Which file should Charlotte run?")
            print("Usage: charlotte run <file.bark>")
            sys.exit(1)
        filepath = sys.argv[2]
        if not os.path.exists(filepath):
            print(f"🐾 *sniffs around* Charlotte can't find \"{filepath}\"!")
            sys.exit(1)
        with open(filepath, "r") as f:
            source = f.read()
        interp = Interpreter()
        interp.run(source)

    elif command == "repl":
        run_repl()

    elif command == "help":
        print_quick_ref()

    else:
        print(f"🐾 *suspicious head tilt* Charlotte doesn't know the command \"{command}\"")
        print("Try: charlotte run <file.bark>  or  charlotte repl")
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
CharlotteLang Interpreter v4.4
A Pythonic programming language with chihuahua soul and pitbull energy.

Usage:
    charlotte run <file.bark>
    charlotte repl
    charlotte --help
"""

import sys
import os
import re
import random
import time
import copy
import json
import math
import urllib.request
import urllib.error
import urllib.parse
import http.server
import threading
try:
    import readline  # noqa: F401 — enables up-arrow history in REPL
except ImportError:
    pass


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


class CharlotteContinue(Exception):
    """Used internally to handle keep going (continue) statements."""
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
        # Dedicated comment prefix: "woof" is always a comment regardless of content
        if trimmed == "woof" or trimmed.startswith("woof ") or trimmed.startswith("woof\t"):
            continue
        # Legacy comment: bare "sniff" lines without a trailing colon
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

    # Substrings that mark an env var name as sensitive (case-insensitive).
    # Access to any matching name is blocked unless it appears in env_allowlist.
    _ENV_SENSITIVE_PATTERNS: tuple = (
        "SECRET", "PASSWORD", "PASSWD", "TOKEN", "API_KEY", "APIKEY",
        "PRIVATE_KEY", "PRIVATEKEY", "ACCESS_KEY", "ACCESSKEY",
        "AUTH_KEY", "AUTHKEY", "CREDENTIAL", "PRIVATE",
    )

    MAX_HTTP_TIMEOUT = 30
    MAX_HTTP_RESPONSE = 10 * 1024 * 1024  # 10 MB

    def __init__(self, output_fn=None, env_allowlist=None, url_allowlist=None,
                 http_timeout=10):
        """
        output_fn: optional callable(text, kind) for all output.
        env_allowlist: optional collection of env var names that sniff_env may read.
            - None (default): all non-sensitive vars are readable; vars matching
              _ENV_SENSITIVE_PATTERNS are blocked.
            - A set/list: ONLY the listed names are readable; everything else
              (including non-sensitive vars) is blocked.
        url_allowlist: optional collection of allowed URL host patterns for HTTP.
            - None (default): any http/https URL is allowed.
            - A set/list: ONLY URLs whose host matches an entry are allowed.
              e.g. {"api.example.com", "localhost"}
        http_timeout: default timeout in seconds for HTTP requests (max 30).
        """
        self.variables: dict = {}
        self.functions: dict = {}
        def _default_output(text, kind="bark"):
            if kind == "howl":
                print(text, file=sys.stderr)
            else:
                print(text)
        self.output_fn = output_fn or _default_output
        self._imported_files: set = set()
        self._source_dir: str = os.getcwd()
        # None → use default blocklist; a frozenset → strict allowlist
        self._env_allowlist: frozenset | None = (
            frozenset(env_allowlist) if env_allowlist is not None else None
        )
        self._url_allowlist: frozenset | None = (
            frozenset(url_allowlist) if url_allowlist is not None else None
        )
        self._http_timeout: int = min(int(http_timeout), self.MAX_HTTP_TIMEOUT)
        # HTTP server state
        self._routes: list = []
        self._server: http.server.HTTPServer | None = None
        self._server_thread: threading.Thread | None = None
        self._server_shutdown: threading.Event = threading.Event()
        self._handler_lock: threading.Lock = threading.Lock()

    def _env_var_permitted(self, name: str) -> bool:
        """Return True if sniff_env is allowed to read this env var name."""
        if self._env_allowlist is not None:
            return name in self._env_allowlist
        # Default mode: block names that look like secrets
        upper = name.upper()
        return not any(pattern in upper for pattern in self._ENV_SENSITIVE_PATTERNS)

    def _validate_url(self, url: str, ln: int):
        """Validate a URL for HTTP requests: scheme and optional host allowlist."""
        try:
            parsed = urllib.parse.urlparse(url)
        except Exception:
            raise CharlotteError(f"*confused sniff* That doesn't look like a URL: \"{url}\"", ln)
        if parsed.scheme not in ("http", "https"):
            raise CharlotteError(
                f"*protective growl* Only http:// and https:// URLs are allowed, "
                f"not \"{parsed.scheme}://\"!", ln
            )
        if not parsed.hostname:
            raise CharlotteError(f"*confused sniff* URL has no host: \"{url}\"", ln)
        if self._url_allowlist is not None and parsed.hostname not in self._url_allowlist:
            raise CharlotteError(
                f"*protective growl* Host \"{parsed.hostname}\" is not on the "
                f"allowed list!", ln
            )

    def _http_request(self, url: str, method: str, data=None, headers=None, ln: int = 0):
        """Perform an HTTP request and return a collar (dict) with status, body, headers."""
        self._validate_url(url, ln)
        req_headers = {"User-Agent": "CharlotteLang/4.4"}
        if headers and isinstance(headers, dict):
            req_headers.update({str(k): str(v) for k, v in headers.items()})
        body_bytes = None
        if data is not None:
            if isinstance(data, (dict, list)):
                body_bytes = json.dumps(self._to_json_compatible(data)).encode("utf-8")
            else:
                body_bytes = str(data).encode("utf-8")
            if "Content-Type" not in req_headers:
                req_headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=body_bytes, headers=req_headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self._http_timeout) as resp:
                raw = resp.read(self.MAX_HTTP_RESPONSE)
                charset = resp.headers.get_content_charset() or "utf-8"
                return {
                    "status": resp.status,
                    "body": raw.decode(charset, errors="replace"),
                    "headers": dict(resp.headers.items()),
                }
        except urllib.error.HTTPError as e:
            raw = e.read(self.MAX_HTTP_RESPONSE) if e.fp else b""
            charset = e.headers.get_content_charset() or "utf-8" if e.headers else "utf-8"
            return {
                "status": e.code,
                "body": raw.decode(charset, errors="replace"),
                "headers": dict(e.headers.items()) if e.headers else {},
            }
        except urllib.error.URLError as e:
            raise CharlotteError(f"*whimpers* Could not reach \"{url}\": {e.reason}", ln)
        except Exception as e:
            raise CharlotteError(f"*whimpers* HTTP request failed: {e}", ln)

    def run(self, source: str, source_path: str = None):
        """Run a CharlotteLang program from source string, resetting all state first."""
        self.variables = {}
        self.functions = {}
        self._imported_files = set()
        # Stop any previously running server
        if self._server:
            self._server.shutdown()
            self._server = None
            self._server_thread = None
        self._routes = []
        self._server_shutdown = threading.Event()
        if source_path:
            self._source_dir = os.path.dirname(os.path.abspath(source_path))
        self.execute(source)

    def execute(self, source: str):
        """Execute CharlotteLang source without resetting state (used by REPL)."""
        lines = parse_lines(source)
        try:
            self._execute_block(lines)
        except CharlotteReturn:
            pass  # Top-level rollover is fine
        except CharlotteBreak:
            pass  # Top-level shake off is fine
        except CharlotteContinue:
            pass  # Top-level keep going is fine
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

            # ── snag (import) ──
            if text.startswith("snag "):
                i = self._handle_import(text, i, ln)
                continue

            # ── teach trick (function definition) ──
            if text.startswith("teach trick "):
                i = self._handle_function_def(text, lines, i, indent, ln)
                continue

            # ── bark (print) ──
            if text == "bark":
                self.output_fn("", "bark")
                i += 1
                continue
            if text.startswith("bark "):
                val = self._evaluate(text[5:], ln)
                self.output_fn(str(val), "bark")
                i += 1
                continue

            # ── howl (print to stderr) ──
            if text == "howl":
                self.output_fn("", "howl")
                i += 1
                continue
            if text.startswith("howl "):
                val = self._evaluate(text[5:], ln)
                self.output_fn(str(val), "howl")
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

            # ── keep going (continue) ──
            if text == "keep going":
                raise CharlotteContinue()

            # ── careful: / oops: (try/catch) ──
            if text == "careful:":
                i = self._handle_try_catch(lines, i, indent, ln)
                continue

            # ── zoomies N times: (for-loop) ──
            if text.startswith("zoomies ") and text.endswith(" times:"):
                i = self._handle_for_loop(text, lines, i, indent, ln)
                continue

            # ── zoomies through: (for-each) ──
            if text.startswith("zoomies through ") and text.endswith(":"):
                i = self._handle_foreach(text, lines, i, indent, ln)
                continue

            # ── zoomies VAR through: (named for-each with custom loop variable) ──
            if re.match(r"^zoomies \w+ through .+:$", text):
                i = self._handle_foreach_named(text, lines, i, indent, ln)
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
                if re.match(r"^fetch \w+(?:\s*,\s*\w+)+ =", text):
                    i = self._handle_fetch_destructure(text, i, ln)
                else:
                    i = self._handle_fetch(text, i, ln)
                continue

            # ── reassignment: name = expr ──  (supports dict key assignment: name[key] = expr)
            if "=" in text and not text.startswith("fetch "):
                parts = text.split("=", 1)
                target = parts[0].strip()
                # Dict/list key assignment: name[key] = value
                if "[" in target and target.endswith("]"):
                    bracket_pos = target.index("[")
                    var_name = target[:bracket_pos]
                    key_expr = target[bracket_pos + 1:-1]
                    if var_name in self.variables:
                        container = self.variables[var_name]
                        key = self._evaluate(key_expr, ln)
                        val = self._evaluate(parts[1].strip(), ln)
                        if isinstance(container, dict):
                            container[key] = val
                        elif isinstance(container, list):
                            try:
                                idx = int(key)
                            except (ValueError, TypeError):
                                raise CharlotteError(
                                    f"*confused sniff* List index must be a number, got: {key!r}", ln)
                            try:
                                container[idx] = val
                            except IndexError:
                                raise CharlotteError(
                                    f"*paws at empty bunny* Can't assign to index {idx}! "
                                    f"List has {len(container)} items.", ln)
                        i += 1
                        continue
                if target.isidentifier() and target in self.variables:
                    self.variables[target] = self._evaluate(parts[1].strip(), ln)
                    i += 1
                    continue
                if target.isidentifier() and target not in self.variables and not parts[1].startswith("="):
                    raise CharlotteError(
                        f"*confused sniff* \"{target}\" hasn't been fetched yet! "
                        f"Use: fetch {target} = ...", ln
                    )

            # ── .give() (append) ──
            if ".give(" in text and text.endswith(")"):
                dot_pos = text.index(".give(")
                arr_name = text[:dot_pos]
                val_expr = text[dot_pos + 6:-1]
                if arr_name in self.variables and isinstance(self.variables[arr_name], list):
                    self.variables[arr_name].append(self._evaluate(val_expr, ln))
                    i += 1
                    continue

            # ── .bury() (dict set) ──
            if ".bury(" in text and text.endswith(")"):
                dot_pos = text.index(".bury(")
                dict_name = text[:dot_pos]
                args_str = text[dot_pos + 6:-1]
                if dict_name in self.variables and isinstance(self.variables[dict_name], dict):
                    args = self._parse_args(args_str)
                    if len(args) == 2:
                        key = self._evaluate(args[0].strip(), ln)
                        val = self._evaluate(args[1].strip(), ln)
                        self.variables[dict_name][key] = val
                        i += 1
                        continue

            # ── .dig() (dict delete) ──
            if ".dig(" in text and text.endswith(")"):
                dot_pos = text.index(".dig(")
                dict_name = text[:dot_pos]
                key_expr = text[dot_pos + 5:-1]
                if dict_name in self.variables and isinstance(self.variables[dict_name], dict):
                    key = self._evaluate(key_expr, ln)
                    self.variables[dict_name].pop(key, None)
                    i += 1
                    continue

            # ── .sort() (list sort in-place) ──
            if text.endswith(".sort()"):
                name = text[:-7]
                if name in self.variables and isinstance(self.variables[name], list):
                    self.variables[name].sort()
                    i += 1
                    continue

            # ── .reverse() (list reverse in-place) ──
            if text.endswith(".reverse()"):
                name = text[:-10]
                if name in self.variables and isinstance(self.variables[name], list):
                    self.variables[name].reverse()
                    i += 1
                    continue

            # ── .remove(val) (remove first occurrence from list) ──
            if ".remove(" in text and text.endswith(")"):
                dot_pos = text.index(".remove(")
                arr_name = text[:dot_pos]
                if arr_name in self.variables and isinstance(self.variables[arr_name], list):
                    val = self._evaluate(text[dot_pos + 8:-1], ln)
                    if val in self.variables[arr_name]:
                        self.variables[arr_name].remove(val)
                    i += 1
                    continue

            # ── .pop() as statement (result discarded) ──
            if ".pop(" in text and text.endswith(")"):
                dot_pos = text.index(".pop(")
                arr_name = text[:dot_pos]
                if arr_name in self.variables and isinstance(self.variables[arr_name], list):
                    self._evaluate(text, ln)
                    i += 1
                    continue

            # ── nap() as a standalone statement ──
            if text.startswith("nap(") and text.endswith(")"):
                self._evaluate(text, ln)
                i += 1
                continue

            # ── mark_file() / append_file() as standalone statements ──
            if (text.startswith("mark_file(") or text.startswith("append_file(")) and text.endswith(")"):
                self._evaluate(text, ln)
                i += 1
                continue

            # ── guard (route handler) ──
            if text.startswith("guard ") and text.endswith(":"):
                i = self._handle_guard(text, lines, i, indent, ln)
                continue

            # ── kennel (start server) ──
            if text.startswith("kennel "):
                self._handle_kennel(text, ln)
                i += 1
                continue

            # ── leave_kennel (stop server) ──
            if text == "leave_kennel":
                self._handle_leave_kennel(ln)
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
        match = re.match(r"^fetch (\w+) = (.+)$", text)
        if not match:
            raise CharlotteError("*drops ball* — Use: fetch name = value", ln)
        self.variables[match.group(1)] = self._evaluate(match.group(2), ln)
        return i + 1

    def _handle_fetch_destructure(self, text, i, ln):
        """Handle destructuring: fetch a, b, c = arr"""
        m = re.match(r"^fetch (\w+(?:\s*,\s*\w+)+) = (.+)$", text)
        if not m:
            raise CharlotteError("*drops ball* — Use: fetch a, b, c = array", ln)
        names = [n.strip() for n in m.group(1).split(",")]
        val = self._evaluate(m.group(2), ln)
        if not isinstance(val, list):
            raise CharlotteError(
                f"*confused sniff* Destructuring needs a bunny[] (array), "
                f"got: {type(val).__name__}", ln
            )
        if len(names) != len(val):
            raise CharlotteError(
                f"*paws at bunny* Destructuring mismatch! "
                f"Expected {len(names)} items, bunny has {len(val)}.", ln
            )
        for name, item in zip(names, val):
            self.variables[name] = item
        return i + 1

    def _handle_for_loop(self, text, lines, i, indent, ln):
        expr = text[8:-7].strip()  # strip "zoomies " and " times:"
        try:
            times = int(self._evaluate(expr, ln))
        except (ValueError, TypeError):
            raise CharlotteError("Zoomies count must be a number! *tilts head*", ln)
        if times < 0:
            raise CharlotteError("Zoomies count can't be negative! *sits and stares*", ln)
        if times > self.MAX_LOOPS:
            raise CharlotteError(f"Too many zoomies! Max {self.MAX_LOOPS}.", ln)
        block, next_idx = self._get_block(lines, i + 1, indent)
        for z in range(times):
            self.variables["lap"] = z
            try:
                self._execute_block(block)
            except CharlotteBreak:
                break
            except CharlotteContinue:
                continue
        return next_idx

    def _handle_foreach(self, text, lines, i, indent, ln):
        arr_expr = text[16:-1].strip()  # strip "zoomies through " and ":"
        arr = self._evaluate(arr_expr, ln)
        # Support iterating through dictionaries
        if isinstance(arr, dict):
            block, next_idx = self._get_block(lines, i + 1, indent)
            for z, key in enumerate(arr):
                self.variables["lap"] = z
                self.variables["toy"] = key
                try:
                    self._execute_block(block)
                except CharlotteBreak:
                    break
                except CharlotteContinue:
                    continue
            return next_idx
        if not isinstance(arr, list):
            raise CharlotteError("Can only zoom through a bunny (array) or collar (dict)!", ln)
        block, next_idx = self._get_block(lines, i + 1, indent)
        for z, item in enumerate(arr):
            self.variables["lap"] = z
            self.variables["toy"] = item
            try:
                self._execute_block(block)
            except CharlotteBreak:
                break
            except CharlotteContinue:
                continue
        return next_idx

    def _handle_foreach_named(self, text, lines, i, indent, ln):
        match = re.match(r"^zoomies (\w+) through (.+):$", text)
        var_name = match.group(1)
        arr_expr = match.group(2).strip()
        arr = self._evaluate(arr_expr, ln)
        if isinstance(arr, dict):
            block, next_idx = self._get_block(lines, i + 1, indent)
            for z, key in enumerate(arr):
                self.variables["lap"] = z
                self.variables[var_name] = key
                try:
                    self._execute_block(block)
                except CharlotteBreak:
                    break
                except CharlotteContinue:
                    continue
            return next_idx
        if not isinstance(arr, list):
            raise CharlotteError("Can only zoom through a bunny (array) or collar (dict)!", ln)
        block, next_idx = self._get_block(lines, i + 1, indent)
        for z, item in enumerate(arr):
            self.variables["lap"] = z
            self.variables[var_name] = item
            try:
                self._execute_block(block)
            except CharlotteBreak:
                break
            except CharlotteContinue:
                continue
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
            except CharlotteContinue:
                continue
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

    def _handle_try_catch(self, lines, i, indent, ln):
        """Handle careful:/oops: (try/catch) blocks."""
        try_block, after_try = self._get_block(lines, i + 1, indent)
        if not try_block:
            raise CharlotteError("careful: block has no body! Indent the body.", ln)

        oops_block = []
        error_var = None
        idx = after_try

        if idx < len(lines) and lines[idx].indent == indent:
            t = lines[idx].text
            # oops error_name: or just oops:
            if t.startswith("oops ") and t.endswith(":"):
                error_var = t[5:-1].strip()
                oops_block, idx = self._get_block(lines, idx + 1, indent)
            elif t == "oops:":
                oops_block, idx = self._get_block(lines, idx + 1, indent)

        try:
            self._execute_block(try_block)
        except (CharlotteReturn, CharlotteBreak, CharlotteContinue):
            raise  # Re-raise control flow exceptions
        except CharlotteError as e:
            if oops_block:
                if error_var:
                    self.variables[error_var] = str(e)
                self._execute_block(oops_block)
        except Exception as e:
            if oops_block:
                if error_var:
                    self.variables[error_var] = str(e)
                self._execute_block(oops_block)

        return idx

    def _resolve_sandboxed_path(self, path: str, ln: int) -> str:
        """Resolve path relative to source_dir and verify it stays within the sandbox."""
        if not isinstance(path, str):
            raise CharlotteError("File path must be a string!", ln)
        if not os.path.isabs(path):
            path = os.path.join(self._source_dir, path)
        path = os.path.realpath(path)
        source_dir = os.path.realpath(self._source_dir)
        allowed_prefix = source_dir.rstrip(os.sep) + os.sep
        if path != source_dir and not path.startswith(allowed_prefix):
            raise CharlotteError(
                "*suspicious growl* File access is restricted to the project "
                "directory — no escaping allowed!", ln
            )
        return path

    def _handle_import(self, text, i, ln):
        """Handle snag (import) statements."""
        path_expr = text[5:].strip()
        # Evaluate the path (could be a string literal)
        path = self._evaluate(path_expr, ln)
        if not isinstance(path, str):
            raise CharlotteError("snag path must be a string!", ln)

        path = self._resolve_sandboxed_path(path, ln)

        # Prevent circular imports
        if path in self._imported_files:
            return i + 1
        self._imported_files.add(path)

        if not os.path.exists(path):
            raise CharlotteError(f"*sniffs around* Can't find \"{path}\" to snag!", ln)

        with open(path, "r") as f:
            source = f.read()

        import_lines = parse_lines(source)
        saved_dir = self._source_dir
        self._source_dir = os.path.dirname(path)
        try:
            self._execute_block(import_lines)
        finally:
            self._source_dir = saved_dir
        return i + 1

    # ── Function calls ──

    def _call_function(self, name: str, arg_str: str, ln: int):
        fn = self.functions[name]
        raw_args = [a.strip() for a in self._parse_args(arg_str)] if arg_str.strip() else []

        # Check if any argument uses named syntax (param: value)
        if any(self._is_named_arg(a) for a in raw_args):
            kwargs = {}
            positional_idx = 0
            for a in raw_args:
                if self._is_named_arg(a):
                    colon_pos = a.index(":")
                    pname = a[:colon_pos].strip()
                    pval_expr = a[colon_pos + 1:].strip()
                    if pname not in fn["params"]:
                        raise CharlotteError(
                            f"*confused bark* {name}() has no parameter \"{pname}\"!", ln
                        )
                    kwargs[pname] = self._evaluate(pval_expr, ln)
                else:
                    if positional_idx >= len(fn["params"]):
                        raise CharlotteError(
                            f"*confused bark* Too many arguments for {name}()!", ln
                        )
                    kwargs[fn["params"][positional_idx]] = self._evaluate(a, ln)
                    positional_idx += 1
            missing = [p for p in fn["params"] if p not in kwargs]
            if missing:
                raise CharlotteError(
                    f"*confused bark* {name}() is missing: {', '.join(missing)}!", ln
                )
        else:
            args = [self._evaluate(a, ln) for a in raw_args]
            if len(args) != len(fn["params"]):
                raise CharlotteError(
                    f"*confused bark* {name}() expects {len(fn['params'])} "
                    f"argument(s), got {len(args)}!", ln
                )
            kwargs = dict(zip(fn["params"], args))

        saved = copy.deepcopy(self.variables)
        self.variables.update(kwargs)
        result = None
        try:
            self._execute_block(fn["body"])
        except CharlotteReturn as ret:
            result = ret.value
        finally:
            self.variables = saved
        return result

    def _is_named_arg(self, token: str) -> bool:
        """Return True if token looks like 'identifier: value' at the top level."""
        m = re.match(r'^(\w+)\s*:', token.strip())
        if not m:
            return False
        # Verify the colon is at depth 0 (not inside brackets/parens/braces/strings)
        colon_pos = token.index(":")
        depth = 0
        in_string = False
        string_char = None
        for idx, ch in enumerate(token):
            if not in_string and ch in ('"', "'"):
                in_string = True
                string_char = ch
            elif in_string and ch == string_char:
                in_string = False
            if not in_string:
                if ch in "([{":
                    depth += 1
                elif ch in ")]}":
                    depth -= 1
            if idx == colon_pos:
                return depth == 0
        return False

    def _parse_args(self, arg_str: str) -> list[str]:
        """Split arguments respecting parentheses, brackets, braces, and strings."""
        args = []
        depth = 0
        current = ""
        in_string = False
        string_char = None
        escaped = False
        for ch in arg_str:
            if escaped:
                escaped = False
                current += ch
                continue
            if ch == "\\" and in_string:
                escaped = True
                current += ch
                continue
            if not in_string and ch in ('"', "'"):
                in_string = True
                string_char = ch
            elif in_string and ch == string_char:
                in_string = False
            if not in_string:
                if ch in "([{":
                    depth += 1
                elif ch in ")]}":
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

    def _process_escapes(self, s: str) -> str:
        """Process escape sequences in string literals."""
        escape_map = {
            'n': '\n', 't': '\t', 'r': '\r', '\\': '\\',
            '"': '"', "'": "'", '0': '\0', 'b': '\b', 'f': '\f',
        }
        result = []
        i = 0
        while i < len(s):
            if s[i] == '\\' and i + 1 < len(s):
                result.append(escape_map.get(s[i + 1], '\\' + s[i + 1]))
                i += 2
            else:
                result.append(s[i])
                i += 1
        return ''.join(result)

    def _is_complete_string(self, expr: str) -> bool:
        """Check if expr is a single complete string literal (not two strings joined by an op)."""
        if len(expr) < 2:
            return False
        q = expr[0]
        if q not in ('"', "'"):
            return False
        i = 1
        while i < len(expr):
            if expr[i] == '\\':
                i += 2
                continue
            if expr[i] == q:
                return i == len(expr) - 1
            i += 1
        return False

    def _count_preceding_backslashes(self, s: str, pos: int) -> int:
        """Count consecutive backslashes immediately before position pos."""
        count = 0
        pos -= 1
        while pos >= 0 and s[pos] == '\\':
            count += 1
            pos -= 1
        return count

    def _rfind_operator(self, expr: str, op: str) -> int:
        """Find rightmost operator position respecting parentheses/brackets/braces/strings."""
        depth = 0
        in_string = False
        string_char = None
        result = -1
        for i in range(len(expr) - len(op) + 1):
            ch = expr[i]
            if not in_string and ch in ('"', "'"):
                in_string = True
                string_char = ch
            elif in_string and ch == string_char and self._count_preceding_backslashes(expr, i) % 2 == 0:
                in_string = False
            if not in_string:
                if ch in "([{":
                    depth += 1
                elif ch in ")]}":
                    depth -= 1
                if depth == 0 and expr[i:i + len(op)] == op:
                    result = i
        return result

    def _evaluate(self, expr: str, ln: int):
        expr = expr.strip()

        # String literals — must be a single complete string, not "a" + "b"
        if self._is_complete_string(expr):
            return self._process_escapes(expr[1:-1])

        # f-strings: f"..." or f'...'
        if (expr.startswith('f"') and expr.endswith('"')) or (expr.startswith("f'") and expr.endswith("'")):
            inner = expr[2:-1]
            result = []
            i = 0
            while i < len(inner):
                ch = inner[i]
                if ch == '{' and i + 1 < len(inner) and inner[i + 1] == '{':
                    result.append('{')
                    i += 2
                elif ch == '}' and i + 1 < len(inner) and inner[i + 1] == '}':
                    result.append('}')
                    i += 2
                elif ch == '{':
                    i += 1
                    depth = 1
                    expr_chars = []
                    in_str = None
                    while i < len(inner) and depth > 0:
                        c = inner[i]
                        if in_str:
                            if c == '\\' and i + 1 < len(inner):
                                expr_chars.append(c)
                                expr_chars.append(inner[i + 1])
                                i += 2
                                continue
                            if c == in_str:
                                in_str = None
                        elif c in ('"', "'"):
                            in_str = c
                        elif c == '{':
                            depth += 1
                        elif c == '}':
                            depth -= 1
                            if depth == 0:
                                break
                        expr_chars.append(c)
                        i += 1
                    i += 1  # skip closing }
                    val = self._evaluate(self._process_escapes(''.join(expr_chars).strip()), ln)
                    result.append(str(val))
                elif ch == '\\' and i + 1 < len(inner):
                    escape_map = {'n': '\n', 't': '\t', 'r': '\r', '\\': '\\',
                                  '"': '"', "'": "'", '0': '\0', 'b': '\b', 'f': '\f'}
                    result.append(escape_map.get(inner[i + 1], '\\' + inner[i + 1]))
                    i += 2
                else:
                    result.append(ch)
                    i += 1
            return ''.join(result)

        # Bunny (array) literal
        if expr.startswith("bunny[") and expr.endswith("]"):
            inner = expr[6:-1].strip()
            if not inner:
                return []
            return [self._evaluate(a.strip(), ln) for a in self._parse_args(inner)]

        # Collar (dictionary) literal
        if expr.startswith("collar{") and expr.endswith("}"):
            inner = expr[7:-1].strip()
            if not inner:
                return {}
            result = {}
            pairs = self._parse_args(inner)
            for pair in pairs:
                colon_pos = self._find_operator(pair, ":")
                if colon_pos == -1:
                    raise CharlotteError("collar entries need key: value format!", ln)
                key = self._evaluate(pair[:colon_pos].strip(), ln)
                val = self._evaluate(pair[colon_pos + 1:].strip(), ln)
                result[key] = val
            return result

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

        # Parenthesized expression — only strip if the opening ( matches the closing )
        if expr.startswith("(") and expr.endswith(")"):
            depth = 0
            matches_end = True
            for _i, _ch in enumerate(expr):
                if _ch == "(":
                    depth += 1
                elif _ch == ")":
                    depth -= 1
                if depth == 0 and _i < len(expr) - 1:
                    matches_end = False
                    break
            if matches_end:
                return self._evaluate(expr[1:-1], ln)

        # Indexing and slicing: expr[idx], expr[start:stop], expr[start:stop:step]
        # Supports chained access like arr[0][1] by finding the last top-level [...].
        # We skip this block if there are top-level binary operators in the expression
        # (e.g. arr[0] + arr[1]) — those are handled by the arithmetic handlers below.
        if "[" in expr and expr.endswith("]") and not expr.startswith("bunny[") and not expr.startswith("collar{"):
            # Skip if top-level binary operators are present (let arithmetic/comparison
            # handlers split the expression first)
            _has_top_level_op = False
            for _test_op in (" + ", " - ", " * ", " / ", " // ", " ** ",
                             " and ", " or ", " ~ ", " == ", " != ",
                             " >= ", " <= ", " > ", " < ",
                             " equals ", " not equals ",
                             " is bigger than ", " is smaller than ",
                             " in ", " not in "):
                if self._find_operator(expr, _test_op) != -1:
                    _has_top_level_op = True
                    break
            # Find the last top-level [ whose matching ] is the final char.
            last_bracket_pos = -1
            if not _has_top_level_op:
                _depth = 0
                _in_str = False
                _str_ch = None
                for _i, _ch in enumerate(expr):
                    if not _in_str and _ch in ('"', "'"):
                        _in_str = True
                        _str_ch = _ch
                    elif _in_str and _ch == _str_ch and self._count_preceding_backslashes(expr, _i) % 2 == 0:
                        _in_str = False
                    if not _in_str:
                        if _ch == '[':
                            if _depth == 0:
                                last_bracket_pos = _i
                            _depth += 1
                        elif _ch == ']':
                            _depth -= 1
            if last_bracket_pos > 0:
                base_expr = expr[:last_bracket_pos]
                key_expr = expr[last_bracket_pos + 1:-1]
                container = self._evaluate(base_expr, ln)
                if ":" in key_expr:
                    parts = key_expr.split(":", 2)
                    start = int(self._evaluate(parts[0].strip(), ln)) if parts[0].strip() else None
                    stop = int(self._evaluate(parts[1].strip(), ln)) if parts[1].strip() else None
                    step = int(self._evaluate(parts[2].strip(), ln)) if len(parts) > 2 and parts[2].strip() else None
                    if isinstance(container, (list, str)):
                        return container[start:stop:step]
                    raise CharlotteError("Can only slice a bunny (array) or string!", ln)
                key = self._evaluate(key_expr, ln)
                if isinstance(container, list):
                    try:
                        return container[int(key)]
                    except IndexError:
                        raise CharlotteError(
                            f"*paws at empty bunny* Index {int(key)} is out of bounds! "
                            f"List has {len(container)} items.", ln)
                    except (ValueError, TypeError):
                        raise CharlotteError(
                            f"*confused sniff* List index must be a number, got: {key!r}", ln)
                if isinstance(container, str):
                    try:
                        return container[int(key)]
                    except IndexError:
                        raise CharlotteError(
                            f"*paws at string* Index {int(key)} is out of bounds! "
                            f"String has {len(container)} characters.", ln)
                    except (ValueError, TypeError):
                        raise CharlotteError(
                            f"*confused sniff* String index must be a number, got: {key!r}", ln)
                if isinstance(container, dict):
                    if key not in container:
                        raise CharlotteError(f"*digs around* Key \"{key}\" not found in collar!", ln)
                    return container[key]

        # .toys (length) — works for lists, strings, and dicts
        if expr.endswith(".toys"):
            val = self._evaluate(expr[:-5], ln)
            if isinstance(val, (list, str, dict)):
                return len(val)
            return 0

        # .keys — get dict keys as a list
        if expr.endswith(".keys"):
            val = self._evaluate(expr[:-5], ln)
            if isinstance(val, dict):
                return list(val.keys())

        # .values — get dict values as a list
        if expr.endswith(".values"):
            val = self._evaluate(expr[:-7], ln)
            if isinstance(val, dict):
                return list(val.values())

        # String methods
        # .chew(sep) — split string
        if ".chew(" in expr and expr.endswith(")"):
            dot_pos = expr.index(".chew(")
            val = self._evaluate(expr[:dot_pos], ln)
            sep_expr = expr[dot_pos + 6:-1]
            if isinstance(val, str):
                sep = self._evaluate(sep_expr, ln) if sep_expr.strip() else None
                return val.split(sep)

        # .trim() — strip whitespace
        if expr.endswith(".trim()"):
            val = self._evaluate(expr[:-7], ln)
            if isinstance(val, str):
                return val.strip()

        # .upper() — uppercase
        if expr.endswith(".upper()"):
            val = self._evaluate(expr[:-8], ln)
            if isinstance(val, str):
                return val.upper()

        # .lower() — lowercase
        if expr.endswith(".lower()"):
            val = self._evaluate(expr[:-8], ln)
            if isinstance(val, str):
                return val.lower()

        # .replace(old, new) — replace all occurrences in a string
        if ".replace(" in expr and expr.endswith(")"):
            dot_pos = expr.index(".replace(")
            val = self._evaluate(expr[:dot_pos], ln)
            if isinstance(val, str):
                args = self._parse_args(expr[dot_pos + 9:-1])
                if len(args) == 2:
                    old = self._evaluate(args[0].strip(), ln)
                    new = self._evaluate(args[1].strip(), ln)
                    return val.replace(str(old), str(new))

        # .find(sub) — find index of substring, -1 if not found
        if ".find(" in expr and expr.endswith(")"):
            dot_pos = expr.index(".find(")
            val = self._evaluate(expr[:dot_pos], ln)
            if isinstance(val, str):
                sub = self._evaluate(expr[dot_pos + 6:-1], ln)
                return val.find(str(sub))

        # .startswith(prefix) — check if string starts with prefix
        if ".startswith(" in expr and expr.endswith(")"):
            dot_pos = expr.index(".startswith(")
            val = self._evaluate(expr[:dot_pos], ln)
            if isinstance(val, str):
                prefix = self._evaluate(expr[dot_pos + 12:-1], ln)
                return val.startswith(str(prefix))

        # .endswith(suffix) — check if string ends with suffix
        if ".endswith(" in expr and expr.endswith(")"):
            dot_pos = expr.index(".endswith(")
            val = self._evaluate(expr[:dot_pos], ln)
            if isinstance(val, str):
                suffix = self._evaluate(expr[dot_pos + 10:-1], ln)
                return val.endswith(str(suffix))

        # .join(sep) — join list elements with a separator string
        if ".join(" in expr and expr.endswith(")"):
            dot_pos = expr.index(".join(")
            val = self._evaluate(expr[:dot_pos], ln)
            if isinstance(val, list):
                sep = self._evaluate(expr[dot_pos + 6:-1], ln)
                return str(sep).join(str(item) for item in val)

        # .index(val) — find index of value in list, -1 if not found
        if ".index(" in expr and expr.endswith(")"):
            dot_pos = expr.index(".index(")
            val = self._evaluate(expr[:dot_pos], ln)
            if isinstance(val, list):
                search = self._evaluate(expr[dot_pos + 7:-1], ln)
                try:
                    return val.index(search)
                except ValueError:
                    return -1

        # .pop() / .pop(idx) — remove and return element from list
        if ".pop(" in expr and expr.endswith(")"):
            dot_pos = expr.index(".pop(")
            val = self._evaluate(expr[:dot_pos], ln)
            if isinstance(val, list):
                idx_expr = expr[dot_pos + 5:-1].strip()
                try:
                    if idx_expr:
                        return val.pop(int(self._evaluate(idx_expr, ln)))
                    return val.pop()
                except IndexError:
                    raise CharlotteError("*paws at empty bunny* Can't pop from an empty list!", ln)

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
        idx = self._find_operator(expr, " ~ ")
        if idx != -1:
            parts = []
            while idx != -1:
                parts.append(expr[:idx])
                expr = expr[idx + 3:]
                idx = self._find_operator(expr, " ~ ")
            parts.append(expr)
            return "".join(str(self._evaluate(p.strip(), ln)) for p in parts)

        # Comparisons — longer forms checked before shorter to avoid partial matches
        comparisons = [
            (" is bigger than ", lambda a, b: a > b),
            (" is smaller than ", lambda a, b: a < b),
            (" >= ", lambda a, b: a >= b),
            (" <= ", lambda a, b: a <= b),
            (" > ", lambda a, b: a > b),
            (" < ", lambda a, b: a < b),
            (" not equals ", lambda a, b: a != b),
            (" equals ", lambda a, b: a == b),
            (" != ", lambda a, b: a != b),
            (" == ", lambda a, b: a == b),
            (" not in ", lambda a, b: a not in b if isinstance(b, (list, dict)) else str(a) not in str(b)),
            (" in ", lambda a, b: a in b if isinstance(b, (list, dict)) else str(a) in str(b)),
        ]
        for op_str, op_fn in comparisons:
            idx = self._find_operator(expr, op_str)
            if idx != -1:
                left = self._evaluate(expr[:idx], ln)
                right = self._evaluate(expr[idx + len(op_str):], ln)
                return op_fn(left, right)

        # Arithmetic: + - (scan right to left, respecting parens)
        for op in (" + ", " - "):
            idx = self._rfind_operator(expr, op)
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
            idx = self._rfind_operator(expr, op)
            if idx > 0:
                left = self._evaluate(expr[:idx], ln)
                right = self._evaluate(expr[idx + len(op):], ln)
                if op in (" / ", " // ") and right == 0:
                    raise CharlotteError("Can't divide by zero — stranger danger!", ln)
                if op == " // ":
                    return left // right
                if op == " * ":
                    if isinstance(left, str) and isinstance(right, int):
                        return left * right
                    if isinstance(left, int) and isinstance(right, str):
                        return right * left
                    return left * right
                if op == " % ":
                    return left % right
                return left / right

        # Arithmetic: ** (power) — highest arithmetic precedence, right-to-left
        idx = self._find_operator(expr, " ** ")
        if idx != -1:
            left = self._evaluate(expr[:idx], ln)
            right = self._evaluate(expr[idx + 4:], ln)
            return left ** right

        # Built-in functions
        if expr.startswith("howBig(") and expr.endswith(")"):
            val = self._evaluate(expr[7:-1], ln)
            return len(val) if isinstance(val, (list, str, dict)) else len(str(val))

        if expr.startswith("treat(") and expr.endswith(")"):
            try:
                return float(self._evaluate(expr[6:-1], ln))
            except (ValueError, TypeError) as e:
                raise CharlotteError(f"*confused look* treat() couldn't convert that to a float: {e}", ln)

        if expr.startswith("yap(") and expr.endswith(")"):
            return str(self._evaluate(expr[4:-1], ln))

        if expr.startswith("breed(") and expr.endswith(")"):
            val = self._evaluate(expr[6:-1], ln)
            type_map = {
                int: "number", float: "number", str: "string",
                bool: "boolean", list: "bunny", dict: "collar",
            }
            return type_map.get(type(val), "unknown") if val is not None else "napping"

        if expr.startswith("goodBoy(") and expr.endswith(")"):
            try:
                return int(self._evaluate(expr[8:-1], ln))
            except (ValueError, TypeError) as e:
                raise CharlotteError(f"*confused look* goodBoy() couldn't convert that to an integer: {e}", ln)

        # loyal(x) — convert to bool
        if expr.startswith("loyal(") and expr.endswith(")"):
            return self._is_truthy(self._evaluate(expr[6:-1], ln))

        # abs(x) — absolute value
        if expr.startswith("abs(") and expr.endswith(")"):
            return abs(self._evaluate(expr[4:-1], ln))

        # floor(x) — round down to nearest integer
        if expr.startswith("floor(") and expr.endswith(")"):
            return math.floor(self._evaluate(expr[6:-1], ln))

        # ceil(x) — round up to nearest integer
        if expr.startswith("ceil(") and expr.endswith(")"):
            return math.ceil(self._evaluate(expr[5:-1], ln))

        # round(x) / round(x, digits) — round a number
        if expr.startswith("round(") and expr.endswith(")"):
            args = self._parse_args(expr[6:-1])
            val = self._evaluate(args[0].strip(), ln)
            digits = int(self._evaluate(args[1].strip(), ln)) if len(args) > 1 else None
            return round(val, digits)

        # min(a, b, ...) or min(list) — minimum value
        if expr.startswith("min(") and expr.endswith(")"):
            args = self._parse_args(expr[4:-1])
            if len(args) == 1:
                val = self._evaluate(args[0].strip(), ln)
                if isinstance(val, list):
                    return min(val)
            return min(self._evaluate(a.strip(), ln) for a in args)

        # max(a, b, ...) or max(list) — maximum value
        if expr.startswith("max(") and expr.endswith(")"):
            args = self._parse_args(expr[4:-1])
            if len(args) == 1:
                val = self._evaluate(args[0].strip(), ln)
                if isinstance(val, list):
                    return max(val)
            return max(self._evaluate(a.strip(), ln) for a in args)

        # squirrel() — random number; squirrel() → float, squirrel(n) → int 0..n-1, squirrel(a,b) → int a..b
        if expr.startswith("squirrel(") and expr.endswith(")"):
            raw = expr[9:-1].strip()
            if not raw:
                return random.random()
            args = self._parse_args(raw)
            if len(args) == 1:
                return random.randrange(int(self._evaluate(args[0].strip(), ln)))
            a = int(self._evaluate(args[0].strip(), ln))
            b = int(self._evaluate(args[1].strip(), ln))
            return random.randint(a, b)

        # nap(seconds) — sleep
        if expr.startswith("nap(") and expr.endswith(")"):
            time.sleep(float(self._evaluate(expr[4:-1], ln)))
            return None

        # sniff_env(var) — get environment variable, returns napping if not set
        if expr.startswith("sniff_env(") and expr.endswith(")"):
            var = str(self._evaluate(expr[10:-1], ln))
            if not self._env_var_permitted(var):
                raise CharlotteError(
                    f"*protective growl* sniff_env: \"{var}\" is restricted — "
                    f"looks like a secret or is not on the allowed list!", ln
                )
            return os.environ.get(var, None)

        # beg(prompt) — read user input from stdin, returns string
        if expr.startswith("beg(") and expr.endswith(")"):
            prompt_val = self._evaluate(expr[4:-1], ln)
            return input(str(prompt_val))

        # dig_up(url) / dig_up(url, headers) — HTTP GET request
        if expr.startswith("dig_up(") and expr.endswith(")"):
            args = self._parse_args(expr[7:-1])
            if not args:
                raise CharlotteError("dig_up needs a URL!", ln)
            url = str(self._evaluate(args[0].strip(), ln))
            headers = self._evaluate(args[1].strip(), ln) if len(args) > 1 else None
            return self._http_request(url, "GET", headers=headers, ln=ln)

        # bury(url, data) / bury(url, data, headers) — HTTP POST request
        if expr.startswith("bury(") and expr.endswith(")"):
            args = self._parse_args(expr[5:-1])
            if len(args) < 2:
                raise CharlotteError("bury needs a URL and data!", ln)
            url = str(self._evaluate(args[0].strip(), ln))
            data = self._evaluate(args[1].strip(), ln)
            headers = self._evaluate(args[2].strip(), ln) if len(args) > 2 else None
            return self._http_request(url, "POST", data=data, headers=headers, ln=ln)

        # chew_json(string) — parse JSON string into collar/bunny/value
        if expr.startswith("chew_json(") and expr.endswith(")"):
            raw = str(self._evaluate(expr[10:-1], ln))
            try:
                return json.loads(raw)
            except json.JSONDecodeError as e:
                raise CharlotteError(f"*confused chewing* Invalid JSON: {e}", ln)

        # yap_json(value) — serialize collar/bunny/value to JSON string
        if expr.startswith("yap_json(") and expr.endswith(")"):
            val = self._evaluate(expr[9:-1], ln)
            try:
                return json.dumps(self._to_json_compatible(val))
            except (TypeError, ValueError) as e:
                raise CharlotteError(f"*confused yapping* Can't convert to JSON: {e}", ln)

        # sniff_file(path) — read file, returns string or napping on failure
        if expr.startswith("sniff_file(") and expr.endswith(")"):
            path_val = str(self._evaluate(expr[11:-1], ln))
            resolved = self._resolve_sandboxed_path(path_val, ln)
            try:
                with open(resolved, "r", encoding="utf-8", errors="replace") as f:
                    return f.read()
            except OSError:
                return None

        # mark_file(path, data) — write (overwrite) file, returns napping
        if expr.startswith("mark_file(") and expr.endswith(")"):
            args = self._parse_args(expr[10:-1])
            if len(args) < 2:
                raise CharlotteError("mark_file needs a path and data!", ln)
            path_val = str(self._evaluate(args[0].strip(), ln))
            data_val = str(self._evaluate(args[1].strip(), ln))
            resolved = self._resolve_sandboxed_path(path_val, ln)
            try:
                with open(resolved, "w", encoding="utf-8") as f:
                    f.write(data_val)
            except OSError as e:
                raise CharlotteError(f"*whimpers* Couldn't mark file: {e}", ln)
            return None

        # append_file(path, data) — append to file, returns napping
        if expr.startswith("append_file(") and expr.endswith(")"):
            args = self._parse_args(expr[12:-1])
            if len(args) < 2:
                raise CharlotteError("append_file needs a path and data!", ln)
            path_val = str(self._evaluate(args[0].strip(), ln))
            data_val = str(self._evaluate(args[1].strip(), ln))
            resolved = self._resolve_sandboxed_path(path_val, ln)
            try:
                with open(resolved, "a", encoding="utf-8") as f:
                    f.write(data_val)
            except OSError as e:
                raise CharlotteError(f"*whimpers* Couldn't append to file: {e}", ln)
            return None

        # nose_for_all(text, pattern) — all regex matches as bunny[] (check before nose_for)
        if expr.startswith("nose_for_all(") and expr.endswith(")"):
            args = self._parse_args(expr[13:-1])
            if len(args) < 2:
                raise CharlotteError("nose_for_all needs text and pattern!", ln)
            text_val = str(self._evaluate(args[0].strip(), ln))
            pattern_val = str(self._evaluate(args[1].strip(), ln))
            try:
                return re.findall(pattern_val, text_val)
            except re.error as e:
                raise CharlotteError(f"*confused sniff* Bad pattern: {e}", ln)

        # nose_for(text, pattern) — first match string or napping
        if expr.startswith("nose_for(") and expr.endswith(")"):
            args = self._parse_args(expr[9:-1])
            if len(args) < 2:
                raise CharlotteError("nose_for needs text and pattern!", ln)
            text_val = str(self._evaluate(args[0].strip(), ln))
            pattern_val = str(self._evaluate(args[1].strip(), ln))
            try:
                m = re.search(pattern_val, text_val)
                return m.group(0) if m else None
            except re.error as e:
                raise CharlotteError(f"*confused sniff* Bad pattern: {e}", ln)

        # nose_swap(text, pattern, replacement) — regex substitution
        if expr.startswith("nose_swap(") and expr.endswith(")"):
            args = self._parse_args(expr[10:-1])
            if len(args) < 3:
                raise CharlotteError("nose_swap needs text, pattern, and replacement!", ln)
            text_val = str(self._evaluate(args[0].strip(), ln))
            pattern_val = str(self._evaluate(args[1].strip(), ln))
            repl_val = str(self._evaluate(args[2].strip(), ln))
            try:
                return re.sub(pattern_val, repl_val, text_val)
            except re.error as e:
                raise CharlotteError(f"*confused sniff* Bad pattern: {e}", ln)

        # User function call
        if "(" in expr and expr.endswith(")"):
            paren_pos = expr.index("(")
            fname = expr[:paren_pos]
            if fname in self.functions:
                return self._call_function(fname, expr[paren_pos + 1:-1], ln)

        # Unary minus: -expr  (e.g. -x, -(a + b), -myFunc())
        if expr.startswith("-") and len(expr) > 1:
            return -self._evaluate(expr[1:], ln)

        # Variable lookup
        if expr in self.variables:
            return self.variables[expr]

        raise CharlotteError(
            f"*sniffs suspiciously* Who is \"{expr}\"? Charlotte doesn't know this stranger!", ln
        )

    def _find_operator(self, expr: str, op: str) -> int:
        """Find leftmost operator position respecting parentheses/brackets/braces/strings."""
        depth = 0
        in_string = False
        string_char = None
        for i in range(len(expr) - len(op) + 1):
            ch = expr[i]
            if not in_string and ch in ('"', "'"):
                in_string = True
                string_char = ch
            elif in_string and ch == string_char and self._count_preceding_backslashes(expr, i) % 2 == 0:
                in_string = False
            if not in_string:
                if ch in "([{":
                    depth += 1
                elif ch in ")]}":
                    depth -= 1
                if depth == 0 and expr[i:i + len(op)] == op:
                    return i
        return -1

    def _is_truthy(self, val) -> bool:
        if val is None or val is False or val == 0 or val == "":
            return False
        if isinstance(val, (list, dict)) and len(val) == 0:
            return False
        return True

    def _to_json_compatible(self, val):
        """Convert a CharlotteLang value to a JSON-serializable Python object."""
        if val is None or isinstance(val, (bool, int, float, str)):
            return val
        if isinstance(val, list):
            return [self._to_json_compatible(item) for item in val]
        if isinstance(val, dict):
            return {str(k): self._to_json_compatible(v) for k, v in val.items()}
        return str(val)

    # ── HTTP Server (kennel) ─────────────────────────────────

    def _handle_guard(self, text, lines, i, indent, ln):
        """Register a route handler: guard METHOD "/path":"""
        match = re.match(r'^guard\s+(GET|POST|PUT|DELETE|PATCH)\s+"(.+)":$', text)
        if not match:
            raise CharlotteError(
                '*confused head tilt* — Use: guard GET "/path":', ln
            )
        method = match.group(1)
        path = match.group(2)
        block, next_idx = self._get_block(lines, i + 1, indent)
        if not block:
            raise CharlotteError("Guard block has no body! Indent the body.", ln)

        # Convert path params like {id} to regex named groups
        param_names = re.findall(r'\{(\w+)\}', path)
        pattern_str = re.sub(r'\{(\w+)\}', r'(?P<\1>[^/]+)', path)
        pattern = re.compile(f'^{pattern_str}$')

        self._routes.append({
            "method": method,
            "path": path,
            "pattern": pattern,
            "param_names": param_names,
            "body": block,
        })
        return next_idx

    def _handle_kennel(self, text, ln):
        """Start the HTTP server: kennel PORT"""
        if self._server:
            raise CharlotteError("*confused bark* The kennel is already open!", ln)

        port_expr = text[7:].strip()
        port = self._evaluate(port_expr, ln)
        try:
            port = int(port)
        except (ValueError, TypeError):
            raise CharlotteError("*confused sniff* Kennel port must be a number!", ln)
        if not (1 <= port <= 65535):
            raise CharlotteError("*confused sniff* Port must be between 1 and 65535!", ln)

        interpreter = self

        class CharlotteHandler(http.server.BaseHTTPRequestHandler):
            def do_request(handler_self):
                parsed = urllib.parse.urlsplit(handler_self.path)
                path = parsed.path
                query_params = dict(urllib.parse.parse_qs(
                    parsed.query, keep_blank_values=True
                ))
                # Flatten single-value lists from parse_qs
                query_params = {
                    k: v[0] if len(v) == 1 else v
                    for k, v in query_params.items()
                }

                # Read request body
                content_length = int(
                    handler_self.headers.get("Content-Length", 0)
                )
                body = ""
                if content_length > 0:
                    body = handler_self.rfile.read(content_length).decode("utf-8")

                # Match against registered routes
                for route in interpreter._routes:
                    if route["method"] != handler_self.command:
                        continue
                    m = route["pattern"].match(path)
                    if not m:
                        continue

                    path_params = {
                        name: m.group(name) for name in route["param_names"]
                    }
                    req_headers = {}
                    for key in handler_self.headers:
                        req_headers[key.lower()] = handler_self.headers[key]

                    request_collar = {
                        "method": handler_self.command,
                        "path": path,
                        "headers": req_headers,
                        "body": body,
                        "params": query_params,
                        "path_params": path_params,
                    }

                    with interpreter._handler_lock:
                        saved_vars = copy.deepcopy(interpreter.variables)
                        interpreter.variables["request"] = request_collar
                        response = None
                        try:
                            interpreter._execute_block(route["body"])
                        except CharlotteReturn as ret:
                            response = ret.value
                        except CharlotteError as e:
                            handler_self.send_response(500)
                            handler_self.send_header(
                                "Content-Type", "application/json"
                            )
                            handler_self.end_headers()
                            handler_self.wfile.write(
                                json.dumps({"error": str(e)}).encode("utf-8")
                            )
                            interpreter.variables = saved_vars
                            return
                        except Exception as e:
                            handler_self.send_response(500)
                            handler_self.send_header(
                                "Content-Type", "application/json"
                            )
                            handler_self.end_headers()
                            handler_self.wfile.write(
                                json.dumps({"error": str(e)}).encode("utf-8")
                            )
                            interpreter.variables = saved_vars
                            return
                        finally:
                            interpreter.variables = saved_vars

                    if not isinstance(response, dict):
                        handler_self.send_response(500)
                        handler_self.send_header(
                            "Content-Type", "application/json"
                        )
                        handler_self.end_headers()
                        handler_self.wfile.write(json.dumps(
                            {"error": "Handler must rollover a collar{}"}
                        ).encode("utf-8"))
                        return

                    status = int(response.get("status", 200))
                    resp_body = response.get("body", "")
                    resp_headers = response.get("headers", {})

                    handler_self.send_response(status)
                    has_content_type = False
                    if isinstance(resp_headers, dict):
                        for k, v in resp_headers.items():
                            handler_self.send_header(k, str(v))
                            if k.lower() == "content-type":
                                has_content_type = True
                    if not has_content_type:
                        handler_self.send_header(
                            "Content-Type", "application/json"
                        )
                    handler_self.end_headers()

                    if isinstance(resp_body, (dict, list)):
                        handler_self.wfile.write(json.dumps(
                            interpreter._to_json_compatible(resp_body)
                        ).encode("utf-8"))
                    else:
                        handler_self.wfile.write(
                            str(resp_body).encode("utf-8")
                        )
                    return

                # No route matched — 404
                handler_self.send_response(404)
                handler_self.send_header("Content-Type", "application/json")
                handler_self.end_headers()
                handler_self.wfile.write(
                    json.dumps({"error": "Not found"}).encode("utf-8")
                )

            def do_GET(self):
                self.do_request()

            def do_POST(self):
                self.do_request()

            def do_PUT(self):
                self.do_request()

            def do_DELETE(self):
                self.do_request()

            def do_PATCH(self):
                self.do_request()

            def log_message(self, format, *args):
                interpreter.output_fn(
                    f"🐕 {args[0]} {args[1]} {args[2]}", "bark"
                )

        self._server = http.server.HTTPServer(("", port), CharlotteHandler)
        self._server_thread = threading.Thread(
            target=self._server.serve_forever, daemon=True
        )
        self._server_thread.start()
        self.output_fn(f"🐕 Kennel is open on port {port}! *tail wag*", "bark")

    def _handle_leave_kennel(self, ln):
        """Stop the HTTP server."""
        if not self._server:
            raise CharlotteError("*confused sniff* No kennel to close!", ln)
        self._server.shutdown()
        self._server = None
        self._server_thread = None
        self.output_fn("🐕 Kennel is closed. *lays down*", "bark")


# ─── REPL ──────────────────────────────────────────────────

def run_repl():
    """Interactive CharlotteLang REPL."""
    print("🐕 CharlotteLang v4.4 REPL")
    print("   Type Charlotte code below. Commands:")
    print("   .run      — execute the buffer")
    print("   .clear    — clear the buffer")
    print("   .show     — show the buffer")
    print("   .vars     — show all current variables")
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
                interp.execute(source)
                buffer = []
            else:
                print("🐾 Nothing to run!")
            continue
        elif line.strip() == ".vars":
            if interp.variables:
                print("─── variables ───")
                for k, v in interp.variables.items():
                    print(f"  {k} = {v!r}")
                print("─────────────────")
            else:
                print("🐾 No variables set yet")
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
                interp.execute(stripped)
                buffer = []


def print_quick_ref():
    """Print the CharlotteLang quick reference."""
    print("""
┌──────────────────────────────────────────────────────────┐
│  🐕 CharlotteLang Quick Reference                        │
├──────────────────────────────────────────────────────────┤
│  bark "hello"            → print to stdout               │
│  bark                    → print blank line              │
│  howl "oops"             → print to stderr               │
│  fetch x = 10            → create variable               │
│  x = 20                  → reassign variable             │
│  growl "error!"          → throw error                   │
│                                                          │
│  sniff x is bigger than 5:                               │
│    bark "big!"                                           │
│  else sniff x equals 5:                                  │
│    bark "five!"                                          │
│  else pout:                                              │
│    bark "small"                                          │
│                                                          │
│  zoomies 5 times:        → for loop (lap = index)        │
│    bark f"lap {lap}"                                     │
│                                                          │
│  zoomies through toys:   → foreach (toy=item, lap=idx)   │
│    bark toy                                              │
│  zoomies item through toys: → named foreach (lap=idx)    │
│    bark item                                             │
│                                                          │
│  zoomies while x > 0:    → while loop                    │
│    x = x - 1                                             │
│                                                          │
│  teach trick greet(who):                                 │
│    bark f"hi {who}"                                      │
│    rollover "done"       → return                        │
│                                                          │
│  shake off               → break                         │
│  keep going              → continue                      │
│  bunny[1, 2, 3]          → array literal                 │
│  arr[-1]                 → last element (neg index)      │
│  arr[1:3]                → slice [start:stop:step]       │
│  collar{"a": 1, "b": 2}  → dictionary literal            │
│  list.toys / dict.toys   → length                        │
│  list.give("item")       → append                        │
│  list.pop() / .pop(idx)  → remove and return element     │
│  list.sort()             → sort in-place                 │
│  list.reverse()          → reverse in-place              │
│  list.remove(val)        → remove first occurrence       │
│  list.index(val)         → find position (-1 if missing) │
│  list.join(",")          → join to string                │
│  dict.bury("key", val)   → set key                       │
│  dict.dig("key")         → delete key                    │
│  dict.keys / dict.values → keys/values as list           │
│  str.chew(" ")           → split string                  │
│  str.replace(old, new)   → replace substring             │
│  str.find("sub")         → find index (-1 if missing)    │
│  str.startswith("pre")   → bool                          │
│  str.endswith("suf")     → bool                          │
│  str.trim()              → strip whitespace              │
│  str.upper() / .lower()  → case conversion               │
│  "hello\nworld"          → escape sequences (\n\t\\\")   │
│  loyal / stranger        → true / false                  │
│  napping                 → null/None                     │
│  breed(x)                → type name                     │
│  goodBoy(x)              → convert to int                │
│  loyal(x)                → convert to bool               │
│  abs(x)                  → absolute value                │
│  round(x) / round(x, n)  → round a number               │
│  min(a, b) / min(list)   → minimum value                 │
│  max(a, b) / max(list)   → maximum value                 │
│  beg("prompt")           → read user input (string)      │
│  squirrel()              → random float 0.0–1.0          │
│  squirrel(n)             → random int 0..n-1             │
│  squirrel(a, b)          → random int a..b (inclusive)   │
│  nap(seconds)            → sleep                         │
│  sniff_env("VAR")        → get env variable or napping   │
│                                                          │
│  dig_up(url)             → HTTP GET → collar{status,     │
│                            body, headers}                │
│  dig_up(url, headers)    → GET with custom headers       │
│  bury(url, data)         → HTTP POST → same collar       │
│  bury(url, data, headers)→ POST with custom headers      │
│  chew_json(string)       → parse JSON → collar/bunny     │
│  yap_json(value)         → serialize to JSON string      │
│                                                          │
│  woof this is a comment  → comment (always)              │
│  sniff this is ignored   → comment (only without colon)  │
│  a ~ b                   → string concat                 │
│  and / or / not          → logical ops                   │
│  in / not in             → membership test               │
│  + - * / // % **         → arithmetic (** = power)       │
│  "ha" * 3                → "hahaha" (string repeat)      │
│                                                          │
│  careful:                → try block                     │
│    risky code here                                       │
│  oops e:                 → catch (e = error message)     │
│    bark e                                                │
│                                                          │
│  snag "file.bark"        → import another file           │
│                                                          │
│  guard GET "/path":      → register route handler        │
│    rollover collar{...}  → respond (status, body, hdrs)  │
│  guard POST "/dogs/{id}":→ route with path parameters    │
│  kennel 8080             → start HTTP server             │
│  leave_kennel            → stop HTTP server              │
│                                                          │
│  REPL commands: .run .clear .show .vars .help .exit      │
└──────────────────────────────────────────────────────────┘
""")


# ─── CLI ENTRY POINT ───────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("🐕 CharlotteLang v4.4")
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
        interp.run(source, source_path=filepath)

        # If a kennel (server) is running, block until Ctrl+C
        if interp._server:
            try:
                interp._server_shutdown.wait()
            except KeyboardInterrupt:
                print("\n🐕 Closing the kennel... *sad tail*")
                interp._server.shutdown()

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

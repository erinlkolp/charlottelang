"""
Comprehensive test suite for the CharlotteLang interpreter.
"""

import pytest
import sys
import os
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from charlotte import Interpreter, CharlotteError, parse_lines


# ─── Test Helpers ───────────────────────────────────────────

def run(source: str) -> list[str]:
    """Run CharlotteLang source and return list of output strings."""
    outputs = []
    interp = Interpreter(output_fn=lambda text, kind="bark": outputs.append(text))
    interp.run(source)
    return outputs


def run_errors(source: str) -> list[str]:
    """Run source and return only error outputs."""
    errors = []
    interp = Interpreter(output_fn=lambda text, kind="bark": errors.append(text) if kind == "error" else None)
    interp.run(source)
    return errors


def last(source: str) -> str:
    """Run source and return the last output line."""
    return run(source)[-1]


def only(source: str) -> str:
    """Run source expecting exactly one output line, return it."""
    result = run(source)
    assert len(result) == 1, f"Expected 1 output, got {len(result)}: {result}"
    return result[0]


# ─── Tokenizer Tests ────────────────────────────────────────

class TestTokenizer:
    def test_blank_lines_stripped(self):
        lines = parse_lines("bark \"a\"\n\n\nbark \"b\"")
        assert len(lines) == 2

    def test_comment_lines_stripped(self):
        lines = parse_lines("sniff this is a comment\nbark \"hello\"")
        assert len(lines) == 1
        assert lines[0].text == 'bark "hello"'

    def test_bare_sniff_stripped(self):
        lines = parse_lines("sniff\nbark \"hello\"")
        assert len(lines) == 1

    def test_sniff_with_colon_not_stripped(self):
        lines = parse_lines("sniff x equals 1:")
        assert len(lines) == 1

    def test_indentation_tracked(self):
        lines = parse_lines("bark \"a\"\n  bark \"b\"\n    bark \"c\"")
        assert lines[0].indent == 0
        assert lines[1].indent == 2
        assert lines[2].indent == 4

    def test_line_numbers_tracked(self):
        lines = parse_lines("\nbark \"a\"\n\nbark \"b\"")
        assert lines[0].line_num == 2
        assert lines[1].line_num == 4


# ─── I/O Tests ──────────────────────────────────────────────

class TestIO:
    def test_bark_string(self):
        assert only('bark "hello"') == "hello"

    def test_bark_number(self):
        assert only("bark 42") == "42"

    def test_bark_expression(self):
        assert only("bark 2 + 3") == "5"

    def test_bark_boolean_true(self):
        assert only("bark loyal") == "True"

    def test_bark_boolean_false(self):
        assert only("bark stranger") == "False"

    def test_bark_null(self):
        assert only("bark napping") == "None"

    def test_bark_multiple(self):
        out = run('bark "a"\nbark "b"\nbark "c"')
        assert out == ["a", "b", "c"]

    def test_growl_raises_error(self):
        errors = run_errors('growl "bad thing happened"')
        assert len(errors) == 1
        assert "bad thing happened" in errors[0]


# ─── Variable Tests ─────────────────────────────────────────

class TestVariables:
    def test_fetch_integer(self):
        assert only("fetch x = 5\nbark x") == "5"

    def test_fetch_float(self):
        assert only("fetch x = 3.14\nbark x") == "3.14"

    def test_fetch_string(self):
        assert only('fetch name = "Charlotte"\nbark name') == "Charlotte"

    def test_fetch_boolean_true(self):
        assert only("fetch flag = loyal\nbark flag") == "True"

    def test_fetch_boolean_false(self):
        assert only("fetch flag = stranger\nbark flag") == "False"

    def test_fetch_null(self):
        assert only("fetch x = napping\nbark x") == "None"

    def test_reassign_variable(self):
        assert only("fetch x = 10\nx = 20\nbark x") == "20"

    def test_reassign_preserves_type(self):
        assert only('fetch x = 1\nx = "hello"\nbark x') == "hello"

    def test_unknown_variable_error(self):
        errors = run_errors("bark unknown_var")
        assert len(errors) == 1
        assert "unknown_var" in errors[0]

    def test_fstring_interpolation(self):
        assert only('fetch name = "Charlotte"\nbark f"Hi {name}!"') == "Hi Charlotte!"

    def test_fstring_expression(self):
        assert only('fetch x = 5\nbark f"Result: {x * 2}"') == "Result: 10"

    def test_fstring_multiple_vars(self):
        assert only('fetch a = 1\nfetch b = 2\nbark f"{a} + {b} = {a + b}"') == "1 + 2 = 3"


# ─── Arithmetic Tests ───────────────────────────────────────

class TestArithmetic:
    def test_addition(self):
        assert only("bark 3 + 4") == "7"

    def test_subtraction(self):
        assert only("bark 10 - 3") == "7"

    def test_multiplication(self):
        assert only("bark 3 * 4") == "12"

    def test_division(self):
        assert only("bark 10 / 4") == "2.5"

    def test_integer_division(self):
        assert only("bark 10 // 3") == "3"

    def test_modulo(self):
        assert only("bark 10 % 3") == "1"

    def test_negative_numbers(self):
        assert only("bark 0 - 5") == "-5"

    def test_float_arithmetic(self):
        assert only("bark 1.5 + 2.5") == "4.0"

    def test_division_by_zero_error(self):
        errors = run_errors("bark 5 / 0")
        assert len(errors) == 1
        assert "zero" in errors[0].lower()

    def test_integer_division_by_zero_error(self):
        errors = run_errors("bark 5 // 0")
        assert len(errors) == 1

    def test_string_plus_coercion(self):
        assert only('bark "hi" + " there"') == "hi there"

    def test_number_plus_string_coercion(self):
        assert only('bark 42 + " is the answer"') == "42 is the answer"

    def test_string_concat_tilde(self):
        assert only('bark "hello" ~ " " ~ "world"') == "hello world"

    def test_operator_precedence(self):
        assert only("bark 2 + 3 * 4") == "14"


# ─── Comparison Tests ───────────────────────────────────────

class TestComparisons:
    def test_equals_true(self):
        assert only("bark 5 equals 5") == "True"

    def test_equals_false(self):
        assert only("bark 5 equals 6") == "False"

    def test_double_equals(self):
        assert only("bark 5 == 5") == "True"

    def test_not_equals(self):
        assert only("bark 5 not equals 6") == "True"

    def test_not_equals_symbol(self):
        assert only("bark 5 != 6") == "True"

    def test_bigger_than_true(self):
        assert only("bark 10 is bigger than 5") == "True"

    def test_bigger_than_false(self):
        assert only("bark 3 is bigger than 5") == "False"

    def test_smaller_than_true(self):
        assert only("bark 3 is smaller than 5") == "True"

    def test_smaller_than_false(self):
        assert only("bark 10 is smaller than 5") == "False"

    def test_greater_equal(self):
        assert only("bark 5 >= 5") == "True"

    def test_less_equal(self):
        assert only("bark 5 <= 5") == "True"

    def test_in_list_true(self):
        assert only("fetch arr = bunny[1, 2, 3]\nbark 2 in arr") == "True"

    def test_in_list_false(self):
        assert only("fetch arr = bunny[1, 2, 3]\nbark 5 in arr") == "False"

    def test_in_dict_true(self):
        assert only('fetch d = collar{"a": 1}\nbark "a" in d') == "True"

    def test_in_dict_false(self):
        assert only('fetch d = collar{"a": 1}\nbark "b" in d') == "False"

    def test_in_string_true(self):
        assert only('fetch s = "hello"\nbark "ell" in s') == "True"


# ─── Logical Operator Tests ─────────────────────────────────

class TestLogical:
    def test_and_true(self):
        assert only("bark loyal and loyal") == "True"

    def test_and_false(self):
        assert only("bark loyal and stranger") == "False"

    def test_or_true(self):
        assert only("bark stranger or loyal") == "True"

    def test_or_false(self):
        assert only("bark stranger or stranger") == "False"

    def test_not_true(self):
        assert only("bark not stranger") == "True"

    def test_not_false(self):
        assert only("bark not loyal") == "False"

    def test_and_short_circuit(self):
        # If left is false, right is never evaluated
        assert only("bark stranger and loyal") == "False"

    def test_or_short_circuit(self):
        assert only("bark loyal or stranger") == "True"

    def test_not_zero(self):
        assert only("bark not 0") == "True"

    def test_not_empty_string(self):
        assert only('bark not ""') == "True"


# ─── Control Flow Tests ─────────────────────────────────────

class TestConditionals:
    def test_if_true(self):
        assert only('fetch x = 5\nsniff x is bigger than 3:\n  bark "yes"') == "yes"

    def test_if_false(self):
        assert run('fetch x = 1\nsniff x is bigger than 3:\n  bark "yes"') == []

    def test_else_pout(self):
        assert only('fetch x = 1\nsniff x is bigger than 3:\n  bark "big"\nelse pout:\n  bark "small"') == "small"

    def test_else_sniff(self):
        result = run(
            'fetch x = 5\n'
            'sniff x is bigger than 10:\n'
            '  bark "big"\n'
            'else sniff x equals 5:\n'
            '  bark "five"\n'
            'else pout:\n'
            '  bark "other"'
        )
        assert result == ["five"]

    def test_multiple_elif_branches(self):
        code = (
            'fetch x = 3\n'
            'sniff x equals 1:\n'
            '  bark "one"\n'
            'else sniff x equals 2:\n'
            '  bark "two"\n'
            'else sniff x equals 3:\n'
            '  bark "three"\n'
            'else pout:\n'
            '  bark "other"'
        )
        assert only(code) == "three"

    def test_if_truthy_number(self):
        assert only('fetch x = 1\nsniff x:\n  bark "yes"') == "yes"

    def test_if_falsy_zero(self):
        assert run('fetch x = 0\nsniff x:\n  bark "yes"') == []

    def test_if_falsy_empty_string(self):
        assert run('fetch x = ""\nsniff x:\n  bark "yes"') == []

    def test_if_falsy_null(self):
        assert run('fetch x = napping\nsniff x:\n  bark "yes"') == []


# ─── Loop Tests ─────────────────────────────────────────────

class TestLoops:
    def test_zoomies_times(self):
        out = run("zoomies 3 times:\n  bark lap")
        assert out == ["0", "1", "2"]

    def test_zoomies_times_zero(self):
        assert run("zoomies 0 times:\n  bark lap") == []

    def test_zoomies_through_list(self):
        out = run("fetch arr = bunny[10, 20, 30]\nzoomies through arr:\n  bark toy")
        assert out == ["10", "20", "30"]

    def test_zoomies_through_list_lap_index(self):
        out = run("fetch arr = bunny[10, 20, 30]\nzoomies through arr:\n  bark lap")
        assert out == ["0", "1", "2"]

    def test_zoomies_while(self):
        out = run("fetch x = 3\nzoomies while x is bigger than 0:\n  bark x\n  x = x - 1")
        assert out == ["3", "2", "1"]

    def test_shake_off_break(self):
        out = run("zoomies 10 times:\n  sniff lap equals 3:\n    shake off\n  bark lap")
        assert out == ["0", "1", "2"]

    def test_keep_going_continue(self):
        out = run("zoomies 5 times:\n  sniff lap % 2 equals 0:\n    keep going\n  bark lap")
        assert out == ["1", "3"]

    def test_keep_going_in_foreach(self):
        out = run(
            "fetch arr = bunny[1, 2, 3, 4, 5]\n"
            "zoomies through arr:\n"
            "  sniff toy % 2 equals 0:\n"
            "    keep going\n"
            "  bark toy"
        )
        assert out == ["1", "3", "5"]

    def test_keep_going_in_while(self):
        out = run(
            "fetch x = 0\n"
            "zoomies while x is smaller than 5:\n"
            "  x = x + 1\n"
            "  sniff x % 2 equals 0:\n"
            "    keep going\n"
            "  bark x"
        )
        assert out == ["1", "3", "5"]

    def test_nested_loops(self):
        out = run("zoomies 2 times:\n  zoomies 2 times:\n    bark lap")
        assert len(out) == 4

    def test_zoomies_through_dict(self):
        out = run('fetch d = collar{"x": 1, "y": 2}\nzoomies through d:\n  bark toy')
        assert set(out) == {"x", "y"}

    def test_while_safety_limit(self):
        errors = run_errors("fetch x = loyal\nzoomies while x:\n  bark x")
        assert len(errors) == 1
        assert "collapsed" in errors[0].lower() or "infinite" in errors[0].lower()

    def test_zoomies_named_var_list(self):
        out = run("fetch arr = bunny[10, 20, 30]\nzoomies item through arr:\n  bark item")
        assert out == ["10", "20", "30"]

    def test_zoomies_named_var_lap_index(self):
        out = run("fetch arr = bunny[10, 20, 30]\nzoomies item through arr:\n  bark lap")
        assert out == ["0", "1", "2"]

    def test_zoomies_named_var_dict(self):
        out = run('fetch d = collar{"x": 1, "y": 2}\nzoomies k through d:\n  bark k')
        assert set(out) == {"x", "y"}

    def test_zoomies_named_var_break(self):
        out = run("fetch arr = bunny[1, 2, 3, 4, 5]\nzoomies n through arr:\n  sniff n equals 3:\n    shake off\n  bark n")
        assert out == ["1", "2"]

    def test_zoomies_named_var_continue(self):
        out = run("fetch arr = bunny[1, 2, 3, 4, 5]\nzoomies n through arr:\n  sniff n % 2 equals 0:\n    keep going\n  bark n")
        assert out == ["1", "3", "5"]

    def test_zoomies_unnamed_backward_compat(self):
        out = run("fetch arr = bunny[10, 20, 30]\nzoomies through arr:\n  bark toy")
        assert out == ["10", "20", "30"]


# ─── User Input Tests ────────────────────────────────────────

class TestUserInput:
    def test_beg_returns_string(self, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda prompt="": "charlotte")
        assert only('fetch name = beg("Name: ")\nbark name') == "charlotte"

    def test_beg_empty_prompt(self, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda prompt="": "woof")
        assert only('fetch r = beg("")\nbark r') == "woof"

    def test_beg_used_in_expression(self, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda prompt="": "5")
        assert only('fetch n = goodBoy(beg("Enter: "))\nbark n + 1') == "6"

    def test_beg_prompt_is_evaluated(self, monkeypatch):
        captured = []
        monkeypatch.setattr("builtins.input", lambda prompt="": captured.append(prompt) or "hi")
        run('fetch label = "say something: "\nfetch r = beg(label)')
        assert captured == ["say something: "]


# ─── Function Tests ─────────────────────────────────────────

class TestFunctions:
    def test_define_and_call(self):
        assert only('teach trick greet():\n  bark "woof"\ngreet()') == "woof"

    def test_function_with_params(self):
        assert only('teach trick say(msg):\n  bark msg\nsay("hello")') == "hello"

    def test_function_with_multiple_params(self):
        assert only('teach trick add(a, b):\n  bark a + b\nadd(3, 4)') == "7"

    def test_function_return_value(self):
        assert only('teach trick double(n):\n  rollover n * 2\nfetch r = double(5)\nbark r') == "10"

    def test_function_bare_rollover(self):
        assert only('teach trick nothing():\n  rollover\nfetch r = nothing()\nbark r') == "None"

    def test_function_local_scope(self):
        # Variables inside function don't leak out
        code = (
            'fetch x = 1\n'
            'teach trick change():\n'
            '  fetch x = 999\n'
            'change()\n'
            'bark x'
        )
        assert only(code) == "1"

    def test_function_params_dont_leak(self):
        code = (
            'teach trick fn(y):\n'
            '  bark y\n'
            'fn(42)\n'
            'bark "done"'
        )
        out = run(code)
        assert out == ["42", "done"]

    def test_recursive_function(self):
        code = (
            'teach trick factorial(n):\n'
            '  sniff n is smaller than 2:\n'
            '    rollover 1\n'
            '  rollover n * factorial(n - 1)\n'
            'bark factorial(5)'
        )
        assert only(code) == "120"

    def test_function_called_in_expression(self):
        code = (
            'teach trick double(n):\n'
            '  rollover n * 2\n'
            'bark double(3) + double(4)'
        )
        assert only(code) == "14"


# ─── Array Tests ────────────────────────────────────────────

class TestArrays:
    def test_empty_array(self):
        assert only("fetch arr = bunny[]\nbark arr.toys") == "0"

    def test_array_literal(self):
        assert only("fetch arr = bunny[1, 2, 3]\nbark arr.toys") == "3"

    def test_array_index(self):
        assert only("fetch arr = bunny[10, 20, 30]\nbark arr[0]") == "10"

    def test_array_index_last(self):
        assert only("fetch arr = bunny[10, 20, 30]\nbark arr[2]") == "30"

    def test_array_give_append(self):
        assert only("fetch arr = bunny[1, 2]\narr.give(3)\nbark arr.toys") == "3"

    def test_array_give_value(self):
        assert only("fetch arr = bunny[]\narr.give(99)\nbark arr[0]") == "99"

    def test_array_of_strings(self):
        out = run('fetch arr = bunny["a", "b", "c"]\nzoomies through arr:\n  bark toy')
        assert out == ["a", "b", "c"]

    def test_array_mixed_types(self):
        assert only('fetch arr = bunny[1, "two", loyal]\nbark arr.toys') == "3"

    def test_array_index_assignment(self):
        assert only("fetch arr = bunny[1, 2, 3]\narr[1] = 99\nbark arr[1]") == "99"

    def test_howbig_array(self):
        assert only("fetch arr = bunny[1, 2, 3]\nbark howBig(arr)") == "3"

    def test_foreach_collects_all(self):
        out = run("fetch arr = bunny[5, 10, 15]\nzoomies through arr:\n  bark toy")
        assert out == ["5", "10", "15"]


# ─── Dictionary Tests ───────────────────────────────────────

class TestDictionaries:
    def test_empty_dict(self):
        assert only("fetch d = collar{}\nbark d.toys") == "0"

    def test_dict_literal(self):
        assert only('fetch d = collar{"a": 1, "b": 2}\nbark d.toys') == "2"

    def test_dict_access(self):
        assert only('fetch d = collar{"name": "Charlotte"}\nbark d["name"]') == "Charlotte"

    def test_dict_integer_key(self):
        assert only("fetch d = collar{1: \"one\", 2: \"two\"}\nbark d[1]") == "one"

    def test_dict_bury_set(self):
        assert only('fetch d = collar{}\nd.bury("x", 42)\nbark d["x"]') == "42"

    def test_dict_dig_delete(self):
        assert only('fetch d = collar{"a": 1, "b": 2}\nd.dig("a")\nbark d.toys') == "1"

    def test_dict_dig_missing_key_no_error(self):
        # dig on missing key should not raise
        errors = run_errors('fetch d = collar{}\nd.dig("missing")')
        assert errors == []

    def test_dict_keys(self):
        out = run('fetch d = collar{"x": 1, "y": 2}\nfetch k = d.keys\nzoomies through k:\n  bark toy')
        assert set(out) == {"x", "y"}

    def test_dict_values(self):
        out = run('fetch d = collar{"x": 1, "y": 2}\nfetch v = d.values\nzoomies through v:\n  bark toy')
        assert set(out) == {"1", "2"}

    def test_dict_index_assignment(self):
        assert only('fetch d = collar{"a": 1}\nd["a"] = 99\nbark d["a"]') == "99"

    def test_dict_index_assignment_new_key(self):
        assert only('fetch d = collar{}\nd["new"] = "value"\nbark d["new"]') == "value"

    def test_dict_in_membership(self):
        assert only('fetch d = collar{"a": 1}\nbark "a" in d') == "True"

    def test_dict_not_in_membership(self):
        assert only('fetch d = collar{"a": 1}\nbark "b" in d') == "False"

    def test_dict_toys_length(self):
        assert only('fetch d = collar{"a": 1, "b": 2, "c": 3}\nbark d.toys') == "3"

    def test_dict_missing_key_error(self):
        errors = run_errors('fetch d = collar{"a": 1}\nbark d["missing"]')
        assert len(errors) == 1

    def test_dict_iterate_keys(self):
        out = run('fetch d = collar{"a": 1}\nzoomies through d:\n  bark toy')
        assert out == ["a"]

    def test_howbig_dict(self):
        assert only('fetch d = collar{"a": 1, "b": 2}\nbark howBig(d)') == "2"

    def test_dict_update_existing(self):
        assert only('fetch d = collar{"x": 1}\nd.bury("x", 2)\nbark d["x"]') == "2"


# ─── Try/Catch Tests ────────────────────────────────────────

class TestTryCatch:
    def test_careful_without_error(self):
        out = run('careful:\n  bark "safe"\n')
        assert out == ["safe"]

    def test_careful_catches_growl(self):
        out = run('careful:\n  growl "oops"\noops:\n  bark "caught"')
        assert out == ["caught"]

    def test_oops_with_variable(self):
        out = run('careful:\n  growl "the error"\noops e:\n  bark e')
        assert len(out) == 1
        assert "the error" in out[0]

    def test_careful_no_oops_eats_error(self):
        # careful without oops: silently eats the error
        out = run('careful:\n  growl "silent"\nbark "after"')
        assert out == ["after"]

    def test_oops_block_not_run_on_success(self):
        out = run('careful:\n  bark "ok"\noops:\n  bark "should not appear"')
        assert out == ["ok"]

    def test_break_propagates_through_careful(self):
        # CharlotteBreak must propagate through careful
        out = run('zoomies 5 times:\n  careful:\n    shake off\n  bark "no"')
        assert out == []

    def test_return_propagates_through_careful(self):
        code = (
            'teach trick fn():\n'
            '  careful:\n'
            '    rollover "returned"\n'
            '  bark "unreachable"\n'
            'bark fn()'
        )
        assert only(code) == "returned"

    def test_nested_try_catch(self):
        code = (
            'careful:\n'
            '  careful:\n'
            '    growl "inner"\n'
            '  oops e:\n'
            '    bark "inner caught"\n'
            'oops e:\n'
            '  bark "outer caught"'
        )
        assert only(code) == "inner caught"

    def test_careful_catches_index_error(self):
        out = run('careful:\n  fetch arr = bunny[1]\n  bark arr[99]\noops e:\n  bark "caught"')
        assert out == ["caught"]


# ─── Import Tests ───────────────────────────────────────────

class TestImports:
    def test_snag_loads_file(self, tmp_path):
        lib = tmp_path / "lib.bark"
        lib.write_text('bark "from lib"')
        main = tmp_path / "main.bark"
        main.write_text('snag "lib.bark"')

        outputs = []
        interp = Interpreter(output_fn=lambda text, kind="bark": outputs.append(text))
        interp.run(main.read_text(), source_path=str(main))
        assert outputs == ["from lib"]

    def test_snag_loads_functions(self, tmp_path):
        lib = tmp_path / "helpers.bark"
        lib.write_text('teach trick add(a, b):\n  rollover a + b')
        main = tmp_path / "main.bark"
        main.write_text('snag "helpers.bark"\nbark add(3, 4)')

        outputs = []
        interp = Interpreter(output_fn=lambda text, kind="bark": outputs.append(text))
        interp.run(main.read_text(), source_path=str(main))
        assert outputs == ["7"]

    def test_circular_import_prevented(self, tmp_path):
        a = tmp_path / "a.bark"
        b = tmp_path / "b.bark"
        a.write_text('snag "b.bark"\nbark "a done"')
        b.write_text('snag "a.bark"\nbark "b done"')

        outputs = []
        interp = Interpreter(output_fn=lambda text, kind="bark": outputs.append(text))
        interp.run(a.read_text(), source_path=str(a))
        # Should not recurse infinitely; b done runs, a is skipped due to circular guard
        assert "b done" in outputs

    def test_snag_missing_file_error(self):
        errors = run_errors('snag "nonexistent.bark"')
        assert len(errors) == 1
        assert "nonexistent.bark" in errors[0]


# ─── String Method Tests ────────────────────────────────────

class TestStringMethods:
    def test_chew_split(self):
        out = run('fetch s = "a,b,c"\nfetch parts = s.chew(",")\nzoomies through parts:\n  bark toy')
        assert out == ["a", "b", "c"]

    def test_chew_split_spaces(self):
        out = run('fetch s = "hello world"\nfetch parts = s.chew(" ")\nbark parts.toys')
        assert out == ["2"]

    def test_trim_whitespace(self):
        assert only('fetch s = "  hello  "\nbark s.trim()') == "hello"

    def test_trim_no_whitespace(self):
        assert only('fetch s = "hello"\nbark s.trim()') == "hello"

    def test_upper(self):
        assert only('fetch s = "hello"\nbark s.upper()') == "HELLO"

    def test_lower(self):
        assert only('fetch s = "HELLO"\nbark s.lower()') == "hello"

    def test_upper_preserves_non_alpha(self):
        assert only('fetch s = "hello 123"\nbark s.upper()') == "HELLO 123"


# ─── Built-in Function Tests ────────────────────────────────

class TestBuiltins:
    def test_howbig_list(self):
        assert only("fetch arr = bunny[1, 2, 3]\nbark howBig(arr)") == "3"

    def test_howbig_string(self):
        assert only('bark howBig("hello")') == "5"

    def test_howbig_empty(self):
        assert only("bark howBig(bunny[])") == "0"

    def test_treat_to_float(self):
        assert only('bark treat("3.14")') == "3.14"

    def test_treat_int_to_float(self):
        assert only("bark treat(5)") == "5.0"

    def test_yap_to_string(self):
        assert only("bark yap(42)") == "42"

    def test_yap_float(self):
        assert only("bark yap(3.14)") == "3.14"

    def test_breed_int(self):
        assert only("bark breed(42)") == "number"

    def test_breed_float(self):
        assert only("bark breed(3.14)") == "number"

    def test_breed_string(self):
        assert only('bark breed("hello")') == "string"

    def test_breed_boolean(self):
        assert only("bark breed(loyal)") == "boolean"

    def test_breed_null(self):
        assert only("bark breed(napping)") == "napping"

    def test_breed_list(self):
        assert only("bark breed(bunny[1, 2])") == "bunny"

    def test_breed_dict(self):
        assert only('fetch d = collar{}\nbark breed(d)') == "collar"

    def test_goodboy_float_to_int(self):
        assert only("bark goodBoy(3.9)") == "3"

    def test_goodboy_string_to_int(self):
        assert only('bark goodBoy("42")') == "42"


# ─── Parse Args Tests ───────────────────────────────────────

class TestParseArgs:
    def test_nested_parens_not_split(self):
        assert only('teach trick f(x):\n  rollover x\nbark f(f(5))') == "5"

    def test_nested_brackets_not_split(self):
        assert only('teach trick f(arr):\n  rollover arr.toys\nbark f(bunny[1, 2, 3])') == "3"

    def test_string_comma_not_split(self):
        assert only('teach trick f(s):\n  rollover s\nbark f("a,b,c")') == "a,b,c"


# ─── Truthy/Falsy Tests ─────────────────────────────────────

class TestTruthy:
    def test_zero_is_falsy(self):
        assert only('sniff 0:\n  bark "y"\nelse pout:\n  bark "n"') == "n"

    def test_empty_string_is_falsy(self):
        assert only('sniff "":\n  bark "y"\nelse pout:\n  bark "n"') == "n"

    def test_null_is_falsy(self):
        assert only('sniff napping:\n  bark "y"\nelse pout:\n  bark "n"') == "n"

    def test_stranger_is_falsy(self):
        assert only('sniff stranger:\n  bark "y"\nelse pout:\n  bark "n"') == "n"

    def test_empty_list_is_falsy(self):
        assert only('fetch arr = bunny[]\nsniff arr:\n  bark "y"\nelse pout:\n  bark "n"') == "n"

    def test_empty_dict_is_falsy(self):
        assert only('fetch d = collar{}\nsniff d:\n  bark "y"\nelse pout:\n  bark "n"') == "n"

    def test_one_is_truthy(self):
        assert only('sniff 1:\n  bark "y"') == "y"

    def test_nonempty_string_is_truthy(self):
        assert only('sniff "hi":\n  bark "y"') == "y"

    def test_loyal_is_truthy(self):
        assert only('sniff loyal:\n  bark "y"') == "y"


# ─── Integration Tests ──────────────────────────────────────

class TestIntegration:
    def test_fizzbuzz(self):
        code = (
            'zoomies 15 times:\n'
            '  fetch n = lap + 1\n'
            '  sniff n % 15 equals 0:\n'
            '    bark "FizzBuzz"\n'
            '  else sniff n % 3 equals 0:\n'
            '    bark "Fizz"\n'
            '  else sniff n % 5 equals 0:\n'
            '    bark "Buzz"\n'
            '  else pout:\n'
            '    bark n'
        )
        out = run(code)
        assert out[0] == "1"
        assert out[2] == "Fizz"
        assert out[4] == "Buzz"
        assert out[14] == "FizzBuzz"

    def test_fibonacci(self):
        code = (
            'teach trick fib(n):\n'
            '  sniff n is smaller than 2:\n'
            '    rollover n\n'
            '  rollover fib(n - 1) + fib(n - 2)\n'
            'bark fib(0)\n'
            'bark fib(1)\n'
            'bark fib(7)'
        )
        out = run(code)
        assert out == ["0", "1", "13"]

    def test_word_count_with_dict(self):
        code = (
            'fetch words = bunny["apple", "banana", "apple", "cherry", "banana", "apple"]\n'
            'fetch counts = collar{}\n'
            'zoomies through words:\n'
            '  sniff toy in counts:\n'
            '    counts[toy] = counts[toy] + 1\n'
            '  else pout:\n'
            '    counts[toy] = 1\n'
            'bark counts["apple"]\n'
            'bark counts["banana"]\n'
            'bark counts["cherry"]'
        )
        out = run(code)
        assert out == ["3", "2", "1"]

    def test_error_recovery_with_careful(self):
        code = (
            'fetch results = bunny[]\n'
            'fetch inputs = bunny[10, 0, 5, 0, 2]\n'
            'zoomies through inputs:\n'
            '  careful:\n'
            '    fetch r = 100 // toy\n'
            '    results.give(r)\n'
            '  oops:\n'
            '    results.give(-1)\n'
            'bark results[0]\n'
            'bark results[1]\n'
            'bark results[2]'
        )
        out = run(code)
        assert out == ["10", "-1", "20"]

    def test_string_processing_pipeline(self):
        code = (
            'fetch sentence = "  Hello, World! How are you?  "\n'
            'fetch trimmed = sentence.trim()\n'
            'fetch lower = trimmed.lower()\n'
            'fetch words = lower.chew(" ")\n'
            'bark words.toys'
        )
        assert only(code) == "5"

    def test_higher_order_like_pattern(self):
        code = (
            'teach trick apply_double(arr):\n'
            '  fetch result = bunny[]\n'
            '  zoomies through arr:\n'
            '    result.give(toy * 2)\n'
            '  rollover result\n'
            'fetch nums = bunny[1, 2, 3, 4, 5]\n'
            'fetch doubled = apply_double(nums)\n'
            'zoomies through doubled:\n'
            '  bark toy'
        )
        out = run(code)
        assert out == ["2", "4", "6", "8", "10"]


# ─── Escape Sequence Tests ──────────────────────────────────

class TestEscapeSequences:
    def test_newline_escape(self):
        result = only('bark "hello\\nworld"')
        assert result == "hello\nworld"

    def test_tab_escape(self):
        result = only('bark "a\\tb"')
        assert result == "a\tb"

    def test_backslash_escape(self):
        result = only('bark "one\\\\two"')
        assert result == "one\\two"

    def test_escaped_quote(self):
        result = only('bark "say \\"hello\\""')
        assert result == 'say "hello"'

    def test_escape_in_variable(self):
        assert only('fetch s = "line1\\nline2"\nbark s') == "line1\nline2"

    def test_escape_in_fstring(self):
        result = only('fetch name = "Charlotte"\nbark f"Hello\\t{name}"')
        assert result == "Hello\tCharlotte"

    def test_no_escape_passthrough(self):
        result = only('bark "\\q"')
        assert result == "\\q"

    def test_escape_affects_string_length(self):
        assert only('fetch s = "a\\nb"\nbark howBig(s)') == "3"


# ─── Negative Indexing Tests ────────────────────────────────

class TestNegativeIndexing:
    def test_list_negative_one(self):
        assert only("fetch arr = bunny[10, 20, 30]\nbark arr[-1]") == "30"

    def test_list_negative_two(self):
        assert only("fetch arr = bunny[10, 20, 30]\nbark arr[-2]") == "20"

    def test_string_negative_index(self):
        assert only('fetch s = "hello"\nbark s[-1]') == "o"

    def test_string_positive_index(self):
        assert only('fetch s = "hello"\nbark s[0]') == "h"

    def test_string_middle_index(self):
        assert only('fetch s = "hello"\nbark s[2]') == "l"


# ─── Slicing Tests ──────────────────────────────────────────

class TestSlicing:
    def test_list_slice_start_stop(self):
        assert only("fetch arr = bunny[1, 2, 3, 4, 5]\nbark arr[1:3]") == "[2, 3]"

    def test_list_slice_from_start(self):
        assert only("fetch arr = bunny[1, 2, 3, 4, 5]\nbark arr[:2]") == "[1, 2]"

    def test_list_slice_to_end(self):
        assert only("fetch arr = bunny[1, 2, 3, 4, 5]\nbark arr[2:]") == "[3, 4, 5]"

    def test_list_slice_negative(self):
        assert only("fetch arr = bunny[1, 2, 3, 4, 5]\nbark arr[-2:]") == "[4, 5]"

    def test_list_slice_with_step(self):
        assert only("fetch arr = bunny[1, 2, 3, 4, 5]\nbark arr[::2]") == "[1, 3, 5]"

    def test_list_slice_full_copy(self):
        assert only("fetch arr = bunny[1, 2, 3]\nbark arr[:]") == "[1, 2, 3]"

    def test_string_slice(self):
        assert only('fetch s = "hello world"\nbark s[0:5]') == "hello"

    def test_string_slice_to_end(self):
        assert only('fetch s = "hello world"\nbark s[6:]') == "world"

    def test_string_slice_negative(self):
        assert only('fetch s = "hello"\nbark s[-3:]') == "llo"

    def test_slice_length(self):
        assert only("fetch arr = bunny[1, 2, 3, 4, 5]\nfetch s = arr[1:4]\nbark s.toys") == "3"


# ─── New String Method Tests ────────────────────────────────

class TestNewStringMethods:
    def test_replace_basic(self):
        assert only('fetch s = "hello world"\nbark s.replace("world", "Charlotte")') == "hello Charlotte"

    def test_replace_all_occurrences(self):
        assert only('fetch s = "aaa"\nbark s.replace("a", "b")') == "bbb"

    def test_replace_not_found(self):
        assert only('fetch s = "hello"\nbark s.replace("xyz", "abc")') == "hello"

    def test_find_found(self):
        assert only('fetch s = "hello world"\nbark s.find("world")') == "6"

    def test_find_not_found(self):
        assert only('fetch s = "hello"\nbark s.find("xyz")') == "-1"

    def test_find_from_start(self):
        assert only('fetch s = "abcabc"\nbark s.find("b")') == "1"

    def test_startswith_true(self):
        assert only('fetch s = "hello world"\nbark s.startswith("hello")') == "True"

    def test_startswith_false(self):
        assert only('fetch s = "hello world"\nbark s.startswith("world")') == "False"

    def test_endswith_true(self):
        assert only('fetch s = "hello world"\nbark s.endswith("world")') == "True"

    def test_endswith_false(self):
        assert only('fetch s = "hello world"\nbark s.endswith("hello")') == "False"


# ─── New List Method Tests ──────────────────────────────────

class TestNewListMethods:
    def test_join_comma(self):
        assert only('fetch arr = bunny["a", "b", "c"]\nbark arr.join(",")') == "a,b,c"

    def test_join_space(self):
        assert only('fetch arr = bunny["hello", "world"]\nbark arr.join(" ")') == "hello world"

    def test_join_empty_sep(self):
        assert only('fetch arr = bunny["a", "b", "c"]\nbark arr.join("")') == "abc"

    def test_join_numbers(self):
        assert only("fetch arr = bunny[1, 2, 3]\nbark arr.join(\"-\")") == "1-2-3"

    def test_index_found(self):
        assert only("fetch arr = bunny[10, 20, 30]\nbark arr.index(20)") == "1"

    def test_index_first_occurrence(self):
        assert only("fetch arr = bunny[1, 2, 1, 2]\nbark arr.index(2)") == "1"

    def test_index_not_found(self):
        assert only("fetch arr = bunny[1, 2, 3]\nbark arr.index(99)") == "-1"

    def test_pop_last(self):
        assert only("fetch arr = bunny[1, 2, 3]\nfetch x = arr.pop()\nbark x") == "3"

    def test_pop_last_removes(self):
        assert only("fetch arr = bunny[1, 2, 3]\narr.pop()\nbark arr.toys") == "2"

    def test_pop_index(self):
        assert only("fetch arr = bunny[10, 20, 30]\nfetch x = arr.pop(1)\nbark x") == "20"

    def test_pop_index_removes(self):
        assert only("fetch arr = bunny[10, 20, 30]\narr.pop(0)\nbark arr[0]") == "20"

    def test_pop_empty_error(self):
        errors = run_errors("fetch arr = bunny[]\narr.pop()")
        assert len(errors) == 1

    def test_sort_numbers(self):
        assert only("fetch arr = bunny[3, 1, 4, 1, 5, 2]\narr.sort()\nbark arr[0]") == "1"

    def test_sort_is_inplace(self):
        out = run("fetch arr = bunny[3, 1, 2]\narr.sort()\nzoomies through arr:\n  bark toy")
        assert out == ["1", "2", "3"]

    def test_reverse_inplace(self):
        out = run("fetch arr = bunny[1, 2, 3]\narr.reverse()\nzoomies through arr:\n  bark toy")
        assert out == ["3", "2", "1"]

    def test_remove_first_occurrence(self):
        out = run("fetch arr = bunny[1, 2, 1, 2]\narr.remove(1)\nzoomies through arr:\n  bark toy")
        assert out == ["2", "1", "2"]

    def test_remove_missing_no_error(self):
        errors = run_errors("fetch arr = bunny[1, 2, 3]\narr.remove(99)")
        assert errors == []

    def test_remove_shrinks_list(self):
        assert only("fetch arr = bunny[1, 2, 3]\narr.remove(2)\nbark arr.toys") == "2"


# ─── Woof Comment Tests (fix #1) ────────────────────────────

class TestWoofComments:
    """woof is always a comment regardless of content; sniff without colon is legacy comment."""

    def test_woof_basic(self):
        assert only('woof this is a comment\nbark "hi"') == "hi"

    def test_woof_bare(self):
        assert only('woof\nbark "hi"') == "hi"

    def test_woof_with_trailing_colon(self):
        # The bug: a comment ending in ":" was treated as an if-statement
        assert only('woof this ends with a colon:\nbark "hi"') == "hi"

    def test_woof_many_colons(self):
        assert only('woof key: value: more: stuff:\nbark "hi"') == "hi"

    def test_woof_indented(self):
        out = run('sniff loyal:\n  woof indented comment:\n  bark "yes"')
        assert out == ["yes"]

    def test_woof_does_not_execute(self):
        # Content after woof is never evaluated
        out = run('woof bark "should not print"\nbark "only this"')
        assert out == ["only this"]

    def test_sniff_legacy_comment_no_colon(self):
        assert only('sniff this is a legacy comment\nbark "hi"') == "hi"

    def test_sniff_if_colon_still_works(self):
        assert only('sniff loyal:\n  bark "yes"') == "yes"

    def test_sniff_comment_before_if(self):
        out = run('sniff a comment here\nsniff loyal:\n  bark "yes"')
        assert out == ["yes"]

    def test_multiple_woof_comments(self):
        out = run('woof first\nwoof second\nwoof third\nbark "result"')
        assert out == ["result"]


# ─── Escaped Quote Arg Parsing Tests (fix #4) ───────────────

class TestEscapedQuoteArgs:
    """_parse_args must not end string tracking on backslash-escaped quotes."""

    def test_escaped_quote_in_single_arg(self):
        code = 'teach trick echo(s):\n  rollover s\nfetch r = echo("say \\"hi\\"")\nbark r'
        assert only(code) == 'say "hi"'

    def test_comma_inside_string_arg_not_split(self):
        code = 'teach trick echo(s):\n  rollover s\nfetch r = echo("hello, world")\nbark r'
        assert only(code) == "hello, world"

    def test_escaped_quote_then_real_comma(self):
        code = (
            'teach trick pair(a, b):\n'
            '  bark a\n'
            '  bark b\n'
            'pair("say \\"hi\\"", "bye")'
        )
        out = run(code)
        assert out == ['say "hi"', "bye"]

    def test_nested_function_call_as_arg(self):
        code = (
            'teach trick add(a, b):\n'
            '  rollover a + b\n'
            'teach trick double(n):\n'
            '  rollover n * 2\n'
            'bark add(double(3), double(4))'
        )
        assert only(code) == "14"

    def test_bunny_literal_as_arg(self):
        code = (
            'teach trick first(arr):\n'
            '  rollover arr[0]\n'
            'bark first(bunny[99, 2, 3])'
        )
        assert only(code) == "99"


# ─── New Built-in Tests (squirrel, nap, sniff_env) ──────────

class TestNewBuiltins:
    def test_squirrel_no_args_returns_float(self):
        assert only('fetch r = squirrel()\nbark breed(r)') == "number"

    def test_squirrel_no_args_in_range(self):
        # Run 20 times; all results must be in [0, 1)
        code = (
            'zoomies 20 times:\n'
            '  fetch r = squirrel()\n'
            '  sniff r >= 0:\n'
            '    sniff r is smaller than 1:\n'
            '      bark "ok"'
        )
        out = run(code)
        assert out == ["ok"] * 20

    def test_squirrel_n_in_range(self):
        code = (
            'zoomies 20 times:\n'
            '  fetch r = squirrel(10)\n'
            '  sniff r >= 0:\n'
            '    sniff r is smaller than 10:\n'
            '      bark "ok"'
        )
        out = run(code)
        assert out == ["ok"] * 20

    def test_squirrel_ab_in_range(self):
        code = (
            'zoomies 20 times:\n'
            '  fetch r = squirrel(5, 15)\n'
            '  sniff r >= 5:\n'
            '    sniff r <= 15:\n'
            '      bark "ok"'
        )
        out = run(code)
        assert out == ["ok"] * 20

    def test_squirrel_returns_int_with_args(self):
        assert only('fetch r = squirrel(100)\nbark breed(r)') == "number"

    def test_nap_statement(self):
        # nap as a standalone statement should not error
        assert only('nap(0)\nbark "done"') == "done"

    def test_nap_expression(self):
        # nap used in fetch should return napping (None)
        assert only('fetch r = nap(0)\nbark r') == "None"

    def test_sniff_env_set(self):
        import os
        os.environ["CHARLOTTE_TEST_VAR"] = "chihuahua"
        assert only('fetch v = sniff_env("CHARLOTTE_TEST_VAR")\nbark v') == "chihuahua"
        del os.environ["CHARLOTTE_TEST_VAR"]

    def test_sniff_env_unset_returns_null(self):
        assert only('fetch v = sniff_env("__DEFINITELY_NOT_SET_XYZ__")\nbark v') == "None"

    def test_sniff_env_unset_is_falsy(self):
        out = run('fetch v = sniff_env("__DEFINITELY_NOT_SET_XYZ__")\nsniff v:\n  bark "set"\nelse pout:\n  bark "unset"')
        assert out == ["unset"]


# ─── Example File Tests ──────────────────────────────────────

class TestExamples:
    def _run_file(self, filename):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(root, "examples", filename)
        outputs = []
        interp = Interpreter(output_fn=lambda text, kind="bark": outputs.append(text))
        with open(path) as f:
            source = f.read()
        interp.run(source, source_path=path)
        return outputs

    def test_hello(self):
        out = self._run_file("hello.bark")
        assert out[0] == "Yap yap! Hello World! 🐾"
        assert "Charlotte has 10 treats!" in out
        assert "After sharing: 5 each 🦴" in out

    def test_fizzbuzz_length(self):
        out = self._run_file("fizzbuzz.bark")
        assert len(out) == 20

    def test_fizzbuzz_fizz(self):
        out = self._run_file("fizzbuzz.bark")
        assert out[2] == "3: 🐕 BARK! (Fizz)"

    def test_fizzbuzz_buzz(self):
        out = self._run_file("fizzbuzz.bark")
        assert out[4] == "5: 💨 ZOOM! (Buzz)"

    def test_fizzbuzz_fizzbuzz(self):
        out = self._run_file("fizzbuzz.bark")
        assert out[14] == "15: 🐕 BARK BUZZ! (FizzBuzz)"

    def test_full_day_morning(self):
        out = self._run_file("full_day.bark")
        assert "🐕 BARK BARK BARK at mailman!!" in out

    def test_full_day_mood(self):
        out = self._run_file("full_day.bark")
        assert "Charlotte is: ecstatic 🥰" in out

    def test_full_day_evening(self):
        out = self._run_file("full_day.bark")
        assert "Scratch. My. Belly. Now. 👑" in out

    def test_new_features_completes(self):
        out = self._run_file("new_features.bark")
        assert "All new features working! *happy tail wag*" in out

    def test_new_features_imports(self):
        out = self._run_file("new_features.bark")
        assert "Woof woof, World! Welcome to the pack!" in out

    def test_new_features_dict(self):
        out = self._run_file("new_features.bark")
        assert "Name: Charlotte" in out

    def test_new_features_try_catch(self):
        out = self._run_file("new_features.bark")
        assert any("Caught error" in line for line in out)


# ─── F-string brace-depth tests (fix #18) ───────────────────

class TestFStringBraceDepth:
    """The old regex [^}]+ broke on any } inside {…} expressions."""

    def test_dict_string_key_in_fstring(self):
        # d["key"] — no } in expression but validates the new parser
        src = 'fetch d = collar{"k": "v"}\nbark f"val={d["k"]}"'
        assert only(src) == "val=v"

    def test_collar_literal_in_fstring(self):
        # collar{…} has } inside the expression — old regex [^}]+ broke here
        src = 'bark f"type: {breed(collar{"a": 99})}"'
        assert only(src) == "type: collar"

    def test_nested_fstring(self):
        src = 'fetch name = "Charlotte"\nbark f"hi {f"dear {name}"}!"'
        assert only(src) == "hi dear Charlotte!"

    def test_double_brace_literal_open(self):
        assert only('bark f"{{open"') == "{open"

    def test_double_brace_literal_close(self):
        assert only('bark f"close}}"') == "close}"

    def test_double_brace_both(self):
        assert only('bark f"{{literal}}"') == "{literal}"

    def test_multiple_expressions(self):
        src = 'fetch a = 1\nfetch b = 2\nbark f"{a} + {b} = {a + b}"'
        assert only(src) == "1 + 2 = 3"

    def test_expression_with_method_call(self):
        src = 'fetch s = "hello world"\nfetch parts = s.chew(" ")\nbark f"words: {parts.toys}"'
        assert only(src) == "words: 2"

    def test_arithmetic_in_fstring(self):
        assert only('fetch x = 7\nbark f"double: {x * 2}"') == "double: 14"

    def test_fstring_no_expressions(self):
        assert only('bark f"just text"') == "just text"

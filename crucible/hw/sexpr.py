"""
crucible.hw.sexpr — pure-Python S-expression parser for KiCad file format.

KiCad .kicad_sch and .kicad_pcb files are Lisp-like S-expressions. This module
tokenizes and parses them into nested Python lists, and serializes them back.

No external dependencies. Handles KiCad 6, 7, 8, and 9/10 file formats.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any


class SExprError(ValueError):
    """Raised on malformed S-expression input."""


# ── Tokenizer ─────────────────────────────────────────────────────────────────

def tokenize(text: str) -> list[str]:
    """Convert raw KiCad file text into a flat token list.

    Tokens are one of: '(' | ')' | quoted_string | bare_token
    Comments (; to end of line) are stripped.
    Quoted strings preserve internal content verbatim (backslash escapes respected).
    """
    tokens: list[str] = []
    i = 0
    n = len(text)
    buf: list[str] = []

    def flush() -> None:
        if buf:
            tokens.append("".join(buf))
            buf.clear()

    while i < n:
        c = text[i]

        if c == ";":
            flush()
            while i < n and text[i] != "\n":
                i += 1

        elif c in "()":
            flush()
            tokens.append(c)
            i += 1

        elif c == '"':
            flush()
            i += 1
            s: list[str] = []
            while i < n:
                ch = text[i]
                if ch == "\\":
                    i += 1
                    if i < n:
                        escaped = text[i]
                        # Preserve common escape sequences
                        if escaped == "n":
                            s.append("\n")
                        elif escaped == "t":
                            s.append("\t")
                        elif escaped == "\\":
                            s.append("\\")
                        elif escaped == '"':
                            s.append('"')
                        else:
                            s.append("\\")
                            s.append(escaped)
                        i += 1
                elif ch == '"':
                    i += 1
                    break
                else:
                    s.append(ch)
                    i += 1
            tokens.append('"' + "".join(s) + '"')

        elif c in " \t\r\n":
            flush()
            i += 1

        else:
            buf.append(c)
            i += 1

    flush()
    return tokens


# ── Parser ────────────────────────────────────────────────────────────────────

def parse(tokens: list[str], pos: int = 0) -> tuple[Any, int]:
    """Recursive descent parser over tokenize() output.

    Returns (node, next_pos) where node is:
      - str  for bare tokens
      - str  for quoted strings (without surrounding quotes)
      - list for S-expression lists: [head, *children]

    Raises SExprError on malformed input.
    """
    if pos >= len(tokens):
        raise SExprError("Unexpected end of token stream")

    tok = tokens[pos]

    if tok == ")":
        raise SExprError(f"Unexpected ')' at token index {pos}")

    if tok == "(":
        pos += 1
        items: list[Any] = []
        while pos < len(tokens) and tokens[pos] != ")":
            child, pos = parse(tokens, pos)
            items.append(child)
        if pos >= len(tokens):
            raise SExprError("Missing closing ')'")
        pos += 1  # consume ')'
        return items, pos

    # Bare token or quoted string
    if tok.startswith('"') and tok.endswith('"') and len(tok) >= 2:
        return tok[1:-1], pos + 1  # strip surrounding quotes

    return tok, pos + 1


def load(path: str | Path) -> list:
    """Read a .kicad_sch or .kicad_pcb file and return the top-level S-expression."""
    text = Path(path).read_text(encoding="utf-8")
    tokens = tokenize(text)
    if not tokens:
        raise SExprError(f"Empty file: {path}")
    node, _ = parse(tokens)
    if not isinstance(node, list):
        raise SExprError(f"Top-level node is not a list in: {path}")
    return node


# ── Serializer ────────────────────────────────────────────────────────────────

def _needs_quotes(s: str) -> bool:
    """Return True if the string must be quoted in S-expression output."""
    if not s:
        return True
    for ch in s:
        if ch in (' ', '\t', '\r', '\n', '"', '(', ')', ';', '\\'):
            return True
    return False


def _quote(s: str) -> str:
    """Wrap a string in quotes, escaping internal special characters."""
    s = s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t")
    return f'"{s}"'


def _is_flat(node: list) -> bool:
    """Return True if all children of a list node are bare strings (no nested lists)."""
    return all(isinstance(child, str) for child in node)


def dump(node: Any, indent: int = 0) -> str:
    """Serialize a node back to KiCad S-expression format.

    Flat lists (all-string children) are written on one line.
    Nested lists are indented 2 spaces per level.
    """
    if isinstance(node, str):
        return _quote(node) if _needs_quotes(node) else node

    if not isinstance(node, list):
        raise TypeError(f"Cannot serialize node of type {type(node)}")

    if not node:
        return "()"

    if _is_flat(node):
        inner = " ".join(dump(child) for child in node)
        return f"({inner})"

    pad = "  " * indent
    inner_pad = "  " * (indent + 1)
    parts: list[str] = []
    for i, child in enumerate(node):
        if i == 0:
            parts.append(dump(child, indent + 1))
        else:
            parts.append(inner_pad + dump(child, indent + 1))
    return "(" + parts[0] + "\n" + "\n".join(parts[1:]) + "\n" + pad + ")"


# ── Navigation helpers ────────────────────────────────────────────────────────

def find_all(node: list, key: str) -> list[list]:
    """Depth-first search: all sub-expressions where sub[0] == key."""
    results: list[list] = []
    if isinstance(node, list):
        if node and node[0] == key:
            results.append(node)
        for child in node[1:]:
            if isinstance(child, list):
                results.extend(find_all(child, key))
    return results


def find_first(node: list, key: str) -> list | None:
    """Return the first sub-expression where sub[0] == key, or None."""
    if isinstance(node, list):
        if node and node[0] == key:
            return node
        for child in node[1:]:
            if isinstance(child, list):
                found = find_first(child, key)
                if found is not None:
                    return found
    return None


def get_value(node: list, key: str, default: Any = None) -> Any:
    """Get the second element of the first direct child where child[0] == key.

    Searches only direct children (not recursive).
    Returns default if not found or child has fewer than 2 elements.
    """
    for child in node[1:]:
        if isinstance(child, list) and child and child[0] == key:
            return child[1] if len(child) >= 2 else default
    return default

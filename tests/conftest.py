"""Shared fixtures for flux-skills tests."""
import sys
import os
import pytest
import tempfile
import struct
import importlib.util

# Ensure runtime modules are importable
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_root, "runtime"))
sys.path.insert(0, _root)

# Pre-import MUDNavigator from the hyphenated directory path
_mud_nav_path = os.path.join(_root, "skills", "mud-navigator", "mud_navigator.py")
if os.path.exists(_mud_nav_path) and "skills.mud_navigator" not in sys.modules:
    _mud_nav_parent = os.path.join(_root, "skills", "mud-navigator")
    sys.path.insert(0, _mud_nav_parent)
    import mud_navigator as _mud_nav_mod
    sys.modules["skills.mud_navigator.mud_navigator"] = _mud_nav_mod
    # Also register parent packages
    import types
    _skills = types.ModuleType("skills")
    _skills.__path__ = [os.path.join(_root, "skills")]
    sys.modules["skills"] = _skills
    _mud_nav_pkg = types.ModuleType("skills.mud_navigator")
    _mud_nav_pkg.__path__ = [_mud_nav_parent]
    sys.modules["skills.mud_navigator"] = _mud_nav_pkg
    sys.modules["skills.mud_navigator"].mud_navigator = _mud_nav_mod


@pytest.fixture
def tmp_bytecode_dir(tmp_path):
    """Provide a temp directory for bytecode files."""
    return tmp_path


def make_code(*parts) -> bytes:
    """Helper to build bytecode from mixed bytes/int/struct parts."""
    def flatten(p):
        if isinstance(p, (list, tuple)):
            for item in p:
                yield from flatten(item)
        else:
            yield p
    return b"".join(
        p if isinstance(p, bytes) else struct.pack(">B", p)
        for p in flatten(parts)
    )


def imm16(v):
    return struct.pack(">h", v)


def addr16(v):
    return struct.pack(">H", v)


@pytest.fixture
def code_helper():
    """Provide bytecode construction helpers."""
    return type("CH", (), {
        "code": make_code,
        "imm16": imm16,
        "addr16": addr16,
    })()


@pytest.fixture
def fresh_vm():
    """Create a fresh SkillVM instance."""
    from skill_vm import SkillVM
    return SkillVM()

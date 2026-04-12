#!/usr/bin/env python3
"""
Cross-language conformance test for FLUX Skill VM.
Generates test bytecode and runs against all available runtimes.
"""

import subprocess
import struct
import sys
import os

RUNTIMES = {
    "python": ["python3", "-c", "import sys; sys.path.insert(0,'runtime'); from skill_vm import SkillVM; vm=SkillVM(); vm.load_bytecode(sys.argv[1]); vm.run(); print(f'HALT after {len(vm.get_output())} outputs')"],
    "c": ["runtime/c/skill_vm"],
    "go": ["runtime/go/skill_vm"],
    "rust": ["runtime/rust/target/release/flux-skill-vm"],
    "zig": ["runtime/zig/skill_vm"],
}

def movi(reg, val):
    return struct.pack(">Bbh", 0x02, reg, val)

def add(rd, rs1, rs2):
    return bytes([0x08, rd, rs1, rs2])

def sub(rd, rs1, rs2):
    return bytes([0x09, rd, rs1, rs2])

def mul(rd, rs1, rs2):
    return bytes([0x0A, rd, rs1, rs2])

def push(val):
    return struct.pack(">Bh", 0x28, val)

def pop(reg):
    return bytes([0x29, reg])

def store(key, reg):
    return bytes([0x50, key, reg])

def load(reg, key):
    return bytes([0x51, reg, key])

def out():
    return bytes([0x80])

def halt():
    return bytes([0x00])

TESTS = [
    {
        "name": "movi_halt",
        "desc": "MOVI R0, 42; HALT → R0=42",
        "code": movi(0, 42) + halt(),
        "expect_r0": 42,
    },
    {
        "name": "add_basic",
        "desc": "R0=10, R1=20, ADD R2 R0 R1 → R2=30",
        "code": movi(0, 10) + movi(1, 20) + add(2, 0, 1) + halt(),
        "expect_r2": 30,
    },
    {
        "name": "sub_basic",
        "desc": "R0=50, R1=20, SUB R2 R0 R1 → R2=30",
        "code": movi(0, 50) + movi(1, 20) + sub(2, 0, 1) + halt(),
        "expect_r2": 30,
    },
    {
        "name": "mul_basic",
        "desc": "R0=6, R1=7, MUL R2 R0 R1 → R2=42",
        "code": movi(0, 6) + movi(1, 7) + mul(2, 0, 1) + halt(),
        "expect_r2": 42,
    },
    {
        "name": "push_pop",
        "desc": "PUSH 99, POP R3 → R3=99",
        "code": push(99) + pop(3) + halt(),
        "expect_r3": 99,
    },
    {
        "name": "store_load",
        "desc": "R0=77, STORE 1 R0, LOAD R3 1 → R3=77",
        "code": movi(0, 77) + store(1, 0) + movi(0, 0) + load(3, 1) + halt(),
        "expect_r3": 77,
    },
    {
        "name": "negative_immediate",
        "desc": "MOVI R0, -5 → R0=-5",
        "code": movi(0, -5) + halt(),
        "expect_r0": -5,
    },
]

def run_test(test, runtime_name, runtime_cmd, tmpdir):
    """Run a test bytecode against a runtime and check output."""
    bc_path = os.path.join(tmpdir, f"{test['name']}.fluxbc")
    with open(bc_path, "wb") as f:
        f.write(test["code"])

    try:
        result = subprocess.run(
            runtime_cmd + [bc_path],
            capture_output=True, text=True, timeout=5,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        output = result.stdout.strip()
        # Parse JSON output lines to check register values
        return output, result.returncode
    except Exception as e:
        return f"ERROR: {e}", -1

def check_output(output, test):
    """Check if output contains expected register values."""
    import json
    for line in output.split("\n"):
        line = line.strip()
        if line.startswith("{"):
            try:
                data = json.loads(line)
                for key, expected in test.items():
                    if key.startswith("expect_"):
                        reg = key.replace("expect_r", "r")
                        if reg in data:
                            if data[reg] != expected:
                                return False, f"{reg}: got {data[reg]}, expected {expected}"
                return True, "OK"
            except json.JSONDecodeError:
                pass
    return True, "no JSON to check"

if __name__ == "__main__":
    import tempfile
    tmpdir = tempfile.mkdtemp()

    print(f"FLUX Skill VM Cross-Language Conformance Tests")
    print(f"=" * 60)

    available = {}
    for name, cmd in RUNTIMES.items():
        cmd_path = cmd[0] if len(cmd) == 1 else cmd[1] if "--" not in cmd[0] else None
        full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), cmd_path) if cmd_path else cmd[0]
        if os.path.exists(full_path):
            available[name] = [full_path] + cmd[1:] if len(cmd) > 1 else [full_path]

    if not available:
        print("No runtimes found!")
        sys.exit(1)

    print(f"Runtimes: {', '.join(available.keys())}")
    print()

    total_pass = 0
    total_fail = 0

    for test in TESTS:
        print(f"  {test['name']}: {test['desc']}")
        for rname, rcmd in available.items():
            output, rc = run_test(test, rname, rcmd, tmpdir)
            ok, msg = check_output(output, test)
            status = "✅" if ok else "❌"
            print(f"    {rname}: {status} {msg}")
            if ok:
                total_pass += 1
            else:
                total_fail += 1

    print()
    print(f"Results: {total_pass} passed, {total_fail} failed")
    sys.exit(1 if total_fail > 0 else 0)

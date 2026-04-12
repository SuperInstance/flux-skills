#!/usr/bin/env python3
import pytest, sys, os, struct
sys.path.insert(0, os.path.dirname(__file__))
from skill_vm import SkillVM


def _code(*parts) -> bytes:
    return b"".join(p if isinstance(p, bytes) else struct.pack(">B", p) for p in _flatten(parts))

def _flatten(parts):
    for p in parts:
        if isinstance(p, list):
            yield from _flatten(p)
        else:
            yield p

def imm16(v):
    return struct.pack(">h", v)

def addr16(v):
    return struct.pack(">H", v)


class TestSkillVM:
    def test_halt(self):
        vm = SkillVM()
        vm.code = _code(0x00)
        vm.run()
        assert vm.halted

    def test_movi(self):
        vm = SkillVM()
        vm.code = _code([0x02, 0, imm16(42), 0x00])
        vm.run()
        assert vm.registers[0] == 42

    def test_add(self):
        vm = SkillVM()
        vm.code = _code(
            [0x02, 0, imm16(10)],
            [0x02, 1, imm16(20)],
            [0x08, 2, 0, 1],   # ADD R2, R0, R1
            0x00,
        )
        vm.run()
        assert vm.registers[2] == 30

    def test_sub(self):
        vm = SkillVM()
        vm.code = _code(
            [0x02, 0, imm16(50)],
            [0x02, 1, imm16(20)],
            [0x09, 2, 0, 1],
            0x00,
        )
        vm.run()
        assert vm.registers[2] == 30

    def test_mul(self):
        vm = SkillVM()
        vm.code = _code(
            [0x02, 0, imm16(6)],
            [0x02, 1, imm16(7)],
            [0x0A, 2, 0, 1],
            0x00,
        )
        vm.run()
        assert vm.registers[2] == 42

    def test_push_pop(self):
        vm = SkillVM()
        vm.code = _code(
            [0x28, imm16(42)],  # PUSH 42
            [0x29, 0],           # POP R0
            0x00,
        )
        vm.run()
        assert vm.registers[0] == 42

    def test_output(self):
        vm = SkillVM()
        vm.code = _code(0x80, 0x00)
        result = vm.run()
        assert len(result) == 1

    def test_input(self):
        vm = SkillVM()
        vm.load_input([{"a": 10, "b": 20}])
        vm.code = _code(0x81, 0x00)
        vm.run()
        assert vm.registers[0] == 10
        assert vm.registers[1] == 20

    def test_state_save_load(self):
        vm = SkillVM()
        vm.registers[0] = 99
        vm.code = _code(0x84, 0x00)
        vm.run()
        assert vm.state["registers"][0] == 99

    def test_store_load(self):
        vm = SkillVM()
        vm.code = _code(
            [0x02, 0, imm16(77)],
            [0x50, 1, 0],   # STORE key=1, value=R0
            [0x02, 0, imm16(0)],  # clear R0
            [0x51, 0, 1],   # LOAD R0, key=1
            0x00,
        )
        vm.run()
        assert vm.registers[0] == 77

    def test_loop_with_max_steps(self):
        vm = SkillVM()
        vm.code = _code([0x03, addr16(0)])  # JMP 0
        vm.run(max_steps=100)
        assert not vm.halted

    def test_call_ret(self):
        vm = SkillVM()
        # CALL 5, then HALT. At 5: MOVI R0 99, RET
        vm.code = _code(
            [0x06, addr16(4)],  # offset 0: CALL 5
            0x00,                # offset 3: HALT
            [0x02, 0, imm16(99)],  # offset 5: MOVI R0, 99
            0x07,                # offset 9: RET
        )
        vm.run()
        assert vm.registers[0] == 99
        assert vm.halted

    def test_config(self):
        vm = SkillVM(config={"behavior": {"max_thoughts": 50}})
        assert vm.config["behavior"]["max_thoughts"] == 50

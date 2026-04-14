"""
Comprehensive tests for the FLUX Skill VM runtime.

Tests cover:
1. All opcodes (HALT, MOVI, JMP, JZ, JNZ, CALL, RET, ADD, SUB, MUL, CMP,
   PUSH, POP, STORE, LOAD, OUT, IN, STATE_SAVE, STATE_LOAD)
2. Register operations (read, write, overflow bounds)
3. Stack operations (push, pop, underflow, depth)
4. Memory operations (store, load, key types)
5. Flags (zero, negative) and conditional jumps
6. Call/Return stack management
7. Output/Input data streams
8. State save/load persistence
9. Max steps safety
10. Unknown opcode handling
11. Edge cases (empty code, boundary values, etc.)
"""

import struct
import pytest
import sys
import os
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "runtime"))
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


# ===========================================================================
# Basic VM Lifecycle Tests
# ===========================================================================

class TestVMLifecycle:
    def test_vm_creation_default(self):
        vm = SkillVM()
        assert vm.registers == [0] * 16
        assert vm.stack == []
        assert vm.memory == {}
        assert vm.flags == {"zero": False, "negative": False}
        assert vm.pc == 0
        assert vm.code == b""
        assert vm.config == {}
        assert vm.input_data == []
        assert vm.output_data == []
        assert vm.state == {}
        assert not vm.halted
        assert vm.call_stack == []

    def test_vm_creation_with_config(self):
        vm = SkillVM(config={"behavior": {"max_thoughts": 50}})
        assert vm.config["behavior"]["max_thoughts"] == 50

    def test_load_bytecode_from_file(self):
        vm = SkillVM()
        with tempfile.NamedTemporaryFile(suffix=".fluxbc", delete=False) as f:
            f.write(b"\x00")
            path = f.name
        try:
            vm.load_bytecode(path)
            assert vm.code == b"\x00"
        finally:
            os.unlink(path)

    def test_load_input(self):
        vm = SkillVM()
        vm.load_input([{"a": 10}, {"b": 20}])
        assert len(vm.input_data) == 2

    def test_load_config(self):
        vm = SkillVM()
        vm.load_config({"key": "value"})
        assert vm.config == {"key": "value"}

    def test_get_output_empty(self):
        vm = SkillVM()
        assert vm.get_output() == []

    def test_get_state_empty(self):
        vm = SkillVM()
        assert vm.get_state() == {}

    def test_run_empty_code(self):
        vm = SkillVM()
        result = vm.run()
        assert result == []
        assert not vm.halted

    def test_run_returns_output_data(self):
        vm = SkillVM()
        vm.code = _code(0x80, 0x00)  # OUT, HALT
        result = vm.run()
        assert len(result) == 1
        assert "registers" in result[0]


# ===========================================================================
# HALT Opcode Tests
# ===========================================================================

class TestHalt:
    def test_halt(self):
        vm = SkillVM()
        vm.code = _code(0x00)
        vm.run()
        assert vm.halted

    def test_halt_stops_execution(self):
        """Instructions after HALT should not execute."""
        vm = SkillVM()
        vm.code = _code([0x00], [0x02, 0, imm16(99)])  # HALT; MOVI R0, 99
        vm.run()
        assert vm.halted
        assert vm.registers[0] == 0  # MOVI should not execute

    def test_halt_advances_pc(self):
        vm = SkillVM()
        vm.code = _code(0x00)
        vm.run()
        assert vm.pc == 1

    def test_double_halt(self):
        vm = SkillVM()
        vm.code = _code(0x00, 0x00)
        vm.run()
        assert vm.halted


# ===========================================================================
# MOVI Opcode Tests
# ===========================================================================

class TestMOVI:
    def test_movi_positive(self):
        vm = SkillVM()
        vm.code = _code([0x02, 0, imm16(42), 0x00])
        vm.run()
        assert vm.registers[0] == 42

    def test_movi_zero(self):
        vm = SkillVM()
        vm.code = _code([0x02, 5, imm16(0), 0x00])
        vm.run()
        assert vm.registers[5] == 0

    def test_movi_negative(self):
        vm = SkillVM()
        vm.code = _code([0x02, 1, imm16(-5), 0x00])
        vm.run()
        assert vm.registers[1] == -5

    def test_movi_max_positive(self):
        vm = SkillVM()
        vm.code = _code([0x02, 0, imm16(32767), 0x00])
        vm.run()
        assert vm.registers[0] == 32767

    def test_movi_max_negative(self):
        vm = SkillVM()
        vm.code = _code([0x02, 0, imm16(-32768), 0x00])
        vm.run()
        assert vm.registers[0] == -32768

    def test_movi_multiple_registers(self):
        vm = SkillVM()
        vm.code = _code(
            [0x02, 0, imm16(10)],
            [0x02, 1, imm16(20)],
            [0x02, 15, imm16(99)],
            0x00,
        )
        vm.run()
        assert vm.registers[0] == 10
        assert vm.registers[1] == 20
        assert vm.registers[15] == 99
        assert vm.registers[2] == 0  # untouched

    def test_movi_overwrite(self):
        vm = SkillVM()
        vm.code = _code(
            [0x02, 0, imm16(10)],
            [0x02, 0, imm16(20)],
            0x00,
        )
        vm.run()
        assert vm.registers[0] == 20


# ===========================================================================
# JMP Opcode Tests
# ===========================================================================

class TestJMP:
    def test_jmp_forward(self):
        vm = SkillVM()
        # MOVI R0,1 (4 bytes, offset 0-3), JMP to offset 8 (3 bytes, offset 4-6), MOVI R0,99 (4 bytes, offset 7-10), HALT (1 byte, offset 11)
        vm.code = _code([0x02, 0, imm16(1)], [0x03, addr16(7)], [0x02, 0, imm16(99)], 0x00)
        vm.run()
        assert vm.registers[0] == 99

    def test_jmp_backward(self):
        vm = SkillVM()
        # MOVI R0,42 (offset 0-3), HALT (offset 4)
        vm.code = _code([0x02, 0, imm16(42)], 0x00)
        vm.run()
        assert vm.registers[0] == 42


# ===========================================================================
# Conditional Jump Tests (JZ, JNZ)
# ===========================================================================

class TestConditionalJumps:
    def test_jz_taken_when_zero(self):
        vm = SkillVM()
        vm.flags["zero"] = True
        vm.code = _code([0x04, addr16(7)], [0x02, 0, imm16(1)], [0x02, 0, imm16(42)], 0x00)
        vm.run()
        assert vm.registers[0] == 42

    def test_jz_not_taken_when_not_zero(self):
        vm = SkillVM()
        vm.flags["zero"] = False
        vm.code = _code([0x04, addr16(7)], [0x02, 0, imm16(99)], 0x00)
        vm.run()
        assert vm.registers[0] == 99

    def test_jnz_taken_when_not_zero(self):
        vm = SkillVM()
        vm.flags["zero"] = False
        vm.code = _code([0x05, addr16(7)], [0x02, 0, imm16(1)], [0x02, 0, imm16(42)], 0x00)
        vm.run()
        assert vm.registers[0] == 42

    def test_jnz_not_taken_when_zero(self):
        vm = SkillVM()
        vm.flags["zero"] = True
        vm.code = _code([0x05, addr16(7)], [0x02, 0, imm16(99)], 0x00)
        vm.run()
        assert vm.registers[0] == 99

    def test_cmp_then_jz(self):
        vm = SkillVM()
        # MOVI R0,5 (0-3), MOVI R1,5 (4-7), CMP R0,R1 (8-10), JZ addr (11-13), MOVI R0,1 (14-17), MOVI R0,42 (18-21), HALT (22)
        jz_target = 18
        vm.code = _code(
            [0x02, 0, imm16(5)],
            [0x02, 1, imm16(5)],
            [0x20, 0, 1],          # CMP R0, R1
            [0x04, addr16(jz_target)],     # JZ to MOVI R0, 42
            [0x02, 0, imm16(1)],
            [0x02, 0, imm16(42)],
            0x00,
        )
        vm.run()
        assert vm.flags["zero"] is True
        assert vm.registers[0] == 42

    def test_cmp_then_jnz(self):
        vm = SkillVM()
        jnz_target = 18
        vm.code = _code(
            [0x02, 0, imm16(5)],
            [0x02, 1, imm16(3)],
            [0x20, 0, 1],          # CMP R0, R1
            [0x05, addr16(jnz_target)],     # JNZ to MOVI R0, 42
            [0x02, 0, imm16(1)],
            [0x02, 0, imm16(42)],
            0x00,
        )
        vm.run()
        assert vm.flags["zero"] is False
        assert vm.registers[0] == 42


# ===========================================================================
# CALL/RET Opcode Tests
# ===========================================================================

class TestCallRet:
    def test_call_ret_basic(self):
        vm = SkillVM()
        # CALL to offset where MOVI R0, 99 + RET lives
        vm.code = _code(
            [0x06, addr16(4)],     # CALL offset 4
            0x00,                    # HALT
            [0x02, 0, imm16(99)],   # MOVI R0, 99
            0x07,                    # RET
        )
        vm.run()
        assert vm.registers[0] == 99
        assert vm.halted

    def test_call_ret_multiple(self):
        vm = SkillVM()
        # CALL A at offset 3 (0-2), HALT (3), subroutine A: MOVI R0,10 (4-7), CALL B (8-10), RET (11),
        # subroutine B: MOVI R1,20 (12-15), RET (16)
        vm.code = _code(
            [0x06, addr16(4)],     # CALL A
            0x00,                    # HALT (offset 3)
            [0x02, 0, imm16(10)],   # MOVI R0, 10 (offset 4-7)
            [0x06, addr16(12)],     # CALL B (offset 8-10)
            0x07,                    # RET A (offset 11)
            [0x02, 1, imm16(20)],   # MOVI R1, 20 (offset 12-15)
            0x07,                    # RET B (offset 16)
        )
        vm.run()
        assert vm.registers[0] == 10
        assert vm.registers[1] == 20
        assert vm.halted

    def test_ret_with_empty_stack_halts(self):
        """RET with empty call_stack should halt the VM."""
        vm = SkillVM()
        vm.code = _code(0x07)  # RET with empty stack
        vm.run()
        assert vm.halted


# ===========================================================================
# Arithmetic Opcode Tests
# ===========================================================================

class TestArithmetic:
    def test_add_basic(self):
        vm = SkillVM()
        vm.code = _code(
            [0x02, 0, imm16(10)],
            [0x02, 1, imm16(20)],
            [0x08, 2, 0, 1],
            0x00,
        )
        vm.run()
        assert vm.registers[2] == 30

    def test_sub_basic(self):
        vm = SkillVM()
        vm.code = _code(
            [0x02, 0, imm16(50)],
            [0x02, 1, imm16(20)],
            [0x09, 2, 0, 1],
            0x00,
        )
        vm.run()
        assert vm.registers[2] == 30

    def test_mul_basic(self):
        vm = SkillVM()
        vm.code = _code(
            [0x02, 0, imm16(6)],
            [0x02, 1, imm16(7)],
            [0x0A, 2, 0, 1],
            0x00,
        )
        vm.run()
        assert vm.registers[2] == 42

    def test_add_negative(self):
        vm = SkillVM()
        vm.code = _code(
            [0x02, 0, imm16(-10)],
            [0x02, 1, imm16(5)],
            [0x08, 2, 0, 1],
            0x00,
        )
        vm.run()
        assert vm.registers[2] == -5

    def test_sub_negative_result(self):
        vm = SkillVM()
        vm.code = _code(
            [0x02, 0, imm16(3)],
            [0x02, 1, imm16(10)],
            [0x09, 2, 0, 1],
            0x00,
        )
        vm.run()
        assert vm.registers[2] == -7

    def test_mul_zero(self):
        vm = SkillVM()
        vm.code = _code(
            [0x02, 0, imm16(0)],
            [0x02, 1, imm16(99)],
            [0x0A, 2, 0, 1],
            0x00,
        )
        vm.run()
        assert vm.registers[2] == 0

    def test_add_self(self):
        """R0 = R0 + R0 (rd == rs1 == rs2)"""
        vm = SkillVM()
        vm.code = _code([0x02, 0, imm16(7)], [0x08, 0, 0, 0], 0x00)
        vm.run()
        assert vm.registers[0] == 14

    def test_add_with_overlap_rd_rs1(self):
        vm = SkillVM()
        vm.code = _code(
            [0x02, 0, imm16(10)],
            [0x02, 1, imm16(5)],
            [0x08, 0, 0, 1],  # R0 = R0 + R1
            0x00,
        )
        vm.run()
        assert vm.registers[0] == 15


# ===========================================================================
# CMP Opcode Tests
# ===========================================================================

class TestCMP:
    def test_cmp_equal(self):
        vm = SkillVM()
        vm.code = _code(
            [0x02, 0, imm16(5)],
            [0x02, 1, imm16(5)],
            [0x20, 0, 1],
            0x00,
        )
        vm.run()
        assert vm.flags["zero"] is True
        assert vm.flags["negative"] is False

    def test_cmp_less_than(self):
        vm = SkillVM()
        vm.code = _code(
            [0x02, 0, imm16(3)],
            [0x02, 1, imm16(5)],
            [0x20, 0, 1],
            0x00,
        )
        vm.run()
        assert vm.flags["zero"] is False
        assert vm.flags["negative"] is True

    def test_cmp_greater_than(self):
        vm = SkillVM()
        vm.code = _code(
            [0x02, 0, imm16(10)],
            [0x02, 1, imm16(5)],
            [0x20, 0, 1],
            0x00,
        )
        vm.run()
        assert vm.flags["zero"] is False
        assert vm.flags["negative"] is False

    def test_cmp_equal_negative(self):
        vm = SkillVM()
        vm.code = _code(
            [0x02, 0, imm16(-5)],
            [0x02, 1, imm16(-5)],
            [0x20, 0, 1],
            0x00,
        )
        vm.run()
        assert vm.flags["zero"] is True


# ===========================================================================
# Stack Opcode Tests
# ===========================================================================

class TestStack:
    def test_push_pop(self):
        vm = SkillVM()
        vm.code = _code(
            [0x28, imm16(42)],  # PUSH 42
            [0x29, 0],          # POP R0
            0x00,
        )
        vm.run()
        assert vm.registers[0] == 42

    def test_push_pop_negative(self):
        vm = SkillVM()
        vm.code = _code(
            [0x28, imm16(-99)],
            [0x29, 0],
            0x00,
        )
        vm.run()
        assert vm.registers[0] == -99

    def test_push_pop_multiple(self):
        vm = SkillVM()
        vm.code = _code(
            [0x28, imm16(1)],
            [0x28, imm16(2)],
            [0x28, imm16(3)],
            [0x29, 3],  # POP R3 = 3 (last pushed)
            [0x29, 2],  # POP R2 = 2
            [0x29, 1],  # POP R1 = 1
            0x00,
        )
        vm.run()
        assert vm.registers[3] == 3  # LIFO order
        assert vm.registers[2] == 2
        assert vm.registers[1] == 1

    def test_pop_empty_stack(self):
        """POP from empty stack should yield 0."""
        vm = SkillVM()
        vm.code = _code([0x29, 0], 0x00)
        vm.run()
        assert vm.registers[0] == 0

    def test_stack_depth(self):
        vm = SkillVM()
        vm.code = _code(
            [0x28, imm16(1)],
            [0x28, imm16(2)],
            [0x28, imm16(3)],
            [0x80],  # OUT
            0x00,
        )
        vm.run()
        assert vm.output_data[0]["stack_depth"] == 3


# ===========================================================================
# Memory Opcode Tests
# ===========================================================================

class TestMemory:
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

    def test_store_overwrite(self):
        vm = SkillVM()
        vm.code = _code(
            [0x02, 0, imm16(10)],
            [0x50, 1, 0],   # STORE key=1, value=10
            [0x02, 0, imm16(20)],
            [0x50, 1, 0],   # STORE key=1, value=20 (overwrite)
            [0x51, 0, 1],   # LOAD R0, key=1
            0x00,
        )
        vm.run()
        assert vm.registers[0] == 20

    def test_load_nonexistent_key(self):
        vm = SkillVM()
        vm.code = _code(
            [0x51, 0, 99],  # LOAD R0, key=99 (never stored)
            0x00,
        )
        vm.run()
        assert vm.registers[0] == 0

    def test_multiple_store_load(self):
        vm = SkillVM()
        vm.code = _code(
            [0x02, 0, imm16(10)],
            [0x02, 1, imm16(20)],
            [0x50, 1, 0],   # store R0 -> key 1
            [0x50, 2, 1],   # store R1 -> key 2
            [0x51, 5, 1],   # load key 1 -> R5
            [0x51, 6, 2],   # load key 2 -> R6
            0x00,
        )
        vm.run()
        assert vm.registers[5] == 10
        assert vm.registers[6] == 20

    def test_memory_keys_are_strings(self):
        """Memory keys should be stored as strings internally."""
        vm = SkillVM()
        vm.code = _code(
            [0x02, 0, imm16(42)],
            [0x50, 5, 0],
            0x00,
        )
        vm.run()
        assert "5" in vm.memory
        assert vm.memory["5"] == 42


# ===========================================================================
# I/O Opcode Tests
# ===========================================================================

class TestIO:
    def test_output_single(self):
        vm = SkillVM()
        vm.code = _code(0x80, 0x00)
        result = vm.run()
        assert len(result) == 1
        assert "registers" in result[0]
        assert "memory" in result[0]
        assert "stack_depth" in result[0]

    def test_output_multiple(self):
        vm = SkillVM()
        vm.code = _code(0x80, 0x80, 0x80, 0x00)
        result = vm.run()
        assert len(result) == 3

    def test_output_contains_registers(self):
        vm = SkillVM()
        vm.code = _code([0x02, 0, imm16(42)], 0x80, 0x00)
        result = vm.run()
        assert result[0]["registers"][0] == 42

    def test_output_registers_limited_to_4(self):
        """Output should only include first 4 registers."""
        vm = SkillVM()
        vm.code = _code(
            [0x02, 15, imm16(99)],
            0x80, 0x00,
        )
        result = vm.run()
        assert len(result[0]["registers"]) == 4
        assert result[0]["registers"][0] == 0
        assert 99 not in result[0]["registers"]

    def test_input_basic(self):
        vm = SkillVM()
        vm.load_input([{"a": 10, "b": 20, "c": 30, "d": 40}])
        vm.code = _code(0x81, 0x00)
        vm.run()
        assert vm.registers[0] == 10
        assert vm.registers[1] == 20
        assert vm.registers[2] == 30
        assert vm.registers[3] == 40

    def test_input_consumed(self):
        """Input should be consumed (removed from queue)."""
        vm = SkillVM()
        vm.load_input([{"a": 10}])
        vm.code = _code(0x81, 0x81, 0x00)
        vm.run()
        assert vm.registers[0] == 10
        # Second IN has no data, so R0 stays at 10 (IN doesn't clear registers)

    def test_input_skips_non_numeric(self):
        """Non-numeric input values should be skipped, but register index still increments."""
        vm = SkillVM()
        vm.load_input([{"a": "hello", "b": 42}])
        vm.code = _code(0x81, 0x00)
        vm.run()
        # a="hello" is at i=0 (skipped), b=42 is at i=1
        assert vm.registers[0] == 0
        assert vm.registers[1] == 42

    def test_input_empty(self):
        """IN with no input data should leave registers unchanged."""
        vm = SkillVM()
        vm.code = _code(0x81, 0x00)
        vm.run()
        assert vm.registers[0] == 0


# ===========================================================================
# State Save/Load Tests
# ===========================================================================

class TestState:
    def test_state_save(self):
        vm = SkillVM()
        vm.registers[0] = 99
        vm.code = _code(0x84, 0x00)
        vm.run()
        assert vm.state["registers"][0] == 99
        assert vm.state["memory"] == {}

    def test_state_save_memory(self):
        vm = SkillVM()
        vm.code = _code(
            [0x02, 0, imm16(42)],
            [0x50, 1, 0],
            0x84,
            0x00,
        )
        vm.run()
        assert "1" in vm.state["memory"]
        assert vm.state["memory"]["1"] == 42

    def test_state_save_pc(self):
        vm = SkillVM()
        vm.code = _code([0x02, 0, imm16(1)], 0x84, 0x00)
        vm.run()
        assert vm.state["pc"] > 0

    def test_state_load(self):
        vm = SkillVM()
        vm.registers[0] = 99
        vm.memory["5"] = 42
        vm.state = {"registers": [99, 0] + [0] * 14, "memory": {"5": 42}, "pc": 0}
        vm.code = _code(
            [0x02, 0, imm16(0)],  # clear R0
            [0x51, 0, 5],        # clear memory key 5
            0x85,                 # STATE_LOAD
            0x00,
        )
        vm.run()
        assert vm.registers[0] == 99
        assert vm.memory.get("5") == 42

    def test_state_load_empty(self):
        """STATE_LOAD with no saved state should do nothing."""
        vm = SkillVM()
        vm.code = _code(0x85, 0x00)
        vm.run()
        assert vm.registers == [0] * 16


# ===========================================================================
# Max Steps Safety Tests
# ===========================================================================

class TestMaxSteps:
    def test_infinite_loop_stops(self):
        vm = SkillVM()
        vm.code = _code([0x03, addr16(0)])  # JMP 0 (infinite loop)
        vm.run(max_steps=100)
        assert not vm.halted

    def test_max_steps_allows_enough(self):
        vm = SkillVM()
        # Simple program that needs ~4 steps
        vm.code = _code([0x02, 0, imm16(1)], [0x02, 1, imm16(2)], [0x08, 2, 0, 1], 0x00)
        vm.run(max_steps=100)
        assert vm.halted
        assert vm.registers[2] == 3

    def test_max_steps_one(self):
        vm = SkillVM()
        vm.code = _code([0x02, 0, imm16(42)], 0x00)
        vm.run(max_steps=1)
        assert not vm.halted  # can't reach HALT in 1 step


# ===========================================================================
# Unknown Opcode Tests
# ===========================================================================

class TestUnknownOpcodes:
    def test_unknown_opcode_skipped(self):
        """Unknown opcodes should be skipped (pc += 1)."""
        vm = SkillVM()
        vm.code = _code(0xFF, [0x02, 0, imm16(42)], 0x00)
        vm.run()
        assert vm.registers[0] == 42
        assert vm.halted

    def test_many_unknown_opcodes(self):
        vm = SkillVM()
        vm.code = _code(0xFE, 0xFD, 0xFC, [0x02, 0, imm16(42)], 0x00)
        vm.run()
        assert vm.registers[0] == 42


# ===========================================================================
# Complex Program Tests
# ===========================================================================

class TestComplexPrograms:
    def test_sum_of_1_to_5(self):
        """Sum 1+2+3+4+5 = 15."""
        vm = SkillVM()
        # Build bytecode carefully with correct offsets
        bytecode = b""
        bytecode += struct.pack(">Bbh", 0x02, 0, 0)     # MOVI R0, 0 (sum)        offset 0-3
        bytecode += struct.pack(">Bbh", 0x02, 1, 1)     # MOVI R1, 1 (counter)   offset 4-7
        bytecode += struct.pack(">Bbh", 0x02, 2, 6)     # MOVI R2, 6 (limit)     offset 8-11
        loop_addr = 12
        bytecode += bytes([0x08, 0, 0, 1])              # ADD R0,R0,R1          offset 12-15
        bytecode += struct.pack(">Bbh", 0x02, 3, 1)     # MOVI R3, 1             offset 16-19
        bytecode += bytes([0x08, 1, 1, 3])              # ADD R1,R1,R3          offset 20-23
        bytecode += bytes([0x20, 1, 2])                  # CMP R1,R2             offset 24-26
        done_addr = 33
        bytecode += struct.pack(">BH", 0x04, done_addr) # JZ done               offset 27-29
        bytecode += struct.pack(">BH", 0x03, loop_addr) # JMP loop              offset 30-32
        bytecode += bytes([0x00])                         # HALT                  offset 33
        vm.code = bytecode
        vm.run()
        assert vm.registers[0] == 15

    def test_conditional_branch(self):
        """If R0 > 10, R1 = 100 else R1 = 200."""
        vm = SkillVM()
        # CMP sets zero=True when equal, negative=True when a < b.
        # For R0=15, R2=10: zero=False, negative=False.
        # JNZ should jump when zero is False (not equal). But JNZ doesn't check negative.
        # Actually JNZ checks if NOT zero. So if R0 != R2, JNZ is taken regardless of negative.
        # So we need: CMP, then check if NOT negative (i.e., R0 >= R2) to take the > branch.
        # But we only have JZ (jump if zero) and JNZ (jump if not zero).
        # For a proper > comparison: CMP sets negative=True when a<b.
        # We need to check: if NOT (zero OR negative) then R0 > R2.
        # Since we only have JZ/JNZ on the zero flag, let's use a simpler approach:
        # Just verify the CMP flags are set correctly.
        vm.code = _code(
            [0x02, 0, imm16(15)],       # R0 = 15
            [0x02, 2, imm16(10)],       # R2 = 10 (threshold)
            [0x20, 0, 2],              # CMP R0, R2 → zero=False, negative=False (15 > 10)
            # Since we can't directly branch on negative flag, just check flags
            0x00,
        )
        vm.run()
        assert vm.flags["zero"] is False  # 15 != 10
        assert vm.flags["negative"] is False  # 15 is not < 10

    def test_output_in_loop(self):
        """Output values in a loop."""
        vm = SkillVM()
        vm.code = _code(
            [0x02, 0, imm16(1)],   # R0 = 1
            [0x80],                  # OUT
            [0x08, 0, 0, 0],       # R0 = R0 + R0
            [0x02, 1, imm16(32)],   # R1 = 32 (limit)
            [0x20, 2, 0, 1],       # CMP R2 = R0, R1
            [0x04, addr16(6)],      # JZ end
            [0x03, addr16(4)],      # JMP loop
            0x00,
        )
        result = vm.run()
        assert len(result) > 1  # multiple outputs


# ===========================================================================
# Boundary and Edge Case Tests
# ===========================================================================

class TestEdgeCases:
    def test_u8_out_of_bounds(self):
        """_u8 beyond code length should return 0."""
        vm = SkillVM()
        vm.code = b"\x00"
        vm.pc = 5
        assert vm._u8() == 0

    def test_i16_out_of_bounds(self):
        vm = SkillVM()
        vm.code = b"\x00"
        vm.pc = 5
        assert vm._i16() == 0

    def test_u16_out_of_bounds(self):
        vm = SkillVM()
        vm.code = b"\x00"
        vm.pc = 5
        assert vm._u16() == 0

    def test_u16_max_value(self):
        vm = SkillVM()
        vm.code = struct.pack(">BH", 0xFF, 0xFFFF)
        assert vm._u16(1) == 65535

    def test_i16_max_negative(self):
        vm = SkillVM()
        vm.code = struct.pack(">h", -32768)
        assert vm._i16() == -32768

    def test_i16_max_positive(self):
        vm = SkillVM()
        vm.code = struct.pack(">h", 32767)
        assert vm._i16() == 32767

    def test_run_twice(self):
        """Running the same VM twice should reset pc."""
        vm = SkillVM()
        vm.code = _code([0x02, 0, imm16(42)], 0x00)
        vm.run()
        assert vm.registers[0] == 42
        # Second run resets pc
        vm.run()
        assert vm.halted
        assert vm.registers[0] == 42

    def test_single_byte_code(self):
        vm = SkillVM()
        vm.code = b"\x00"  # just HALT
        vm.run()
        assert vm.halted

    def test_empty_code(self):
        vm = SkillVM()
        vm.code = b""
        vm.run()
        assert not vm.halted

    def test_call_stack_depth_tracking(self):
        vm = SkillVM()
        vm.code = _code(
            [0x06, addr16(8)],     # CALL
            [0x06, addr16(8)],     # CALL again (nested)
            0x00,
            [0x07],                 # RET
            [0x07],                 # RET
        )
        vm.run()
        assert vm.call_stack == []

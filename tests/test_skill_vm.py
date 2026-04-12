"""Tests for the SkillVM bytecode interpreter — comprehensive opcode coverage."""
import pytest
import struct
import tempfile
import os
import json

from conftest import make_code, imm16, addr16


class TestSkillVMInit:
    def test_default_state(self, fresh_vm):
        vm = fresh_vm
        assert len(vm.registers) == 16
        assert all(r == 0 for r in vm.registers)
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

    def test_config_init(self):
        from skill_vm import SkillVM
        vm = SkillVM(config={"key": "value", "nested": {"a": 1}})
        assert vm.config["key"] == "value"
        assert vm.config["nested"]["a"] == 1


class TestHalt:
    def test_halt(self, fresh_vm):
        vm = fresh_vm
        vm.code = make_code(0x00)
        vm.run()
        assert vm.halted

    def test_halt_stops_execution(self, fresh_vm):
        vm = fresh_vm
        vm.code = make_code(0x00, 0x02, 0, imm16(99))  # HALT then MOVI
        vm.run()
        assert vm.halted
        assert vm.registers[0] == 0  # MOVI should not execute


class TestMovi:
    def test_movi_positive(self, fresh_vm):
        vm = fresh_vm
        vm.code = make_code([0x02, 0, imm16(42)], 0x00)
        vm.run()
        assert vm.registers[0] == 42

    def test_movi_negative(self, fresh_vm):
        vm = fresh_vm
        vm.code = make_code([0x02, 0, imm16(-100)], 0x00)
        vm.run()
        assert vm.registers[0] == -100

    def test_movi_zero(self, fresh_vm):
        vm = fresh_vm
        vm.code = make_code([0x02, 0, imm16(0)], 0x00)
        vm.run()
        assert vm.registers[0] == 0

    def test_movi_different_registers(self, fresh_vm):
        vm = fresh_vm
        vm.code = make_code(
            [0x02, 5, imm16(111)],
            [0x02, 15, imm16(222)],
            0x00,
        )
        vm.run()
        assert vm.registers[5] == 111
        assert vm.registers[15] == 222

    def test_movi_max_value(self, fresh_vm):
        vm = fresh_vm
        vm.code = make_code([0x02, 0, imm16(32767)], 0x00)
        vm.run()
        assert vm.registers[0] == 32767

    def test_movi_min_value(self, fresh_vm):
        vm = fresh_vm
        vm.code = make_code([0x02, 0, imm16(-32768)], 0x00)
        vm.run()
        assert vm.registers[0] == -32768


class TestJmp:
    def test_jmp_forward(self, fresh_vm):
        vm = fresh_vm
        # JMP over MOVI to HALT
        # offset 0: JMP (3 bytes)
        # offset 3: MOVI (4 bytes, skipped)
        # offset 7: HALT (1 byte, skipped)
        # offset 8: MOVI R1, 42 (4 bytes)
        # offset 12: HALT
        vm.code = make_code(
            [0x03, addr16(8)],         # offset 0: JMP 8
            [0x02, 0, imm16(99)],      # offset 3: MOVI R0, 99 (skipped)
            0x00,                       # offset 7: HALT (skipped)
            [0x02, 1, imm16(42)],      # offset 8: MOVI R1, 42
            0x00,                       # offset 12: HALT
        )
        vm.run()
        assert vm.registers[0] == 0  # skipped
        assert vm.registers[1] == 42

    def test_jmp_backward_creates_loop(self, fresh_vm):
        vm = fresh_vm
        # Accumulate R2 using a backward jump
        # offset 0: MOVI R0, 1 (4 bytes)
        # offset 4: ADD R2, R2, R0 (4 bytes) — R2 += 1
        # offset 8: JMP 4 (3 bytes) — loop back to ADD
        vm.code = make_code(
            [0x02, 0, imm16(1)],   # offset 0: R0 = 1
            [0x08, 2, 2, 0],       # offset 4: R2 = R2 + R0
            [0x03, addr16(4)],     # offset 8: JMP 4
        )
        vm.run(max_steps=100)
        # After many iterations, R2 should be large
        assert vm.registers[2] >= 10
        assert not vm.halted


class TestConditionalJumps:
    def test_jz_taken(self, fresh_vm):
        vm = fresh_vm
        vm.code = make_code(
            [0x02, 0, imm16(10)],    # offset 0: R0 = 10 (4 bytes)
            [0x02, 1, imm16(10)],    # offset 4: R1 = 10 (4 bytes)
            [0x20, 0, 1],            # offset 8: CMP R0, R1 → zero=True (3 bytes)
            [0x04, addr16(17)],      # offset 11: JZ 17 (3 bytes)
            [0x02, 2, imm16(99)],    # offset 14: R2 = 99 (4 bytes, skipped)
            0x00,                      # offset 18: HALT (skipped)
        )
        vm.run(max_steps=10)
        assert vm.registers[2] == 0  # not reached

    def test_jz_not_taken(self, fresh_vm):
        vm = fresh_vm
        vm.code = make_code(
            [0x02, 0, imm16(10)],    # offset 0: R0 = 10
            [0x02, 1, imm16(20)],    # offset 4: R1 = 20
            [0x20, 0, 1],            # offset 8: CMP → zero=False
            [0x04, addr16(100)],    # offset 11: JZ 100 (not taken)
            [0x02, 2, imm16(55)],    # offset 14: R2 = 55
            0x00,                      # offset 18: HALT
        )
        vm.run(max_steps=10)
        assert vm.registers[2] == 55

    def test_jnz_taken(self, fresh_vm):
        vm = fresh_vm
        vm.code = make_code(
            [0x02, 0, imm16(10)],    # offset 0
            [0x02, 1, imm16(20)],    # offset 4
            [0x20, 0, 1],            # offset 8: CMP → zero=False
            [0x05, addr16(17)],     # offset 11: JNZ 17 (taken)
            [0x02, 2, imm16(99)],    # offset 14: skipped
            0x00,                      # offset 18
        )
        vm.run(max_steps=10)
        assert vm.registers[2] == 0

    def test_jnz_not_taken(self, fresh_vm):
        vm = fresh_vm
        vm.code = make_code(
            [0x02, 0, imm16(10)],    # offset 0
            [0x02, 1, imm16(10)],    # offset 4
            [0x20, 0, 1],            # offset 8: CMP → zero=True
            [0x05, addr16(100)],    # offset 11: JNZ (not taken)
            [0x02, 2, imm16(77)],    # offset 14
            0x00,                      # offset 18
        )
        vm.run(max_steps=10)
        assert vm.registers[2] == 77


class TestArithmetic:
    def test_add(self, fresh_vm):
        vm = fresh_vm
        vm.code = make_code(
            [0x02, 0, imm16(10)],
            [0x02, 1, imm16(20)],
            [0x08, 2, 0, 1],
            0x00,
        )
        vm.run()
        assert vm.registers[2] == 30

    def test_add_negative(self, fresh_vm):
        vm = fresh_vm
        vm.code = make_code(
            [0x02, 0, imm16(-10)],
            [0x02, 1, imm16(-20)],
            [0x08, 2, 0, 1],
            0x00,
        )
        vm.run()
        assert vm.registers[2] == -30

    def test_add_zero(self, fresh_vm):
        vm = fresh_vm
        vm.code = make_code(
            [0x02, 0, imm16(0)],
            [0x02, 1, imm16(0)],
            [0x08, 2, 0, 1],
            0x00,
        )
        vm.run()
        assert vm.registers[2] == 0

    def test_sub(self, fresh_vm):
        vm = fresh_vm
        vm.code = make_code(
            [0x02, 0, imm16(50)],
            [0x02, 1, imm16(20)],
            [0x09, 2, 0, 1],
            0x00,
        )
        vm.run()
        assert vm.registers[2] == 30

    def test_sub_negative_result(self, fresh_vm):
        vm = fresh_vm
        vm.code = make_code(
            [0x02, 0, imm16(10)],
            [0x02, 1, imm16(20)],
            [0x09, 2, 0, 1],
            0x00,
        )
        vm.run()
        assert vm.registers[2] == -10

    def test_mul(self, fresh_vm):
        vm = fresh_vm
        vm.code = make_code(
            [0x02, 0, imm16(6)],
            [0x02, 1, imm16(7)],
            [0x0A, 2, 0, 1],
            0x00,
        )
        vm.run()
        assert vm.registers[2] == 42

    def test_mul_by_zero(self, fresh_vm):
        vm = fresh_vm
        vm.code = make_code(
            [0x02, 0, imm16(100)],
            [0x02, 1, imm16(0)],
            [0x0A, 2, 0, 1],
            0x00,
        )
        vm.run()
        assert vm.registers[2] == 0

    def test_mul_negative(self, fresh_vm):
        vm = fresh_vm
        vm.code = make_code(
            [0x02, 0, imm16(-5)],
            [0x02, 1, imm16(3)],
            [0x0A, 2, 0, 1],
            0x00,
        )
        vm.run()
        assert vm.registers[2] == -15

    def test_add_to_self(self, fresh_vm):
        vm = fresh_vm
        vm.code = make_code(
            [0x02, 0, imm16(10)],
            [0x08, 0, 0, 0],  # ADD R0, R0, R0
            0x00,
        )
        vm.run()
        assert vm.registers[0] == 20


class TestCmp:
    def test_equal(self, fresh_vm):
        vm = fresh_vm
        vm.code = make_code(
            [0x02, 0, imm16(42)],
            [0x02, 1, imm16(42)],
            [0x20, 0, 1],
            0x00,
        )
        vm.run()
        assert vm.flags["zero"] is True
        assert vm.flags["negative"] is False

    def test_less_than(self, fresh_vm):
        vm = fresh_vm
        vm.code = make_code(
            [0x02, 0, imm16(10)],
            [0x02, 1, imm16(20)],
            [0x20, 0, 1],
            0x00,
        )
        vm.run()
        assert vm.flags["zero"] is False
        assert vm.flags["negative"] is True

    def test_greater_than(self, fresh_vm):
        vm = fresh_vm
        vm.code = make_code(
            [0x02, 0, imm16(30)],
            [0x02, 1, imm16(20)],
            [0x20, 0, 1],
            0x00,
        )
        vm.run()
        assert vm.flags["zero"] is False
        assert vm.flags["negative"] is False


class TestStack:
    def test_push_pop(self, fresh_vm):
        vm = fresh_vm
        vm.code = make_code(
            [0x28, imm16(42)],
            [0x29, 0],
            0x00,
        )
        vm.run()
        assert vm.registers[0] == 42

    def test_push_multiple_pop_lifo(self, fresh_vm):
        vm = fresh_vm
        vm.code = make_code(
            [0x28, imm16(10)],
            [0x28, imm16(20)],
            [0x28, imm16(30)],
            [0x29, 0],  # pop 30
            [0x29, 1],  # pop 20
            [0x29, 2],  # pop 10
            0x00,
        )
        vm.run()
        assert vm.registers[0] == 30
        assert vm.registers[1] == 20
        assert vm.registers[2] == 10

    def test_pop_empty_stack(self, fresh_vm):
        vm = fresh_vm
        vm.code = make_code([0x29, 0], 0x00)
        vm.run()
        assert vm.registers[0] == 0  # default 0 for empty pop

    def test_push_negative(self, fresh_vm):
        vm = fresh_vm
        vm.code = make_code([0x28, imm16(-77)], [0x29, 0], 0x00)
        vm.run()
        assert vm.registers[0] == -77


class TestCallRet:
    def test_call_ret_basic(self, fresh_vm):
        vm = fresh_vm
        # offset 0: CALL 4 (3 bytes: opcode + addr16)
        # offset 3: HALT (1 byte)
        # offset 4: MOVI R0, 99 (4 bytes)
        # offset 8: RET (1 byte)
        vm.code = make_code(
            [0x06, addr16(4)],      # CALL 4
            0x00,                     # HALT
            [0x02, 0, imm16(99)],   # MOVI R0, 99
            0x07,                     # RET
        )
        vm.run()
        assert vm.registers[0] == 99
        assert vm.halted

    def test_nested_call(self, fresh_vm):
        vm = fresh_vm
        # offset 0: CALL func1 (3 bytes)
        # offset 3: HALT
        # func1 at offset 4: MOVI R0, 10 (4 bytes)
        # offset 8: CALL func2 (3 bytes)
        # offset 11: RET (1 byte)
        # func2 at offset 12: MOVI R1, 20 (4 bytes)
        # offset 16: RET (1 byte)
        vm.code = make_code(
            [0x06, addr16(4)],      # CALL func1 at offset 4
            0x00,                     # HALT
            [0x02, 0, imm16(10)],   # func1: MOVI R0, 10
            [0x06, addr16(12)],     # CALL func2 at offset 12
            0x07,                     # RET
            [0x02, 1, imm16(20)],   # func2: MOVI R1, 20
            0x07,                     # RET
        )
        vm.run()
        assert vm.registers[0] == 10
        assert vm.registers[1] == 20
        assert vm.halted

    def test_ret_empty_stack_halts(self, fresh_vm):
        vm = fresh_vm
        vm.code = make_code(0x07)  # RET with no call
        vm.run()
        assert vm.halted


class TestMemory:
    def test_store_load(self, fresh_vm):
        vm = fresh_vm
        vm.code = make_code(
            [0x02, 0, imm16(77)],
            [0x50, 1, 0],        # STORE key=1, value=R0
            [0x02, 0, imm16(0)],  # clear R0
            [0x51, 0, 1],        # LOAD R0, key=1
            0x00,
        )
        vm.run()
        assert vm.registers[0] == 77

    def test_load_nonexistent_key(self, fresh_vm):
        vm = fresh_vm
        vm.code = make_code([0x51, 0, 99], 0x00)  # LOAD R0, key=99 (doesn't exist)
        vm.run()
        assert vm.registers[0] == 0

    def test_store_overwrite(self, fresh_vm):
        vm = fresh_vm
        vm.code = make_code(
            [0x02, 0, imm16(10)],
            [0x50, 1, 0],
            [0x02, 0, imm16(20)],
            [0x50, 1, 0],
            [0x51, 0, 1],
            0x00,
        )
        vm.run()
        assert vm.registers[0] == 20

    def test_multiple_keys(self, fresh_vm):
        vm = fresh_vm
        vm.code = make_code(
            [0x02, 0, imm16(100)],  # R0 = 100
            [0x02, 1, imm16(200)],  # R1 = 200
            [0x50, 10, 0],          # STORE key=10, R0
            [0x50, 20, 1],          # STORE key=20, R1
            [0x51, 2, 10],          # LOAD R2, key=10
            [0x51, 3, 20],          # LOAD R3, key=20
            0x00,
        )
        vm.run()
        assert vm.registers[2] == 100
        assert vm.registers[3] == 200


class TestInputOutput:
    def test_output_creates_record(self, fresh_vm):
        vm = fresh_vm
        vm.code = make_code(0x80, 0x00)
        result = vm.run()
        assert len(result) == 1
        assert "registers" in result[0]
        assert "memory" in result[0]
        assert "stack_depth" in result[0]

    def test_output_captures_registers(self, fresh_vm):
        vm = fresh_vm
        vm.code = make_code(
            [0x02, 0, imm16(10)],
            [0x02, 1, imm16(20)],
            [0x02, 2, imm16(30)],
            [0x02, 3, imm16(40)],
            0x80,
            0x00,
        )
        result = vm.run()
        assert result[0]["registers"] == [10, 20, 30, 40]

    def test_output_captures_memory(self, fresh_vm):
        vm = fresh_vm
        vm.code = make_code(
            [0x02, 0, imm16(42)],
            [0x50, 5, 0],
            0x80,
            0x00,
        )
        result = vm.run()
        assert "5" in result[0]["memory"]
        assert result[0]["memory"]["5"] == 42

    def test_output_stack_depth(self, fresh_vm):
        vm = fresh_vm
        vm.code = make_code(
            [0x28, imm16(1)],
            [0x28, imm16(2)],
            [0x28, imm16(3)],
            0x80,
            0x00,
        )
        result = vm.run()
        assert result[0]["stack_depth"] == 3

    def test_input_loads_values(self, fresh_vm):
        vm = fresh_vm
        vm.load_input([{"a": 10, "b": 20, "c": 30}])
        vm.code = make_code(0x81, 0x00)
        vm.run()
        assert vm.registers[0] == 10
        assert vm.registers[1] == 20
        assert vm.registers[2] == 30

    def test_input_skips_non_numeric(self, fresh_vm):
        """Non-numeric values are skipped; only numeric values go to registers."""
        vm = fresh_vm
        vm.load_input([{"a": "text", "b": 42}])
        vm.code = make_code(0x81, 0x00)
        vm.run()
        # 'text' at index 0 is skipped (not numeric), 42 at index 1 goes to R1
        assert vm.registers[0] == 0  # skipped
        assert vm.registers[1] == 42

    def test_input_consumes_sequentially(self, fresh_vm):
        """Multiple IN instructions consume input FIFO."""
        vm = fresh_vm
        vm.load_input([{"v": 10}, {"v": 20}])
        vm.code = make_code(
            0x81,                     # IN: loads first input → R0=10
            [0x08, 5, 0, 0],          # R5 = R0 + R0 = 20
            0x81,                     # IN: loads second input → R0=20
            0x00,
        )
        vm.run()
        assert vm.registers[5] == 20  # 10+10 saved to R5
        assert vm.registers[0] == 20  # second input

    def test_input_empty(self, fresh_vm):
        vm = fresh_vm
        vm.load_input([])
        vm.code = make_code(0x81, 0x00)
        vm.run()
        assert vm.registers[0] == 0  # no change

    def test_multiple_outputs(self, fresh_vm):
        vm = fresh_vm
        vm.code = make_code(0x80, 0x80, 0x80, 0x00)
        result = vm.run()
        assert len(result) == 3


class TestStateSaveLoad:
    def test_state_save(self, fresh_vm):
        vm = fresh_vm
        vm.code = make_code(
            [0x02, 0, imm16(99)],
            0x84,
            0x00,
        )
        vm.run()
        assert vm.state["registers"][0] == 99

    def test_state_save_includes_memory(self, fresh_vm):
        vm = fresh_vm
        vm.code = make_code(
            [0x02, 0, imm16(42)],
            [0x50, 1, 0],
            0x84,
            0x00,
        )
        vm.run()
        assert vm.state["memory"]["1"] == 42

    def test_state_load(self, fresh_vm):
        vm = fresh_vm
        vm.code = make_code(
            [0x02, 0, imm16(50)],
            [0x50, 1, 0],
            0x84,            # save state
            [0x02, 0, imm16(0)],  # clear R0
            0x85,            # load state (restores R0=50, memory)
            [0x51, 2, 1],    # LOAD R2, key=1
            0x00,
        )
        vm.run()
        assert vm.registers[0] == 50  # restored
        assert vm.registers[2] == 50  # loaded from restored memory

    def test_state_load_empty(self, fresh_vm):
        vm = fresh_vm
        vm.code = make_code(0x85, 0x00)  # LOAD with no prior SAVE
        vm.run()
        # Should not crash


class TestMaxSteps:
    def test_max_steps_prevents_infinite_loop(self, fresh_vm):
        vm = fresh_vm
        vm.code = make_code([0x03, addr16(0)])  # JMP 0 (infinite)
        vm.run(max_steps=100)
        assert not vm.halted

    def test_max_steps_at_exact_count(self, fresh_vm):
        vm = fresh_vm
        vm.code = make_code([0x03, addr16(0)])
        vm.run(max_steps=50)
        assert not vm.halted

    def test_run_returns_output_regardless_of_halt(self, fresh_vm):
        vm = fresh_vm
        vm.code = make_code(0x80, [0x03, addr16(1)])  # OUT then loop
        result = vm.run(max_steps=5)
        assert len(result) == 1


class TestLoadBytecode:
    def test_load_bytecode_from_file(self, fresh_vm, tmp_bytecode_dir):
        vm = fresh_vm
        bc_file = tmp_bytecode_dir / "test.fluxbc"
        bc_file.write_bytes(make_code([0x02, 0, imm16(123)], 0x00))
        vm.load_bytecode(str(bc_file))
        vm.run()
        assert vm.registers[0] == 123

    def test_load_input_method(self, fresh_vm):
        vm = fresh_vm
        vm.load_input([{"x": 1}, {"y": 2}])
        assert len(vm.input_data) == 2

    def test_load_config_method(self, fresh_vm):
        vm = fresh_vm
        vm.load_config({"max_thoughts": 100})
        assert vm.config["max_thoughts"] == 100


class TestUnknownOpcode:
    def test_unknown_opcode_skipped(self, fresh_vm):
        vm = fresh_vm
        vm.code = make_code(0xFF, [0x02, 0, imm16(42)], 0x00)
        vm.run()
        assert vm.registers[0] == 42  # should still work, unknown just skips

    def test_many_unknown_opcodes(self, fresh_vm):
        vm = fresh_vm
        vm.code = make_code(0xFE, 0xFD, 0xFC, [0x02, 0, imm16(7)], 0x00)
        vm.run()
        assert vm.registers[0] == 7


class TestBoundaryConditions:
    def test_out_of_bounds_read(self, fresh_vm):
        vm = fresh_vm
        vm.code = make_code([0x02, 0, imm16(5)], [0x08, 1, 0, 1], 0x00)
        vm.run()
        # R1 = R0 + R1 = 5 + 0 = 5
        assert vm.registers[1] == 5

    def test_pc_at_end_of_code(self, fresh_vm):
        vm = fresh_vm
        vm.code = make_code(0x02)  # partial MOVI (only opcode, no operands)
        vm.run(max_steps=5)
        # Should not crash, just stop


class TestComplexPrograms:
    def test_countdown_loop(self, fresh_vm):
        """Count from 10 to 0, accumulate in R1."""
        vm = fresh_vm
        # R0 = 10 (counter), R1 = 0 (accumulator)
        # Loop: R1 += R0, R0 -= 1, if R0 != 0 goto loop
        # offset 0:  MOVI R0, 10     (4 bytes)
        # offset 4:  MOVI R1, 0      (4 bytes)
        # offset 8:  ADD R1, R1, R0  (4 bytes) — R1 += R0
        # offset 12: MOVI R2, 1      (4 bytes)
        # offset 16: SUB R0, R0, R2  (4 bytes) — R0 -= 1
        # offset 20: MOVI R2, 0      (4 bytes)
        # offset 24: CMP R0, R2      (3 bytes)
        # offset 27: JNZ 8           (3 bytes)
        # offset 30: HALT            (1 byte)
        vm.code = make_code(
            [0x02, 0, imm16(10)],   # R0 = 10
            [0x02, 1, imm16(0)],    # R1 = 0
            # loop at 8:
            [0x08, 1, 1, 0],        # R1 = R1 + R0
            [0x02, 2, imm16(1)],    # R2 = 1
            [0x09, 0, 0, 2],        # R0 = R0 - 1
            [0x02, 2, imm16(0)],    # R2 = 0
            [0x20, 0, 2],           # CMP R0, R2
            [0x05, addr16(8)],      # JNZ loop
            0x00,
        )
        vm.run(max_steps=200)
        # Sum 1+2+...+10 = 55
        assert vm.registers[1] == 55

    def test_call_doubles_value(self, fresh_vm):
        """Call a function that doubles R0."""
        vm = fresh_vm
        # offset 0:  MOVI R0, 3      (4 bytes)
        # offset 4:  MOVI R1, 4      (4 bytes)
        # offset 8:  CALL double_r0  (3 bytes) → jumps to offset 14
        # offset 11: ADD R2, R0, R0  (4 bytes)
        # offset 15: HALT            (1 byte)
        # double_r0 at offset 16:
        # offset 16: MOVI R2, 0      (4 bytes)
        # offset 20: ADD R0, R0, R0  (4 bytes)
        # offset 24: RET             (1 byte)
        vm.code = make_code(
            [0x02, 0, imm16(3)],    # R0 = 3
            [0x02, 1, imm16(4)],    # R1 = 4
            [0x06, addr16(16)],     # CALL double_r0 at 16
            [0x08, 2, 0, 0],        # R2 = R0 + R0
            0x00,
            [0x02, 2, imm16(0)],    # temp = 0
            [0x08, 0, 0, 0],        # R0 = R0 + R0 (double)
            0x07,                     # RET
        )
        vm.run()
        assert vm.registers[0] == 6   # 3 doubled
        assert vm.registers[2] == 12  # 6 + 6

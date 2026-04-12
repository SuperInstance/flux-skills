"""Tests for conformance testing framework."""
import pytest
import subprocess
import struct
import sys
import os
import json
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "runtime"))

from conformance import TESTS, movi, add, sub, mul, push, pop, store, load, out, halt, check_output


class TestConformanceHelpers:
    def test_movi(self):
        code = movi(0, 42)
        assert len(code) == 4
        assert code[0] == 0x02
        assert code[1] == 0

    def test_add(self):
        code = add(0, 1, 2)
        assert code == bytes([0x08, 0, 1, 2])

    def test_sub(self):
        code = sub(0, 1, 2)
        assert code == bytes([0x09, 0, 1, 2])

    def test_mul(self):
        code = mul(0, 1, 2)
        assert code == bytes([0x0A, 0, 1, 2])

    def test_push(self):
        code = push(42)
        assert len(code) == 3
        assert code[0] == 0x28

    def test_pop(self):
        code = pop(0)
        assert code == bytes([0x29, 0])

    def test_store(self):
        code = store(1, 0)
        assert code == bytes([0x50, 1, 0])

    def test_load(self):
        code = load(0, 1)
        assert code == bytes([0x51, 0, 1])

    def test_out(self):
        assert out() == bytes([0x80])

    def test_halt(self):
        assert halt() == bytes([0x00])


class TestConformanceTests:
    """Verify each conformance test case produces correct bytecode."""

    def test_movi_halt_test(self):
        test = TESTS[0]
        assert test["name"] == "movi_halt"
        code = test["code"]
        assert len(code) == 5  # 4 bytes MOVI + 1 byte HALT
        assert test["expect_r0"] == 42

    def test_add_basic_test(self):
        test = TESTS[1]
        assert test["name"] == "add_basic"
        assert test["expect_r2"] == 30

    def test_sub_basic_test(self):
        test = TESTS[2]
        assert test["name"] == "sub_basic"
        assert test["expect_r2"] == 30

    def test_mul_basic_test(self):
        test = TESTS[3]
        assert test["name"] == "mul_basic"
        assert test["expect_r2"] == 42

    def test_push_pop_test(self):
        test = TESTS[4]
        assert test["name"] == "push_pop"
        assert test["expect_r3"] == 99

    def test_store_load_test(self):
        test = TESTS[5]
        assert test["name"] == "store_load"
        assert test["expect_r3"] == 77

    def test_negative_immediate_test(self):
        test = TESTS[6]
        assert test["name"] == "negative_immediate"
        assert test["expect_r0"] == -5

    def test_all_tests_have_required_fields(self):
        for test in TESTS:
            assert "name" in test
            assert "desc" in test
            assert "code" in test
            assert isinstance(test["code"], bytes)
            # At least one expect_* field
            expect_keys = [k for k in test if k.startswith("expect_")]
            assert len(expect_keys) >= 1, f"Test {test['name']} has no expect_* fields"


class TestCheckOutput:
    def test_check_output_matching_json(self):
        output = '{"r0": 42}'
        test = {"expect_r0": 42}
        ok, msg = check_output(output, test)
        assert ok is True

    def test_check_output_mismatching(self):
        output = '{"r0": 99}'
        test = {"expect_r0": 42}
        ok, msg = check_output(output, test)
        assert ok is False
        assert "99" in msg
        assert "42" in msg

    def test_check_output_no_json(self):
        output = "some plain text"
        test = {"expect_r0": 42}
        ok, msg = check_output(output, test)
        assert ok is True  # "no JSON to check" → True

    def test_check_output_empty(self):
        ok, msg = check_output("", {})
        assert ok is True


class TestConformanceBytecodeWithVM:
    """Run conformance test bytecode through the Python VM and verify."""
    from conftest import make_code, imm16

    def test_movi_halt_produces_correct_result(self):
        from skill_vm import SkillVM
        test = TESTS[0]
        vm = SkillVM()
        vm.code = test["code"]
        vm.run()
        assert vm.registers[0] == test["expect_r0"]

    def test_add_basic_produces_correct_result(self):
        from skill_vm import SkillVM
        test = TESTS[1]
        vm = SkillVM()
        vm.code = test["code"]
        vm.run()
        assert vm.registers[2] == test["expect_r2"]

    def test_sub_basic_produces_correct_result(self):
        from skill_vm import SkillVM
        test = TESTS[2]
        vm = SkillVM()
        vm.code = test["code"]
        vm.run()
        assert vm.registers[2] == test["expect_r2"]

    def test_mul_basic_produces_correct_result(self):
        from skill_vm import SkillVM
        test = TESTS[3]
        vm = SkillVM()
        vm.code = test["code"]
        vm.run()
        assert vm.registers[2] == test["expect_r2"]

    def test_push_pop_produces_correct_result(self):
        from skill_vm import SkillVM
        test = TESTS[4]
        vm = SkillVM()
        vm.code = test["code"]
        vm.run()
        assert vm.registers[3] == test["expect_r3"]

    def test_store_load_produces_correct_result(self):
        from skill_vm import SkillVM
        test = TESTS[5]
        vm = SkillVM()
        vm.code = test["code"]
        vm.run()
        assert vm.registers[3] == test["expect_r3"]

    def test_negative_immediate_produces_correct_result(self):
        from skill_vm import SkillVM
        test = TESTS[6]
        vm = SkillVM()
        vm.code = test["code"]
        vm.run()
        assert vm.registers[0] == test["expect_r0"]

    def test_all_conformance_tests_pass_python_vm(self):
        from skill_vm import SkillVM
        for test in TESTS:
            vm = SkillVM()
            vm.code = test["code"]
            vm.run()
            for key, expected in test.items():
                if key.startswith("expect_"):
                    reg_idx = int(key.replace("expect_r", ""))
                    assert vm.registers[reg_idx] == expected, \
                        f"Test {test['name']}: R{reg_idx} = {vm.registers[reg_idx]}, expected {expected}"

#!/usr/bin/env python3
"""
FLUX Skill VM — lightweight runtime for executing FLUX skills.
"""

import json
import struct
from typing import Any


class SkillVM:
    def __init__(self, config: dict | None = None):
        self.registers = [0] * 16
        self.stack: list[int] = []
        self.memory: dict[str, Any] = {}
        self.flags = {"zero": False, "negative": False}
        self.pc = 0
        self.code = b""
        self.config = config or {}
        self.input_data: list[dict] = []
        self.output_data: list[dict] = []
        self.state: dict[str, Any] = {}
        self.halted = False
        self.call_stack: list[int] = []

    def load_bytecode(self, path: str):
        with open(path, "rb") as f:
            self.code = f.read()

    def load_input(self, data: list[dict]):
        self.input_data = list(data)

    def load_config(self, config: dict):
        self.config = config

    def run(self, max_steps: int = 10000) -> list[dict]:
        self.pc = 0
        self.halted = False
        steps = 0
        while not self.halted and self.pc < len(self.code) and steps < max_steps:
            self._step()
            steps += 1
        return self.output_data

    def _u8(self, offset: int = 0) -> int:
        pos = self.pc + offset
        return self.code[pos] if pos < len(self.code) else 0

    def _i16(self, offset: int = 0) -> int:
        pos = self.pc + offset
        if pos + 2 > len(self.code):
            return 0
        return struct.unpack_from(">h", self.code, pos)[0]

    def _u16(self, offset: int = 0) -> int:
        pos = self.pc + offset
        if pos + 2 > len(self.code):
            return 0
        return struct.unpack_from(">H", self.code, pos)[0]

    def _step(self):
        op = self._u8()

        if op == 0x00:  # HALT
            self.halted = True
            self.pc += 1

        elif op == 0x02:  # MOVI reg, imm16
            reg = self._u8(1)
            imm = self._i16(2)
            self.registers[reg] = imm
            self.pc += 4

        elif op == 0x03:  # JMP addr16
            self.pc = self._u16(1)

        elif op == 0x04:  # JZ addr16
            addr = self._u16(1)
            self.pc = addr if self.flags.get("zero") else self.pc + 3

        elif op == 0x05:  # JNZ addr16
            addr = self._u16(1)
            self.pc = addr if not self.flags.get("zero") else self.pc + 3

        elif op == 0x06:  # CALL addr16
            self.call_stack.append(self.pc + 3)
            self.pc = self._u16(1)

        elif op == 0x07:  # RET
            self.pc = self.call_stack.pop() if self.call_stack else (setattr(self, 'halted', True) or 0)

        elif op == 0x08:  # ADD rd, rs1, rs2
            rd, rs1, rs2 = self._u8(1), self._u8(2), self._u8(3)
            self.registers[rd] = self.registers[rs1] + self.registers[rs2]
            self.pc += 4

        elif op == 0x09:  # SUB rd, rs1, rs2
            rd, rs1, rs2 = self._u8(1), self._u8(2), self._u8(3)
            self.registers[rd] = self.registers[rs1] - self.registers[rs2]
            self.pc += 4

        elif op == 0x0A:  # MUL rd, rs1, rs2
            rd, rs1, rs2 = self._u8(1), self._u8(2), self._u8(3)
            self.registers[rd] = self.registers[rs1] * self.registers[rs2]
            self.pc += 4

        elif op == 0x20:  # CMP rs1, rs2
            a = self.registers[self._u8(1)]
            b = self.registers[self._u8(2)]
            self.flags["zero"] = (a == b)
            self.flags["negative"] = (a < b)
            self.pc += 3

        elif op == 0x28:  # PUSH imm16
            self.stack.append(self._i16(1))
            self.pc += 3

        elif op == 0x29:  # POP reg
            reg = self._u8(1)
            self.registers[reg] = self.stack.pop() if self.stack else 0
            self.pc += 2

        elif op == 0x50:  # STORE key, reg
            self.memory[str(self._u8(1))] = self.registers[self._u8(2)]
            self.pc += 3

        elif op == 0x51:  # LOAD reg, key
            reg = self._u8(1)
            self.registers[reg] = self.memory.get(str(self._u8(2)), 0)
            self.pc += 3

        elif op == 0x80:  # OUT — emit JSON output
            self.output_data.append({
                "registers": list(self.registers[:4]),
                "memory": dict(list(self.memory.items())[:10]),
                "stack_depth": len(self.stack),
            })
            self.pc += 1

        elif op == 0x81:  # IN — read input
            if self.input_data:
                item = self.input_data.pop(0)
                for i, v in enumerate(list(item.values())[:4]):
                    if isinstance(v, (int, float)):
                        self.registers[i] = int(v)
            self.pc += 1

        elif op == 0x84:  # STATE_SAVE
            self.state = {"registers": list(self.registers), "memory": dict(self.memory), "pc": self.pc + 1}
            self.pc += 1

        elif op == 0x85:  # STATE_LOAD
            if self.state:
                self.registers = list(self.state["registers"])
                self.memory = dict(self.state["memory"])
            self.pc += 1

        else:
            self.pc += 1  # skip unknown

    def get_output(self) -> list[dict]:
        return self.output_data

    def get_state(self) -> dict:
        return self.state

package main

import (
	"encoding/binary"
	"fmt"
	"os"
)

const (
	numRegs   = 16
	stackSize = 256
	memSize   = 1024
	maxSteps  = 100000
)

type SkillVM struct {
	regs      [numRegs]int16
	stack     [stackSize]int16
	sp        int
	memory    [memSize]int16
	flags     struct{ zero, neg bool }
	pc        uint16
	code      []byte
	halted    bool
	callStack [64]uint16
	callSP    int
	outCount  int
}

func (vm *SkillVM) u8(off int) byte {
	pos := int(vm.pc) + off
	if pos >= len(vm.code) {
		return 0
	}
	return vm.code[pos]
}

func (vm *SkillVM) i16(off int) int16 {
	pos := int(vm.pc) + off
	if pos+2 > len(vm.code) {
		return 0
	}
	return int16(binary.BigEndian.Uint16(vm.code[pos:]))
}

func (vm *SkillVM) u16(off int) uint16 {
	pos := int(vm.pc) + off
	if pos+2 > len(vm.code) {
		return 0
	}
	return binary.BigEndian.Uint16(vm.code[pos:])
}

func (vm *SkillVM) Run() {
	steps := 0
	for !vm.halted && int(vm.pc) < len(vm.code) && steps < maxSteps {
		op := vm.u8(0)
		switch op {
		case 0x00: // HALT
			vm.halted = true
			vm.pc++
		case 0x02: // MOVI reg, imm16
			vm.regs[vm.u8(1)] = vm.i16(2)
			vm.pc += 4
		case 0x03: // JMP
			vm.pc = vm.u16(1)
		case 0x04: // JZ
			addr := vm.u16(1)
			if vm.flags.zero {
				vm.pc = addr
			} else {
				vm.pc += 3
			}
		case 0x05: // JNZ
			addr := vm.u16(1)
			if !vm.flags.zero {
				vm.pc = addr
			} else {
				vm.pc += 3
			}
		case 0x06: // CALL
			vm.callStack[vm.callSP] = vm.pc + 3
			vm.callSP++
			vm.pc = vm.u16(1)
		case 0x07: // RET
			if vm.callSP > 0 {
				vm.callSP--
				vm.pc = vm.callStack[vm.callSP]
			} else {
				vm.halted = true
			}
		case 0x08: // ADD rd, rs1, rs2
			vm.regs[vm.u8(1)] = vm.regs[vm.u8(2)] + vm.regs[vm.u8(3)]
			vm.pc += 4
		case 0x09: // SUB
			vm.regs[vm.u8(1)] = vm.regs[vm.u8(2)] - vm.regs[vm.u8(3)]
			vm.pc += 4
		case 0x0A: // MUL
			vm.regs[vm.u8(1)] = vm.regs[vm.u8(2)] * vm.regs[vm.u8(3)]
			vm.pc += 4
		case 0x0B: // DIV
			d := vm.regs[vm.u8(3)]
			if d != 0 {
				vm.regs[vm.u8(1)] = vm.regs[vm.u8(2)] / d
			}
			vm.pc += 4
		case 0x20: // CMP
			a, b := vm.regs[vm.u8(1)], vm.regs[vm.u8(2)]
			vm.flags.zero = a == b
			vm.flags.neg = a < b
			vm.pc += 3
		case 0x28: // PUSH imm16
			vm.stack[vm.sp] = vm.i16(1)
			vm.sp++
			vm.pc += 3
		case 0x29: // POP
			vm.sp--
			if vm.sp >= 0 {
				vm.regs[vm.u8(1)] = vm.stack[vm.sp]
			}
			vm.pc += 2
		case 0x50: // STORE
			vm.memory[vm.u8(1)] = vm.regs[vm.u8(2)]
			vm.pc += 3
		case 0x51: // LOAD
			vm.regs[vm.u8(1)] = vm.memory[vm.u8(2)]
			vm.pc += 3
		case 0x80: // OUT
			fmt.Printf("{\"r0\":%d,\"r1\":%d,\"r2\":%d,\"r3\":%d}\n",
				vm.regs[0], vm.regs[1], vm.regs[2], vm.regs[3])
			vm.outCount++
			vm.pc++
		case 0x84: // STATE_SAVE
			fmt.Printf("STATE: pc=%d r0=%d\n", vm.pc+1, vm.regs[0])
			vm.pc++
		default:
			vm.pc++
		}
		steps++
	}
}

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintf(os.Stderr, "Usage: %s <skill.fluxbc>\n", os.Args[0])
		os.Exit(1)
	}
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
	vm := &SkillVM{code: data}
	vm.Run()
	fmt.Printf("HALT after %d outputs\n", vm.outCount)
}

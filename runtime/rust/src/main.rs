use std::env;
use std::fs;
use std::process;

const NUM_REGS: usize = 16;
const STACK_SIZE: usize = 256;
const MEM_SIZE: usize = 1024;
const MAX_STEPS: usize = 100_000;

struct Flags { zero: bool, negative: bool }

struct SkillVM {
    regs: [i16; NUM_REGS],
    stack: [i16; STACK_SIZE],
    sp: usize,
    memory: [i16; MEM_SIZE],
    flags: Flags,
    pc: usize,
    code: Vec<u8>,
    halted: bool,
    call_stack: [usize; 64],
    call_sp: usize,
    out_count: usize,
}

impl SkillVM {
    fn new(code: Vec<u8>) -> Self {
        SkillVM {
            regs: [0; NUM_REGS],
            stack: [0; STACK_SIZE],
            sp: 0,
            memory: [0; MEM_SIZE],
            flags: Flags { zero: false, negative: false },
            pc: 0,
            code,
            halted: false,
            call_stack: [0; 64],
            call_sp: 0,
            out_count: 0,
        }
    }

    fn u8(&self, off: usize) -> u8 {
        let pos = self.pc + off;
        self.code.get(pos).copied().unwrap_or(0)
    }

    fn i16(&self, off: usize) -> i16 {
        let pos = self.pc + off;
        if pos + 2 > self.code.len() { return 0; }
        i16::from_be_bytes([self.code[pos], self.code[pos + 1]])
    }

    fn u16(&self, off: usize) -> usize {
        let pos = self.pc + off;
        if pos + 2 > self.code.len() { return 0; }
        u16::from_be_bytes([self.code[pos], self.code[pos + 1]]) as usize
    }

    fn run(&mut self) {
        let mut steps = 0;
        while !self.halted && self.pc < self.code.len() && steps < MAX_STEPS {
            let op = self.u8(0);
            match op {
                0x00 => { self.halted = true; self.pc += 1; }
                0x02 => { let r = self.u8(1) as usize; self.regs[r] = self.i16(2); self.pc += 4; }
                0x03 => { self.pc = self.u16(1); }
                0x04 => { let addr = self.u16(1); self.pc = if self.flags.zero { addr } else { self.pc + 3 }; }
                0x05 => { let addr = self.u16(1); self.pc = if !self.flags.zero { addr } else { self.pc + 3 }; }
                0x06 => { self.call_stack[self.call_sp] = self.pc + 3; self.call_sp += 1; self.pc = self.u16(1); }
                0x07 => { self.call_sp -= 1; self.pc = self.call_stack[self.call_sp]; if self.call_sp == 0 && self.pc == 0 { self.halted = true; } }
                0x08 => { let d = self.u8(1) as usize; self.regs[d] = self.regs[self.u8(2) as usize] + self.regs[self.u8(3) as usize]; self.pc += 4; }
                0x09 => { let d = self.u8(1) as usize; self.regs[d] = self.regs[self.u8(2) as usize] - self.regs[self.u8(3) as usize]; self.pc += 4; }
                0x0A => { let d = self.u8(1) as usize; self.regs[d] = self.regs[self.u8(2) as usize] * self.regs[self.u8(3) as usize]; self.pc += 4; }
                0x0B => { let d = self.u8(1) as usize; let div = self.regs[self.u8(3) as usize]; if div != 0 { self.regs[d] = self.regs[self.u8(2) as usize] / div; } self.pc += 4; }
                0x20 => { let a = self.regs[self.u8(1) as usize]; let b = self.regs[self.u8(2) as usize]; self.flags.zero = a == b; self.flags.negative = a < b; self.pc += 3; }
                0x28 => { self.stack[self.sp] = self.i16(1); self.sp += 1; self.pc += 3; }
                0x29 => { self.sp -= 1; self.regs[self.u8(1) as usize] = self.stack[self.sp]; self.pc += 2; }
                0x50 => { self.memory[self.u8(1) as usize] = self.regs[self.u8(2) as usize]; self.pc += 3; }
                0x51 => { self.regs[self.u8(1) as usize] = self.memory[self.u8(2) as usize]; self.pc += 3; }
                0x80 => { println!("{{\"r0\":{},\"r1\":{},\"r2\":{},\"r3\":{}}}", self.regs[0], self.regs[1], self.regs[2], self.regs[3]); self.out_count += 1; self.pc += 1; }
                0x84 => { println!("STATE: pc={} r0={}", self.pc + 1, self.regs[0]); self.pc += 1; }
                _ => { self.pc += 1; }
            }
            steps += 1;
        }
    }
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 { eprintln!("Usage: {} <skill.fluxbc>", args[0]); process::exit(1); }
    let code = fs::read(&args[1]).unwrap_or_else(|e| { eprintln!("Error: {}", e); process::exit(1); });
    let mut vm = SkillVM::new(code);
    vm.run();
    println!("HALT after {} outputs", vm.out_count);
}

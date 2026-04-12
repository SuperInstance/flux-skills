const std = @import("std");

const NUM_REGS: usize = 16;
const STACK_SIZE: usize = 256;
const MEM_SIZE: usize = 1024;
const MAX_STEPS: usize = 100_000;

const SkillVM = struct {
    regs: [NUM_REGS]i16,
    stack: [STACK_SIZE]i16,
    sp: usize,
    memory: [MEM_SIZE]i16,
    zero_flag: bool,
    neg_flag: bool,
    pc: usize,
    code: []const u8,
    halted: bool,
    call_stack: [64]usize,
    call_sp: usize,
    out_count: usize,

    fn init(code: []const u8) SkillVM {
        return SkillVM{
            .regs = std.mem.zeroes([NUM_REGS]i16),
            .stack = std.mem.zeroes([STACK_SIZE]i16),
            .sp = 0,
            .memory = std.mem.zeroes([MEM_SIZE]i16),
            .zero_flag = false,
            .neg_flag = false,
            .pc = 0,
            .code = code,
            .halted = false,
            .call_stack = std.mem.zeroes([64]usize),
            .call_sp = 0,
            .out_count = 0,
        };
    }

    fn u8at(self: *SkillVM, off: usize) u8 {
        const pos = self.pc + off;
        if (pos >= self.code.len) return 0;
        return self.code[pos];
    }

    fn i16at(self: *SkillVM, off: usize) i16 {
        const pos = self.pc + off;
        if (pos + 2 > self.code.len) return 0;
        return @intCast((@as(u16, self.code[pos]) << 8) | @as(u16, self.code[pos + 1]));
    }

    fn u16at(self: *SkillVM, off: usize) usize {
        const pos = self.pc + off;
        if (pos + 2 > self.code.len) return 0;
        return (@as(usize, self.code[pos]) << 8) | @as(usize, self.code[pos + 1]);
    }

    fn run(self: *SkillVM) void {
        var steps: usize = 0;
        const stdout = std.io.getStdOut().writer();
        while (!self.halted and self.pc < self.code.len and steps < MAX_STEPS) {
            const op = self.u8at(0);
            switch (op) {
                0x00 => { self.halted = true; self.pc += 1; },
                0x02 => { const r = self.u8at(1); self.regs[r] = self.i16at(2); self.pc += 4; },
                0x03 => { self.pc = self.u16at(1); },
                0x04 => { const addr = self.u16at(1); self.pc = if (self.zero_flag) addr else self.pc + 3; },
                0x05 => { const addr = self.u16at(1); self.pc = if (!self.zero_flag) addr else self.pc + 3; },
                0x06 => { self.call_stack[self.call_sp] = self.pc + 3; self.call_sp += 1; self.pc = self.u16at(1); },
                0x07 => { self.call_sp -= 1; self.pc = self.call_stack[self.call_sp]; if (self.call_sp == 0 and self.pc == 0) self.halted = true; },
                0x08 => { const d = self.u8at(1); self.regs[d] = self.regs[self.u8at(2)] + self.regs[self.u8at(3)]; self.pc += 4; },
                0x09 => { const d = self.u8at(1); self.regs[d] = self.regs[self.u8at(2)] - self.regs[self.u8at(3)]; self.pc += 4; },
                0x0A => { const d = self.u8at(1); self.regs[d] = self.regs[self.u8at(2)] * self.regs[self.u8at(3)]; self.pc += 4; },
                0x0B => { const d = self.u8at(1); const dv = self.regs[self.u8at(3)]; if (dv != 0) self.regs[d] = @divTrunc(self.regs[self.u8at(2)], dv); self.pc += 4; },
                0x20 => { const a = self.regs[self.u8at(1)]; const b = self.regs[self.u8at(2)]; self.zero_flag = a == b; self.neg_flag = a < b; self.pc += 3; },
                0x28 => { self.stack[self.sp] = self.i16at(1); self.sp += 1; self.pc += 3; },
                0x29 => { self.sp -= 1; self.regs[self.u8at(1)] = self.stack[self.sp]; self.pc += 2; },
                0x50 => { self.memory[self.u8at(1)] = self.regs[self.u8at(2)]; self.pc += 3; },
                0x51 => { self.regs[self.u8at(1)] = self.memory[self.u8at(2)]; self.pc += 3; },
                0x80 => { stdout.print("{{\"r0\":{},\"r1\":{},\"r2\":{},\"r3\":{}}}\n", .{ self.regs[0], self.regs[1], self.regs[2], self.regs[3] }) catch {}; self.out_count += 1; self.pc += 1; },
                0x84 => { stdout.print("STATE: pc={} r0={}\n", .{ self.pc + 1, self.regs[0] }) catch {}; self.pc += 1; },
                else => { self.pc += 1; },
            }
            steps += 1;
        }
        stdout.print("HALT after {} outputs\n", .{self.out_count}) catch {};
    }
};

pub fn main() !void {
    const args = try std.process.argsAlloc(std.heap.page_allocator);
    if (args.len < 2) {
        std.debug.print("Usage: {s} <skill.fluxbc>\n", .{args[0]});
        std.process.exit(1);
    }
    const file = try std.fs.cwd().openFile(args[1], .{});
    const code = try file.readToEndAlloc(std.heap.page_allocator, 1024 * 1024);
    var vm = SkillVM.init(code);
    vm.run();
}

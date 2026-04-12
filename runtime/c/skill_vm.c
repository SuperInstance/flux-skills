/*
 * FLUX Skill VM — C implementation
 * Lightweight runtime for executing FLUX agent skills
 * 
 * Build: gcc -O2 -o skill_vm skill_vm.c
 * Run:   ./skill_vm skill.fluxbc
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>

#define NUM_REGS 16
#define STACK_SIZE 256
#define MEM_SIZE 1024
#define MAX_STEPS 100000

typedef struct {
    int16_t regs[NUM_REGS];
    int16_t stack[STACK_SIZE];
    int sp;
    int16_t memory[MEM_SIZE];
    struct { bool zero, negative; } flags;
    uint16_t pc;
    uint8_t *code;
    size_t code_len;
    bool halted;
    uint16_t call_stack[64];
    int call_sp;
    int output_count;
} SkillVM;

static inline uint8_t u8(SkillVM *vm, int offset) {
    size_t pos = vm->pc + offset;
    return pos < vm->code_len ? vm->code[pos] : 0;
}

static inline int16_t i16(SkillVM *vm, int offset) {
    size_t pos = vm->pc + offset;
    if (pos + 2 > vm->code_len) return 0;
    return (int16_t)((vm->code[pos] << 8) | vm->code[pos + 1]);
}

static inline uint16_t u16(SkillVM *vm, int offset) {
    size_t pos = vm->pc + offset;
    if (pos + 2 > vm->code_len) return 0;
    return (uint16_t)((vm->code[pos] << 8) | vm->code[pos + 1]);
}

void vm_init(SkillVM *vm) {
    memset(vm, 0, sizeof(SkillVM));
}

int vm_load(SkillVM *vm, const char *path) {
    FILE *f = fopen(path, "rb");
    if (!f) { perror(path); return -1; }
    fseek(f, 0, SEEK_END);
    vm->code_len = ftell(f);
    fseek(f, 0, SEEK_SET);
    vm->code = malloc(vm->code_len);
    if (!vm->code) { fclose(f); return -1; }
    fread(vm->code, 1, vm->code_len, f);
    fclose(f);
    return 0;
}

void vm_run(SkillVM *vm) {
    int steps = 0;
    while (!vm->halted && vm->pc < vm->code_len && steps < MAX_STEPS) {
        uint8_t op = u8(vm, 0);
        switch (op) {
            case 0x00: vm->halted = true; vm->pc++; break;
            case 0x02: { // MOVI reg, imm16
                uint8_t reg = u8(vm, 1);
                vm->regs[reg] = i16(vm, 2);
                vm->pc += 4;
                break;
            }
            case 0x03: vm->pc = u16(vm, 1); break; // JMP
            case 0x04: { // JZ
                uint16_t addr = u16(vm, 1);
                vm->pc = vm->flags.zero ? addr : vm->pc + 3;
                break;
            }
            case 0x05: { // JNZ
                uint16_t addr = u16(vm, 1);
                vm->pc = vm->flags.zero ? vm->pc + 3 : addr;
                break;
            }
            case 0x06: { // CALL
                vm->call_stack[vm->call_sp++] = vm->pc + 3;
                vm->pc = u16(vm, 1);
                break;
            }
            case 0x07: // RET
                vm->pc = vm->call_sp > 0 ? vm->call_stack[--vm->call_sp] : 0;
                if (vm->call_sp == 0 && vm->pc == 0) vm->halted = true;
                break;
            case 0x08: { // ADD rd, rs1, rs2
                vm->regs[u8(vm,1)] = vm->regs[u8(vm,2)] + vm->regs[u8(vm,3)];
                vm->pc += 4; break;
            }
            case 0x09: { // SUB
                vm->regs[u8(vm,1)] = vm->regs[u8(vm,2)] - vm->regs[u8(vm,3)];
                vm->pc += 4; break;
            }
            case 0x0A: { // MUL
                vm->regs[u8(vm,1)] = vm->regs[u8(vm,2)] * vm->regs[u8(vm,3)];
                vm->pc += 4; break;
            }
            case 0x0B: { // DIV
                int16_t d = vm->regs[u8(vm,3)];
                vm->regs[u8(vm,1)] = d != 0 ? vm->regs[u8(vm,2)] / d : 0;
                vm->pc += 4; break;
            }
            case 0x20: { // CMP
                int16_t a = vm->regs[u8(vm,1)], b = vm->regs[u8(vm,2)];
                vm->flags.zero = (a == b);
                vm->flags.negative = (a < b);
                vm->pc += 3; break;
            }
            case 0x28: { // PUSH imm16
                vm->stack[vm->sp++] = i16(vm, 1);
                vm->pc += 3; break;
            }
            case 0x29: { // POP reg
                vm->regs[u8(vm,1)] = vm->sp > 0 ? vm->stack[--vm->sp] : 0;
                vm->pc += 2; break;
            }
            case 0x50: { // STORE key, reg
                vm->memory[u8(vm,1)] = vm->regs[u8(vm,2)];
                vm->pc += 3; break;
            }
            case 0x51: { // LOAD reg, key
                vm->regs[u8(vm,1)] = vm->memory[u8(vm,2)];
                vm->pc += 3; break;
            }
            case 0x80: { // OUT
                printf("{\"r0\":%d,\"r1\":%d,\"r2\":%d,\"r3\":%d,\"mem_0\":%d}\n",
                    vm->regs[0], vm->regs[1], vm->regs[2], vm->regs[3], vm->memory[0]);
                vm->output_count++;
                vm->pc++; break;
            }
            case 0x84: { // STATE_SAVE
                printf("STATE: pc=%d r0=%d r1=%d\n", vm->pc + 1, vm->regs[0], vm->regs[1]);
                vm->pc++; break;
            }
            default: vm->pc++; break; // skip unknown
        }
        steps++;
    }
}

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <skill.fluxbc>\n", argv[0]);
        return 1;
    }
    SkillVM vm;
    vm_init(&vm);
    if (vm_load(&vm, argv[1]) != 0) return 1;
    vm_run(&vm);
    printf("HALT after %d outputs\n", vm.output_count);
    free(vm.code);
    return 0;
}

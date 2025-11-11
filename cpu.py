"""
6502 CPU emulator
"""


class CPU:
    def __init__(self):
        self.a  = 0
        self.x  = 0
        self.y  = 0
        self.pc = 0
        self.sp = 0xFF

        self.flag_n = 0  # negative
        self.flag_v = 0  # overflow
        self.flag_z = 0  # zero
        self.flag_c = 0  # carry

        self.memory  = bytearray(65536)
        self.cycles  = 0
        self.steps   = 0
        self.running = True

    def reset(self):
        self.a      = 0
        self.x      = 0
        self.y      = 0
        self.pc     = 0
        self.sp  = 0xFF
        self.flag_n = 0
        self.flag_v = 0
        self.flag_z = 0
        self.flag_c = 0
        self.cycles = 0
        self.steps  = 0
        self.running = True

    def set_nz(self, val):
        # update neg && zero flags
        val &= 0xFF
        self.flag_z = 1 if val == 0 else 0
        self.flag_n = 1 if val & 0x80 else 0

    def push(self, val):
        # push byte -> stack
        self.memory[0x100 + self.sp] = val & 0xFF
        self.sp = (self.sp - 1) & 0xFF

    def pop(self):
        # pop byte <- stack
        self.sp = (self.sp + 1) & 0xFF
        return self.memory[0x100 + self.sp]

    def step(self):
        
        if not self.running: return False

        op = self.memory[self.pc]
        self.pc = (self.pc + 1) & 0xFFFF
        self.steps += 1

        # ---------------------------------------------
        # loads
        # ---------------------------------------------
        if op == 0xA9:   # LDA #imm
            self.a = self.memory[self.pc]
            self.pc += 1
            self.set_nz(self.a)
            self.cycles += 2

        elif op == 0xA5:  # LDA zpg
            addr = self.memory[self.pc]
            self.pc += 1
            self.a = self.memory[addr]
            self.set_nz(self.a)
            self.cycles += 3

        elif op == 0xAD:  # LDA abs
            lo = self.memory[self.pc]
            hi = self.memory[self.pc + 1]
            self.pc += 2
            self.a = self.memory[(hi << 8) | lo]
            self.set_nz(self.a)
            self.cycles += 4

        elif op == 0xA2:  # LDX #imm
            self.x = self.memory[self.pc]
            self.pc += 1
            self.set_nz(self.x)
            self.cycles += 2

        elif op == 0xA6:  # LDX zpg
            addr = self.memory[self.pc]
            self.pc += 1
            self.x = self.memory[addr]
            self.set_nz(self.x)
            self.cycles += 3

        elif op == 0xB5:  # LDA zpg,X
            zp = self.memory[self.pc]
            self.pc += 1
            addr = (zp + self.x) & 0xFF
            self.a = self.memory[addr]
            self.set_nz(self.a)
            self.cycles += 4

        elif op == 0xA0:  # LDY #imm
            self.y = self.memory[self.pc]
            self.pc += 1
            self.set_nz(self.y)
            self.cycles += 2

        elif op == 0xA4:  # LDY zpg
            addr = self.memory[self.pc]
            self.pc += 1
            self.y = self.memory[addr]
            self.set_nz(self.y)
            self.cycles += 3

        # ---------------------------------------------
        # sstores
        # ---------------------------------------------
        elif op == 0x85:  # STA zpg
            addr = self.memory[self.pc]
            self.pc += 1
            self.memory[addr] = self.a
            self.cycles += 3

        elif op == 0x8D:  # STA abs
            lo = self.memory[self.pc]
            hi = self.memory[self.pc + 1]
            self.pc += 2
            self.memory[(hi << 8) | lo] = self.a
            self.cycles += 4

        elif op == 0x86:  # STX zpg
            addr = self.memory[self.pc]
            self.pc += 1
            self.memory[addr] = self.x
            self.cycles += 3

        elif op == 0x95:  # STA zpg,X
            zp = self.memory[self.pc]
            self.pc += 1
            addr = (zp + self.x) & 0xFF
            self.memory[addr] = self.a
            self.cycles += 4

        elif op == 0x84:  # STY zpg
            addr = self.memory[self.pc]
            self.pc += 1
            self.memory[addr] = self.y
            self.cycles += 3

        # ---------------------------------------------
        # maths
        # ---------------------------------------------
        elif op == 0x69:  # ADC #imm
            val = self.memory[self.pc]
            self.pc += 1
            result = self.a + val + self.flag_c
            self.flag_v = 1 if ((self.a ^ result) & (val ^ result) & 0x80) else 0
            self.flag_c = 1 if result > 0xFF else 0
            self.a = result & 0xFF
            self.set_nz(self.a)
            self.cycles += 2

        elif op == 0x65:  # ADC zpg
            addr = self.memory[self.pc]
            self.pc += 1
            val = self.memory[addr]
            result = self.a + val + self.flag_c
            self.flag_v = 1 if ((self.a ^ result) & (val ^ result) & 0x80) else 0
            self.flag_c = 1 if result > 0xFF else 0
            self.a = result & 0xFF
            self.set_nz(self.a)
            self.cycles += 3

        elif op == 0xE9:  # SBC #imm
            val = self.memory[self.pc]
            self.pc += 1
            result = self.a - val - (1 - self.flag_c)
            self.flag_v = 1 if ((self.a ^ val) & (self.a ^ result) & 0x80) else 0
            self.flag_c = 0 if result < 0 else 1
            self.a = result & 0xFF
            self.set_nz(self.a)
            self.cycles += 2

        # ---------------------------------------------
        # logic
        # ---------------------------------------------
        elif op == 0x29:  # AND #imm
            self.a &= self.memory[self.pc]
            self.pc += 1
            self.set_nz(self.a)
            self.cycles += 2

        elif op == 0x09:  # ORA #imm
            self.a |= self.memory[self.pc]
            self.pc += 1
            self.set_nz(self.a)
            self.cycles += 2

        elif op == 0x49:  # EOR #imm
            self.a ^= self.memory[self.pc]
            self.pc += 1
            self.set_nz(self.a)
            self.cycles += 2

        # ---------------------------------------------
        # compare
        # ---------------------------------------------
        elif op == 0xC9:  # CMP #imm
            val = self.memory[self.pc]
            self.pc += 1
            result = self.a - val
            self.flag_c = 1 if self.a >= val else 0
            self.set_nz(result & 0xFF)
            self.cycles += 2

        elif op == 0xC5:  # CMP zpg  <-- ADD THIS
            addr = self.memory[self.pc]
            self.pc += 1
            val = self.memory[addr]
            result = self.a - val
            self.flag_c = 1 if self.a >= val else 0
            self.set_nz(result & 0xFF)
            self.cycles += 3

        elif op == 0xD5:  # CMP zpg,X
            zp = self.memory[self.pc]
            self.pc += 1
            addr = (zp + self.x) & 0xFF
            val = self.memory[addr]
            result = self.a - val
            self.flag_c = 1 if self.a >= val else 0
            self.set_nz(result & 0xFF)
            self.cycles += 4

        elif op == 0xE0:  # CPX #imm
            val = self.memory[self.pc]
            self.pc += 1
            result = self.x - val
            self.flag_c = 1 if self.x >= val else 0
            self.set_nz(result & 0xFF)
            self.cycles += 2

        elif op == 0xE4:  # CPX zpg  <-- ADD THIS
            addr = self.memory[self.pc]
            self.pc += 1
            val = self.memory[addr]
            result = self.x - val
            self.flag_c = 1 if self.x >= val else 0
            self.set_nz(result & 0xFF)
            self.cycles += 3

        elif op == 0xC0:  # CPY #imm
            val = self.memory[self.pc]
            self.pc += 1
            result = self.y - val
            self.flag_c = 1 if self.y >= val else 0
            self.set_nz(result & 0xFF)
            self.cycles += 2

        elif op == 0xC4:  # CPY zpg  <-- ADD THIS
            addr = self.memory[self.pc]
            self.pc += 1
            val = self.memory[addr]
            result = self.y - val
            self.flag_c = 1 if self.y >= val else 0
            self.set_nz(result & 0xFF)
            self.cycles += 3

        # ---------------------------------------------
        # inc/ dec
        # ---------------------------------------------
        elif op == 0xE8:  # INX
            self.x = (self.x + 1) & 0xFF
            self.set_nz(self.x)
            self.cycles += 2

        elif op == 0xC8:  # INY
            self.y = (self.y + 1) & 0xFF
            self.set_nz(self.y)
            self.cycles += 2

        elif op == 0xCA:  # DEX
            self.x = (self.x - 1) & 0xFF
            self.set_nz(self.x)
            self.cycles += 2

        elif op == 0x88:  # DEY
            self.y = (self.y - 1) & 0xFF
            self.set_nz(self.y)
            self.cycles += 2

        # ---------------------------------------------
        # flags
        # ---------------------------------------------
        elif op == 0x18:  # CLC
            self.flag_c = 0
            self.cycles += 2

        elif op == 0x38:  # SEC
            self.flag_c = 1
            self.cycles += 2

        # ---------------------------------------------
        # transfer
        # ---------------------------------------------
        elif op == 0xAA:  # TAX
            self.x = self.a
            self.set_nz(self.x)
            self.cycles += 2

        elif op == 0xA8:  # TAY
            self.y = self.a
            self.set_nz(self.y)
            self.cycles += 2

        elif op == 0x8A:  # TXA
            self.a = self.x
            self.set_nz(self.a)
            self.cycles += 2

        elif op == 0x98:  # TYA
            self.a = self.y
            self.set_nz(self.a)
            self.cycles += 2

        # ---------------------------------------------
        # jump/ branch
        # ---------------------------------------------
        elif op == 0x4C:  # JMP abs
            lo = self.memory[self.pc]
            hi = self.memory[self.pc + 1]
            self.pc = (hi << 8) | lo
            self.cycles += 3

        elif op == 0x20:  # JSR
            lo = self.memory[self.pc]
            hi = self.memory[self.pc + 1]
            ret_addr = (self.pc + 1) & 0xFFFF
            self.push(ret_addr >> 8)
            self.push(ret_addr & 0xFF)
            self.pc = (hi << 8) | lo
            self.cycles += 6

        elif op == 0x60:  # RTS
            lo = self.pop()
            hi = self.pop()
            self.pc = (((hi << 8) | lo) + 1) & 0xFFFF
            self.cycles += 6

        # ---------------------------------------------
        # branches
        # ---------------------------------------------
        elif op in (0x90, 0xB0, 0xF0, 0xD0, 0x30, 0x10):
            offset = self.memory[self.pc]
            self.pc += 1
            self.cycles += 2

            branch_ = False
            if   op == 0x90: branch_ = (self.flag_c == 0)   # BCC
            elif op == 0xB0: branch_ = (self.flag_c == 1)   # BCS
            elif op == 0xF0: branch_ = (self.flag_z == 1)   # BEQ
            elif op == 0xD0: branch_ = (self.flag_z == 0)   # BNE
            elif op == 0x30: branch_ = (self.flag_n == 1)   # BMI
            elif op == 0x10: branch_ = (self.flag_n == 0)   # BPL

            if branch_:
                self.cycles += 1
                old_pc = self.pc
                # offset := signd byte
                if offset >= 128:
                    offset = offset - 256
                new_pc = (self.pc + offset) & 0xFFFF
                self.pc = new_pc
                if (old_pc & 0xFF00) != (new_pc & 0xFF00):
                    self.cycles += 1

        # ---------------------------------------------
        
        elif op == 0x00: self.running = False     # BRK
        elif op == 0xEA: self.cycles += 2         # NOP
        else: self.cycles += 2  # Unknown opcode -> NOP

        return True


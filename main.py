import curses
import sys
import time

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


class Assembler:

    SIMPLE_OPS = {
        'BRK': 0x00, 'NOP': 0xEA, 'CLC': 0x18, 'SEC': 0x38,
        'INX': 0xE8, 'INY': 0xC8, 'DEX': 0xCA, 'DEY': 0x88,
        'TAX': 0xAA, 'TAY': 0xA8, 'TXA': 0x8A, 'TYA': 0x98,
        'RTS': 0x60
    }

    BRANCH_OPS = {
        'BCC': 0x90, 'BCS': 0xB0, 'BEQ': 0xF0,
        'BNE': 0xD0, 'BMI': 0x30, 'BPL': 0x10
    }

    @staticmethod
    def parse(filename):
        with open(filename) as f:
            lines = f.readlines()

        labels = {}
        instr = []
        addr = 0x0200

        # labels && bake addrs
        for ln, line in enumerate(lines):
            _line = line.rstrip()
            code = line.split(';')[0].strip()
            if not code: continue

            if ':' in code:
                label, rest = code.split(':', 1)
                labels[label.strip().upper()] = addr
                code = rest.strip()
                if not code: continue

            instr.append((ln, _line, addr, code))

            parts = code.upper().split(None, 1)
            if not parts: continue
            mnem = parts[0]

            if mnem in Assembler.SIMPLE_OPS:   addr += 1
            elif mnem in ('JMP', 'JSR'):       addr += 3
            elif mnem in Assembler.BRANCH_OPS: addr += 2
            elif len(parts) > 1:
                rawop = parts[1].strip()
                _op = rawop.upper().replace(' ', '')
                has_idx_x = _op.endswith(',X')
                _immediate = rawop.startswith('#')
                operand = rawop.split(',')[0].strip()
                # best-effort value parse (for deciding zpg vs abs)
                if   operand.startswith('$'):
                    try: val = int(operand[1:], 16)
                    except ValueError: val = 0
                elif operand and operand[0].isdigit():
                    try: val = int(operand)
                    except ValueError: val = 0
                else:  val = 0

                if mnem == 'LDA':
                    if _immediate:          addr += 2
                    elif has_idx_x:         addr += 2     # zpg,X
                    elif val < 256:           addr += 2     # zpg
                    else:                     addr += 3     # abs
                elif mnem == 'STA':
                    if has_idx_x:           addr += 2     # zpg,X
                    elif val < 256:           addr += 2     # zpg
                    else:                     addr += 3     # abs
                elif mnem == 'CMP':
                    if _immediate:          addr += 2     # imm
                    elif has_idx_x:         addr += 2     # zpg,X
                    elif val < 256:           addr += 2     # zpg
                    else:                     addr += 3     # abs (not emitted currently)
                else:
                    if _immediate:  addr += 2
                    elif operand.startswith('$') and len(operand) <= 3: addr += 2
                    else:  addr += 3
            else:
                addr += 1

        # generate bytecode
        bytecode = []
        for ln, _line, line_addr, code in instr:
            parts = code.upper().split(None, 1)
            if not parts: continue
            rawop = parts[1].strip() if len(parts) > 1 else ''
            _op = rawop.upper().replace(' ', '')
            has_idx_x = _op.endswith(',X')
            operand = rawop.split(',')[0].strip()
            mnem = parts[0]

            _immediate = operand.startswith('#')
            if _immediate: operand = operand[1:]

            if operand.startswith('$'):            val = int(operand[1:], 16)
            elif operand and operand[0].isdigit(): val = int(operand)
            elif operand.upper() in labels:        val = labels[operand.upper()]
            else: val = 0

            if mnem in Assembler.SIMPLE_OPS:
                bytecode.append(Assembler.SIMPLE_OPS[mnem])

            elif mnem == 'LDA':
                if _immediate:         bytecode.extend([0xA9, val & 0xFF])
                elif has_idx_x:        bytecode.extend([0xB5, val & 0xFF])       # zpg,X
                elif val < 256:        bytecode.extend([0xA5, val & 0xFF])       # zpg
                else:                  bytecode.extend([0xAD, val & 0xFF, val >> 8])  # abs

            elif mnem == 'LDX':
                if _immediate:         bytecode.extend([0xA2, val & 0xFF])
                else:                  bytecode.extend([0xA6, val])

            elif mnem == 'LDY':
                if _immediate:         bytecode.extend([0xA0, val & 0xFF])
                else:                  bytecode.extend([0xA4, val])

            elif mnem == 'STA':
                if has_idx_x:          bytecode.extend([0x95, val & 0xFF])       # zpg,X
                elif val < 256:        bytecode.extend([0x85, val & 0xFF])       # zpg
                else:                  bytecode.extend([0x8D, val & 0xFF, val >> 8])  # abs

            elif mnem == 'STX':        bytecode.extend([0x86, val])

            elif mnem == 'STY':        bytecode.extend([0x84, val])

            elif mnem == 'ADC':
                if _immediate:         bytecode.extend([0x69, val & 0xFF])
                else:                  bytecode.extend([0x65, val])

            elif mnem == 'SBC':        bytecode.extend([0xE9, val & 0xFF])
            elif mnem == 'AND':        bytecode.extend([0x29, val & 0xFF])
            elif mnem == 'ORA':        bytecode.extend([0x09, val & 0xFF])
            elif mnem == 'EOR':        bytecode.extend([0x49, val & 0xFF])
            elif mnem == 'CMP':
                if _immediate:         bytecode.extend([0xC9, val & 0xFF])       # imm
                elif has_idx_x:        bytecode.extend([0xD5, val & 0xFF])       # zpg,X
                else:                  bytecode.extend([0xC5, val & 0xFF])       # zpg

            elif mnem == 'CPX':
                if _immediate:         bytecode.extend([0xE0, val & 0xFF])
                else:                  bytecode.extend([0xE4, val])  # zero-page

            elif mnem == 'CPY':
                if _immediate:         bytecode.extend([0xC0, val & 0xFF])
                else:                  bytecode.extend([0xC4, val])  # zero-page
            elif mnem == 'JMP':        bytecode.extend([0x4C, val & 0xFF, val >> 8])
            elif mnem == 'JSR':        bytecode.extend([0x20, val & 0xFF, val >> 8])

            elif mnem in Assembler.BRANCH_OPS:
                # rel offset => target - (next instr addr)
                offset = (val - (line_addr + 2)) & 0xFF
                bytecode.extend([Assembler.BRANCH_OPS[mnem], offset])

        addr_line = {addr: _ln for _ln, _, addr, _ in instr}
        return bytecode, addr_line


def _format_hex_line(base, data, width=16):
    # format $XXXX:  XX XX..  |ascii|"""
    hex_part   = " ".join(f"{b:02X}" for b in data)
    ascii_part = "".join(chr(b) if 32 <= b <= 126 else '.' for b in data)
    return f"${base:04X}: {hex_part.ljust(width*3-1)}  {ascii_part}"


def draw(screen, cpu, source_lines, addr_line, pause):
    screen.clear()
    h, w = screen.getmaxyx()

    current_src_line = addr_line.get(cpu.pc, -1)
    if 0 <= current_src_line < len(source_lines):
        instr_text = source_lines[current_src_line].split(';')[0].strip()
    else: instr_text = "???"

    cur_op = cpu.memory[cpu.pc]
    header = f"Step: {cpu.steps}  PC: ${cpu.pc:04X}  SP: ${cpu.sp:02X}  OP:{cur_op:02X}  {instr_text}, {cpu.cycles}"
    screen.addstr(0, 0, header[:w-1], curses.A_BOLD)

    y = 2
    view_start = max(0, current_src_line - 4) if current_src_line >= 0 else 0
    view_end = min(len(source_lines), view_start + 12)

    for i in range(view_start, view_end):
        if y >= h - 14: break 
        display = f"{i+1:4d}: {source_lines[i].rstrip()}"
        if i == current_src_line:
            screen.addstr(y, 0, display[:w-1], curses.A_REVERSE)
        else: screen.addstr(y, 0, display[:w-1])
        y += 1

    y = 14

    sreg = f"N:{cpu.flag_n} V:{cpu.flag_v} Z:{cpu.flag_z} C:{cpu.flag_c}"
    screen.addstr(y+1, 0, f"SREG: {sreg}   PC:${cpu.pc:04X} SP:${cpu.sp:02X}",
                  curses.A_BOLD)
        
    y += 1

    
    screen.addstr(y, 0, "Registers (all):", curses.A_BOLD); y += 1
    r00_15 = f"{cpu.a:02X} {cpu.x:02X} {cpu.y:02X}" + " 00" * 13
    r16_31 = " ".join("00" for _ in range(16))
    screen.addstr(y, 2, f"R00-15:   {r00_15}"); y += 1
    screen.addstr(y, 2, f"R16-31:   {r16_31}"); y += 1

    reg_line = f"A: ${cpu.a:02X} ({cpu.a:3d})   X: ${cpu.x:02X} ({cpu.x:3d})   Y: ${cpu.y:02X} ({cpu.y:3d})"
    screen.addstr(y, 0, reg_line[:w-1], curses.A_BOLD)

    y += 1

    flag_line = f"Flags:  N={cpu.flag_n}  V={cpu.flag_v}  Z={cpu.flag_z}  C={cpu.flag_c}"
    screen.addstr(y, 0, flag_line[:w-1], curses.A_BOLD)

    y += 2

    screen.addstr(y, 0, "Zero Page Memory  $0000..$00FF", curses.A_BOLD)
    y += 1
    for row in range(8):
        if y >= h - 1: break
        base = row * 16
        hex_part = _format_hex_line(base, cpu.memory[base:base+16])
        screen.addstr(y, 0, hex_part[:w-1])
        y += 1

    y += 1
    if y < h - 1:
        screen.addstr(y, 0, "Program Memory  $0200..$02FF", curses.A_BOLD)
        y += 1
        for row in range(8):
            if y >= h - 1: break
            base = 0x0200 + row * 16
            hex_part = _format_hex_line(base, cpu.memory[base:base+16])
            screen.addstr(y, 0, hex_part[:w-1])
            y += 1

    status = "[PAUSED] " if pause else "[RUNNING] "
    if not cpu.running: status = "[STOPPED] "
    status += "SPACE=step  ENTER=run/pause  Q=quit"
    screen.addstr(h - 1, 0, status[:w-1], curses.A_REVERSE)

    screen.refresh()
    return


def Emulate(screen, filename):
    curses.curs_set(0)
    screen.nodelay(True)
    screen.timeout(50)

    with open(filename) as f: source_lines = f.readlines()
    bytecode, addr_line = Assembler.parse(filename)

    cpu = CPU()
    def _load():
        # clr, load@ $0200, reset PC && SP
        cpu.memory[:] = b'\x00' * len(cpu.memory)
        for i, b in enumerate(bytecode):
            cpu.memory[0x0200 + i] = b
        cpu.pc = 0x0200
        cpu.sp = 0xFF

    _load()

    pause = True
    _step = time.time()
    _delay = 0.1

    while True:
        draw(screen, cpu, source_lines, addr_line, pause)

        if not pause and cpu.running:
            now = time.time()
            if now - _step >= _delay:
                cpu.step()
                _step = now

        try:  key = screen.getch()
        except Exception: key = -1

        if key in (ord('q'), ord('Q')): break
        elif key == ord(' '):
            if cpu.running:
                cpu.step()
            pause = True
        elif key in (ord('\n'), ord('\r')):
            if not cpu.running:
                # restart
                cpu.reset()
                _load()
                pause = True
            else:
                pause = not pause
            _step = time.time()



if len(sys.argv) < 2:
    print("Missing args | argv[1]: <filename.asm>")
    sys.exit(1)

curses.wrapper(Emulate, sys.argv[1])
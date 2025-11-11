"""
6502 Assembler
"""


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


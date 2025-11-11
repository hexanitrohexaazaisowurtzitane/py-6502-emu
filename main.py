import curses
import sys
import time

from cpu import CPU
from assembler import Assembler

"""
6502 CPU Emulator
"""


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


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Missing args | argv[1]: <filename.asm>")
        sys.exit(1)

    curses.wrapper(Emulate, sys.argv[1])

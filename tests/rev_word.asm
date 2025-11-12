; Reverse the string "HELLO" in place
; String stored at $10-$14, result at same location

START:
    ; Initialize string "HELLO" at $10-$14
    LDA #72         ; H
    STA $10
    LDA #69         ; E
    STA $11
    LDA #76         ; L
    STA $12
    LDA #76         ; L
    STA $13
    LDA #79         ; O
    STA $14

    ; Reverse the string (5 bytes)
    ; Swap positions: 0<->4, 1<->3, 2 stays
    
    ; Swap $10 and $14 (H <-> O)
    LDA $10         ; Load 'H'
    LDX $14         ; Load 'O' into X
    STA $14         ; Store 'H' at position 4
    STX $10         ; Store 'O' at position 0

    ; Swap $11 and $13 (E <-> L)
    LDA $11         ; Load 'E'
    LDX $13         ; Load 'L' into X
    STA $13         ; Store 'E' at position 3
    STX $11         ; Store 'L' at position 1

    ; $12 (middle 'L') stays in place

    ; Result is now "OLLEH" at $10-$14
    BRK             ; Stop execution

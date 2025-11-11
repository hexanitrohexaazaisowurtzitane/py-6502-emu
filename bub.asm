; 6502 Bubble Sort
; Sorts 8 numbers in ascending order
; Array starts at $10, count at $00

    LDA #$08         ; array size = 8
    STA $00

    ; Initialize unsorted array at $10-$17
    LDA #$2A         ; 42
    STA $10
    LDA #$15         ; 21
    STA $11
    LDA #$3F         ; 63
    STA $12
    LDA #$08         ; 8
    STA $13
    LDA #$4B         ; 75
    STA $14
    LDA #$0C         ; 12
    STA $15
    LDA #$35         ; 53
    STA $16
    LDA #$01         ; 1
    STA $17

outer_loop:
    LDY #$00         ; swapped = 0
    LDX #$00         ; i = 0

pass_loop:
    LDA $10,X
    CMP $11,X
    BCC no_swap
    BEQ no_swap
    STA $02
    LDA $11,X
    STA $10,X
    LDA $02
    STA $11,X
    LDY #$01         ; swapped = 1
no_swap:
    INX
    CPX #$07         ; up to pair (6,7)
    BCC pass_loop

    CPY #$00         ; any swaps?
    BNE outer_loop   ; yes -> another pass

done:
    BRK              ; finished sorting
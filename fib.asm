; 6502 Fibonacci Calculator
; Calculates fibonacci sequence

    CLC              ; clr carry
    LDA #$01         ; F(0) = 1
    STA $00
    LDA #$01         ; F(1) = 1  
    STA $01
    LDX #$08         ; calc + 8 numbrs
loop:
    LDA $00          ; load F(n-2)
    ADC $01          ; add F(n-1)
    STA $02          ; store res
    LDA $01          ; mv F(n-1) -> F(n-2)
    STA $00
    LDA $02          ; mv res -> F(n-1)
    STA $01
    DEX              ; decre count
    BNE loop         ; branch if !zero
done:
    JMP done         ; loop : will overflow at step=298
    ;BRK             ; break clean
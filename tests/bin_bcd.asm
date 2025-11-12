; Convert binary number in A to BCD (Binary Coded Decimal)
; Input: Binary value at $10
; Output: BCD hundreds at $20, tens at $21, ones at $22

    LDA #$9C        ; Test with 156 decimal
    STA $10
    
    LDA #$00
    STA $20         ; Clear hundreds
    STA $21         ; Clear tens
    STA $22         ; Clear ones
    
    LDX $10
    
count_hundreds:
    CPX #$64        ; 100 decimal
    BCC count_tens
    LDA $20
    CLC
    ADC #$01
    STA $20
    TXA
    SEC
    SBC #$64
    TAX
    JMP count_hundreds
    
count_tens:
    CPX #$0A        ; 10 decimal
    BCC count_ones
    LDA $21
    CLC
    ADC #$01
    STA $21
    TXA
    SEC
    SBC #$0A
    TAX
    JMP count_tens
    
count_ones:
    STX $22
    
    BRK

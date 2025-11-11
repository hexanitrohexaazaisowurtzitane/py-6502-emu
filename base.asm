; Simple test - sort 3 numbers
    LDA #$30         ; 48
    STA $10
    LDA #$10         ; 16
    STA $11
    LDA #$20         ; 32
    STA $12

    ; Compare and swap $10 and $11
    LDA $10
    CMP $11
    BCC skip1
    BEQ skip1
    ; Swap using $02 as temp
    LDA $10
    STA $02
    LDA $11
    STA $10
    LDA $02
    STA $11
skip1:

    ; Compare and swap $11 and $12
    LDA $11
    CMP $12
    BCC skip2
    BEQ skip2
    ; Swap
    LDA $11
    STA $02
    LDA $12
    STA $11
    LDA $02
    STA $12
skip2:

    ; Compare and swap $10 and $11 again
    LDA $10
    CMP $11
    BCC done
    BEQ done
    ; Swap
    LDA $10
    STA $02
    LDA $11
    STA $10
    LDA $02
    STA $11

done:
    BRK
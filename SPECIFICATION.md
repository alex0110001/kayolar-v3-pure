# KAYOLAR V4 SPONGE — Specification

**Version**: 4.0.0
**Identifier**: kayolar-hash-v4.0-sponge
**Output**: 344 bits (43 bytes)
**Construction**: sponge over a 1024-bit ARX permutation, 18 rounds
**Author**: Alexandre Jean
**License**: Apache-2.0

## 1. Overview

The state is 32 words of 32 bits (1024 bits). Message blocks of 64 bytes are XORed into the first 16 words (rate, 512 bits). The other 16 words (capacity, 512 bits) are never touched by the message and never output. Operations: addition and multiplication mod 2^32, XOR, rotation. No S-box, no table. All constants derive from 5 public numbers.

## 2. Parameters

| Symbol | Value |
|---|---|
| STATE_WORDS | 32 (1024 bits) |
| RATE_WORDS / RATE_BYTES | 16 / 64 (512 bits) |
| CAPACITY | 512 bits |
| HASH_BYTES | 43 (344 bits) |
| NUM_ROUNDS | 18 |

Generic security of a sponge with capacity c and output n: collisions min(2^(n/2), 2^(c/2)) = **2^172**, pre-images min(2^n, 2^(c/2)) = **2^256**. These bounds assume the permutation behaves like a random permutation, which is not proven (see section 8).

## 3. Constants

Base numbers: R3 = 111, 37, 163, 457, DELTA = 9.

    LCG_MULT = 111 * 37 * 163 * 457 = 305 934 537
    LCG_INC  = 111 + 37 + 163 + 457 + 9 = 777
    seed     = 111 XOR (37 << 8) XOR (163 << 16) XOR (457 << 20) XOR (9 << 28)

Generator (full period mod 2^32, since LCG_MULT = 1 mod 4 and LCG_INC is odd):

    x := x * LCG_MULT + LCG_INC   (mod 2^32)
    output x XOR rotr(x, 16)

Drawn in this order from `seed`:

1. IV[0..32]: 32 outputs.
2. MULT[0..32]: 32 outputs, each set to `(v AND NOT 3) OR 3` (odd, so invertible mod 2^32).
3. RC[k][0..32] for k = 0..17: 18 x 32 outputs.

Rotations, for row in {0, 1, 2} and word i:

    p   := [37, 163, 457, 111][i mod 4]
    ROT[row][i] := ((row + 1) * p + i * 111) mod 31 + 1        // 1..31

Array shifts: SHIFT[row] = 3, 5, 7 (all coprime with 32).

## 4. Permutation

For round k = 0..17, with row = k mod 3:

    (a) for i in 0..32:   s[i] := s[i] + RC[k][i]
    (b) for i in 0..32:   s[i] := rotl(s[i] * MULT[i], ROT[row][i]) XOR s[(i - 1) mod 32]
        (sequential and in place: s[i-1] is the value already updated in this step;
         s[0] reads the old s[31])
    (c) for i in 0..16:   s[i] := s[i] + s[i + 16]
    (d) rotate the array left by SHIFT[row] words

Each step is a bijection. Step (b) is inverted by walking the chain backwards (i = 31 down to 1, then 0) with the modular inverse of MULT[i]. `permute_inverse` in `src/lib.rs` implements it; `tests/sponge.rs` checks P^-1(P(x)) = x.

Because of the in-place chain in (b), a one-bit difference reaches all 32 words within one round. Measured avalanche (`examples/diffusion.rs`) reaches about 511/1024 flipped bits after 2 rounds and every (input bit, output bit) pair is affected after 3 rounds. 18 rounds = 6x this, the same ratio as Keccak-f[1600] (24 rounds).

## 5. Padding (pad10*1)

Append byte 0x01, then zero bytes up to a multiple of 64, and XOR 0x80 into the last byte. The padded message always has at least one extra byte, so the last block is never empty of padding. If the message is 63 mod 64 bytes long, the final byte is 0x81.

## 6. Hash

    s := IV
    for each 64-byte padded block B:
        for i in 0..16: s[i] := s[i] XOR le32(B[4i .. 4i+4])
        permute(s)
    output: the first 43 bytes of le32(s[0]) || le32(s[1]) || ... || le32(s[15])

Since 43 <= 64, a single squeeze is enough.

## 7. Capacity isolation

The message only ever reaches the 16 rate words. Even an attacker who knows the full state cannot cancel a difference in the 512 capacity bits by choosing the next block; `tests/sponge.rs` (`attaque_sans_capacite_echoue`) checks this on a concrete construction.

## 8. Status

Experimental. The sponge mode is standard and well understood; the permutation is new and has had no independent cryptanalysis. Known weak points to study: the only non-linear operations are the multiplication and the modular additions; multiplication only propagates differences towards higher bits (the rotation is what brings them back down).

## 9. Test vectors

See TEST_VECTORS.md.

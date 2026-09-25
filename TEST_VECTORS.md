# KAYOLAR V4 SPONGE — Test Vectors

Inputs are byte sequences. Outputs are 86 lowercase hex characters (43 bytes, 344 bits). All except the 1 GiB case are checked by `cargo test` (`tests/sponge.rs`).

| Input | Output |
|---|---|
| (empty) | `88141106867f261f24e022855d762fa6efc8efaf7466b5e93721449443c441347d461eb84f1bf845f9aeb6` |
| `0x00` | `c99c565d2a17b517768fa59d894ed4f7775a120827083b738d8638695e3496db027dfa94d2805afcb1c926` |
| `0x01` | `b8b596e01cd8c619804187365fb6a7b2e7165c64ee217a8f4603c8346bc4a542b550b17140da1add372f66` |
| `abc` | `4c350f1fcb1d4cd486ba7e707a61ec29dff3801ca9acd0b810deed323eb5d9a082a77c70c506b7e89e647e` |
| `kayolar-v4-sponge` | `5f90ec0fa33835b50cd5c6fea48883387d70390ba0704f5df9799efc6bb222f89f222a6871f95cc28f5868` |
| 63 bytes `0xAA` | `4a56526296a627c92ec9ee8410b0cc5c2232ca3542eef9f914af036777077414d250e1c6a9ac1fb58940de` |
| 64 bytes `0xAA` (one full block) | `fe4f39018f1e25deb3351e4ab7e54cac7a74c888751e5f225fa5b3a21378694495eb9a3e03087e01cb6643` |
| 65 bytes `0xAA` | `eac036085d907884bee6cf9fef4f8c1dff07a3f60432c7d9fd017719d2a58def125056d77d0f051b371537` |
| 1 GiB of `0x00` | `34e1c539ae3f61c6706db52d67c0d4f314383be5ba3c3fac683be9a4f65511ba335d3a41ba450739ca46ec` |

## Verification

```bash
cargo build --release
printf '' | ./target/release/kayolar_v4
./target/release/kayolar_v4 --string abc
head -c 1073741824 /dev/zero | ./target/release/kayolar_v4
```

Author: Alexandre Jean — License: Apache-2.0

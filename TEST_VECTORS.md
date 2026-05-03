# KAYOLAR V3 PURE — Test Vectors

All inputs are byte sequences. All outputs are 86 lowercase hexadecimal characters representing 43 bytes (344 bits). Verified bit-exact on the reference Rust implementation.

| Input | Output |
|---|---|
| (empty, 0 bytes) | `bc3e7d06c9bad2f472aa70a33c36ea9c493fd7e83a33e4d463face70bf6e06abcefaaa4c8668ffdad63600` |
| `0x00` (1 byte) | `42403ef2b6ce734bbd4150c844a5039d396b459eacf9f71d891838cb8303d1663db2c314a1a0b2c8c36513` |
| `0x01` (1 byte) | `fa4ab38fe9815c0d6e5b02a750b778bf880961c67d8b0733ef890c6829a089b3b72436db5f0ef543b8511b` |
| 64 bytes `0xAA` | `368b07a28a96490165447b32f57379b31b99e8182867042ef312fc34d766a309358280e2c31dcf5d1e5f44` |
| 65 bytes `0xAA` | `87b1b2165f88f1a44a44a9c45e8f2f82e1dd614ee6e84ff39bdb0a3601aaeb1c1bf01cf886bef046d32e66` |
| 1 GiB of `0x00` | `178c027e509d3aabd1468790fb423f31b71b83cba54bf67a37f9943c3337485c0793f89e7ff000dba58aee` |
| 1 GiB of `0xFF` | `8b9f5545ecca76fcc9247e6c174eb46fe21ba7e1bbe107cd2e238aae74ab09ac79a78fa827b8a673d421c0` |
| 1 MiB of `(0x00, 0x01)` | `fcf8bc11e6645858076c50d60616fc7516061f04183432aa1ba9216dd3f83b4969611c701b466af26c48cd` |
| `kayolar-v3-pure` (15 ASCII bytes) | `93e63c6f255b3e7707d750a4239c11d77a156746b94e4ddae319decae1dab06f254b0ea656e25265ae20df` |

## Verification

```bash
echo -n "" | kayolar_v3
# bc3e7d06c9bad2f472aa70a33c36ea9c493fd7e83a33e4d463face70bf6e06abcefaaa4c8668ffdad63600

kayolar_v3 --string "kayolar-v3-pure"
# 93e63c6f255b3e7707d750a4239c11d77a156746b94e4ddae319decae1dab06f254b0ea656e25265ae20df

dd if=/dev/zero bs=1M count=1024 2>/dev/null | kayolar_v3
# 178c027e509d3aabd1468790fb423f31b71b83cba54bf67a37f9943c3337485c0793f89e7ff000dba58aee
```

Author: Alexandre Jean — License: Apache-2.0

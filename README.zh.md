# KAYOLAR V4 SPONGE

> [English](README.md) | [Français](README.fr.md) | [Español](README.es.md) | [Português](README.pt.md) | [Deutsch](README.de.md) | [Italiano](README.it.md) | [Русский](README.ru.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [हिन्दी](README.hi.md) | [اردو](README.ur.md) | [Tagalog](README.tl.md)

实验性 344 位哈希函数：基于全新 1024 位 ARX 置换的海绵结构。所有常量均由 5 个公开数字推导。Rust 参考实现。

    kayolar-hash-v4.0-sponge

> **状态：实验性。** 海绵模式是标准结构（SHA-3 使用它）；置换是新的，尚未经过独立密码分析。请暂勿用于保护真实数据。

## 工作原理

- **状态**: 32 个 32 位字（1024 位）。
- **吸收**: 每个 64 字节块异或进前 16 个字（rate），然后对状态做置换。其余 16 个字（容量，512 位）从不被消息触及，也从不输出。
- **置换**: 18 轮，每轮：加轮常量；原地链 `s[i] = rotl(s[i] * m[i], r) ^ s[i-1]`（一个比特的改变在一轮内传遍全部 32 个字）；两半交叉相加；字数组循环移动 3、5 或 7 位。每一步都可逆。
- **输出**: pad10*1 填充，然后取 rate 的前 43 字节。
- **常量**: IV、32 个奇数乘数和 18x32 个轮常量来自基于 111、37、163、457 和 9 的 LCG。

完整细节：SPECIFICATION.md。

## 安全目标

| 攻击 | 通用代价（假设置换可靠） |
|---|---|
| 碰撞 | 2^172 |
| 原像 / 第二原像 | 2^256 |
| 长度扩展 | 不适用 |

这是容量 512 位、输出 344 位的海绵结构的标准界限。它们对置换本身没有任何说明：这正是待解决的问题。

## 快速示例

    cargo build --release
    printf '' | ./target/release/kayolar_v4
    # 88141106867f261f24e022855d762fa6efc8efaf7466b5e93721449443c441347d461eb84f1bf845f9aeb6

    ./target/release/kayolar_v4 --string abc
    # 4c350f1fcb1d4cd486ba7e707a61ec29dff3801ca9acd0b810deed323eb5d9a082a77c70c506b7e89e647e

    ./target/release/kayolar_v4 --file path/to/file
    ./target/release/kayolar_v4 --stream 1000000 out.bin   # 用于统计测试的计数器模式输出流

作为库使用：`hashear_bytes(&data)`、`hashear("文本")`，或对数据流使用 `Hasher::new()` / `update()` / `finalize()`。

## 仓库结构

| 文件 | 用途 |
|---|---|
| SPECIFICATION.md | 完整规范 |
| TEST_VECTORS.md | 参考输出 |
| SECURITY_ANALYSIS.md | 测量结果与开放问题 |
| src/lib.rs | 参考实现（置换、逆置换、海绵、流式 API） |
| src/bin/kayolar_v4.rs | 命令行工具 |
| tests/sponge.rs | 双射性、流式、雪崩、测试向量 |
| examples/diffusion.rs | 逐轮扩散 |
| examples/longest_run_check.rs | 大 N 下的 NIST Longest Run（以 SHA-256 为参照） |
| examples/bench.rs | 与 SHA-256 的吞吐量对比 |
| nist-validation/ | 大 N 下 NIST Longest Run 测试的分析 |

## 编译和测试

    cargo build --release
    cargo test --release

## 测量（可在本仓库复现）

| 项目 | 结果 |
|---|---|
| 置换为双射（10 000 个状态） | 是 |
| 置换完全扩散 | 3 轮（实际用 18 轮） |
| 雪崩，2000 对 | 均值在 344 位中的 172 ± 1.5 以内 |
| 速度，单线程 | 52 MB/s（带 SHA-NI 的 SHA-256：1342 MB/s） |

KAYOLAR V4 比硬件加速的 SHA-256 慢约 20 倍：原地链按设计是串行的。

## 个人数据

要对标识符（手机号、邮箱、身份证号）做假名化，无论用哪种哈希，仅做哈希都不够：低熵值可以被暴力穷举恢复。请在标准原语（SHA-256、SHA-3、BLAKE3、SM3）上使用带密钥的 HMAC。

## 密码分析邀请

欢迎通过 GitHub issues 提交：缩减轮区分器、乘法-旋转链中的差分或线性路径、轮常量之间的关系。

## 作者

Alexandre Jean — 设计与参考实现，2026 年。

## 许可证

Apache License 2.0。见 LICENSE。

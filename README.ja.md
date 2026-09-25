# KAYOLAR V4 SPONGE

> [English](README.md) | [Français](README.fr.md) | [Español](README.es.md) | [Português](README.pt.md) | [Deutsch](README.de.md) | [Italiano](README.it.md) | [Русский](README.ru.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [हिन्दी](README.hi.md) | [اردو](README.ur.md) | [Tagalog](README.tl.md)

実験的な 344 ビットハッシュ関数：新しい 1024 ビット ARX 置換の上に構成したスポンジ。すべての定数は 5 つの公開数から導出されます。Rust によるリファレンス実装。

    kayolar-hash-v4.0-sponge

> **ステータス：実験的。** スポンジ構成は標準的です（SHA-3 が採用）。置換は新規で、独立した暗号解析を受けていません。実データの保護にはまだ使用しないでください。

## 仕組み

- **状態**: 32 ビット語 32 個（1024 ビット）。
- **吸収**: 64 バイトの各ブロックを先頭 16 語（レート）に XOR し、状態を置換します。残り 16 語（容量、512 ビット）はメッセージに触れられず、出力もされません。
- **置換**: 18 ラウンド：ラウンド定数の加算、インプレースの連鎖 `s[i] = rotl(s[i] * m[i], r) ^ s[i-1]`（1 ビットの変化が 1 ラウンドで 32 語すべてに届く）、前半と後半の交差加算、語配列の 3・5・7 語回転。各ステップは可逆です。
- **出力**: pad10*1 パディングの後、レートの先頭 43 バイト。
- **定数**: IV、32 個の奇数乗数、18x32 個のラウンド定数は 111、37、163、457、9 から作った LCG で生成します。

詳細：SPECIFICATION.md。

## 安全性の目標

| 攻撃 | 汎用コスト（置換が健全な場合） |
|---|---|
| 衝突 | 2^172 |
| 原像 / 第二原像 | 2^256 |
| 伸長攻撃 | 該当なし |

容量 512 ビット、出力 344 ビットのスポンジの標準的な上限です。置換そのものについては何も示しません。そこが未解決の問題です。

## クイック例

    cargo build --release
    printf '' | ./target/release/kayolar_v4
    # 88141106867f261f24e022855d762fa6efc8efaf7466b5e93721449443c441347d461eb84f1bf845f9aeb6

    ./target/release/kayolar_v4 --string abc
    # 4c350f1fcb1d4cd486ba7e707a61ec29dff3801ca9acd0b810deed323eb5d9a082a77c70c506b7e89e647e

    ./target/release/kayolar_v4 --file path/to/file
    ./target/release/kayolar_v4 --stream 1000000 out.bin   # 統計テスト用のカウンタモード出力

ライブラリとして：`hashear_bytes(&data)`、`hashear("テキスト")`、ストリームには `Hasher::new()` / `update()` / `finalize()`。

## リポジトリ構造

| ファイル | 役割 |
|---|---|
| SPECIFICATION.md | 完全な仕様 |
| TEST_VECTORS.md | 参照出力 |
| SECURITY_ANALYSIS.md | 測定結果と未解決の問題 |
| src/lib.rs | リファレンス実装（置換、逆置換、スポンジ、ストリーム API） |
| src/bin/kayolar_v4.rs | コマンドラインツール |
| tests/sponge.rs | 全単射性、ストリーム、アバランシェ、テストベクタ |
| examples/diffusion.rs | ラウンドごとの拡散 |
| examples/longest_run_check.rs | 大きな N での NIST Longest Run（SHA-256 を基準） |
| examples/bench.rs | SHA-256 とのスループット比較 |
| nist-validation/ | 大きな N での NIST Longest Run テストの分析 |

## ビルドとテスト

    cargo build --release
    cargo test --release

## 測定（このリポジトリで再現可能）

| 項目 | 結果 |
|---|---|
| 置換が全単射（10 000 状態） | はい |
| 置換の完全拡散 | 3 ラウンド（18 ラウンド使用） |
| アバランシェ、2000 ペア | 平均は 344 ビット中 172 ± 1.5 以内 |
| 速度、シングルスレッド | 52 MB/s（SHA-NI 付き SHA-256：1342 MB/s） |

KAYOLAR V4 はハードウェア SHA-256 より約 20 倍遅くなります。インプレースの連鎖は設計上逐次的です。

## 個人データ

識別子（電話番号、メールアドレス、マイナンバー）の仮名化には、どのハッシュでもハッシュ化だけでは不十分です。低エントロピーの値は総当たりで復元できます。標準プリミティブ（SHA-256、SHA-3、BLAKE3）上で鍵付き HMAC を使用してください。

## 暗号解析への招待

縮小ラウンドの識別器、乗算-回転連鎖の差分・線形特性、ラウンド定数間の関係など、GitHub issues での報告を歓迎します。

## 著者

Alexandre Jean — 設計およびリファレンス実装、2026 年。

## ライセンス

Apache License 2.0。LICENSE を参照してください。

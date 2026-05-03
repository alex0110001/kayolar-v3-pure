cat > /tmp/kayolar-v3-pure/README.ja.md << 'KAYOLAREOF'
# KAYOLAR V3 PURE

> [🇧🇷 Português](README.pt.md) | [🇺🇸 English](README.md) | [🇫🇷 Français](README.fr.md) | [🇪🇸 Español](README.es.md) | [🇷🇺 Русский](README.ru.md) | 🇯🇵 日本語 | [🇨🇳 中文](README.zh.md) | [🇸🇦 العربية](README.ar.md)

344ビット暗号学的ハッシュ関数。純粋ARX。外部プリミティブなし。公開仕様。Rustによるリファレンス実装。

    kayolar-hash-v3.0-pure

## このハッシュが存在する理由

現代の暗号学的ハッシュの大部分(SHA-256、BLAKE3、SHA-3)は、米国の機関または米国資金提供チームによって設計されています。暗号標準の歴史には文書化されたバックドア(NIST Dual_EC_DRBG、2014年に撤回)が含まれています。KAYOLAR V3は、暗号プリミティブをエンドツーエンドで制御したいユーザー向けの、独立した透明性のある代替手段として構築されています。

防御者にとって重要な3つの特性:

1. **バックドア不可能。** すべての定数は5つの小さな公開数値(R3=111、素数37、163、457、delta=9)から決定論的に導出されます。誰でも全スキームを手作業で再導出できます。隠された魔法の値も、不透明なテーブルもありません。

2. **オリジナルARXアーキテクチャ。** 256ビットハッシュを破るために攻撃者が構築した暗号解析パイプライン(SHA-256の差分暗号解析、BLAKE3のディスティングイッシャー)は、12ラウンド、三項置換、11×32ビット状態を持つ344ビットARX構造には適用できません。攻撃者はゼロから始める必要があります。

3. **ポスト量子マージン。** Groverアルゴリズム下では、344ビット出力は172ビットの実効セキュリティを保持します。SHA-256は128に低下します。KAYOLAR V3はアルゴリズムの変更なしに構造的にポスト量子時代に備えています。

## 日本およびアジア太平洋のデータ保護法への適合

KAYOLAR V3 PUREは、個人情報保護法制下で**匿名化**および**仮名化**技術として使用できます:

- **日本**: 個人情報の保護に関する法律(個人情報保護法、2003年制定、2022年改正)、第20条(安全管理措置)
- **韓国**: 個人情報保護法(PIPA、2011年)
- **台湾**: 個人資料保護法(2010年)
- **シンガポール**: Personal Data Protection Act(PDPA、2012年)
- **タイ**: Personal Data Protection Act(PDPA、2019年)
- **ベトナム**: 個人データ保護令(2023年)

KAYOLAR V3 PUREは特に以下に適しています:

- 保存または交換前の個人識別子(マイナンバー、住民登録番号、パスポート番号)の匿名化
- 適切なソルティングを伴うパスワードハッシュ化(Argon2やPBKDF2などのKDFと組み合わせて)
- データウェアハウス用の決定論的不可逆IDの生成
- 規制要件下での監査証跡

**暗号学的独立性**(NIST/NSA標準への依存なし)は、外国管轄への露出を減らし、**地域のデジタル主権**を強化したいアジア企業にとって具体的な論拠です。

## クイック例

    echo -n "" | kayolar_v3
    # bc3e7d06c9bad2f472aa70a33c36ea9c493fd7e83a33e4d463face70bf6e06abcefaaa4c8668ffdad63600

    kayolar_v3 --string "kayolar-v3-pure"
    # 93e63c6f255b3e7707d750a4239c11d77a156746b94e4ddae319decae1dab06f254b0ea656e25265ae20df

## リポジトリ構造

| ファイル | 機能 |
|---|---|
| SPECIFICATION.md | アルゴリズムの完全仕様 |
| TEST_VECTORS.md | 検証用リファレンス出力 |
| SECURITY_ANALYSIS.md | 経験的監査(雪崩、衝突、原像、性能) |
| LICENSE | Apache-2.0 |
| Cargo.toml | Rust crateマニフェスト |
| src/lib.rs | リファレンス実装 |
| nist-validation/ | NIST STSレポート + カイ二乗飽和発見 |

## ビルドとテスト

    cargo build --release
    cargo test --release

## 経験的セキュリティ要約

| テスト | 結果 |
|---|---|
| 雪崩(1024ペア、1ビット反転) | 172.21 / 172ビット反転(偏差0.12%) |
| 誕生日衝突(10^10入力) | 0衝突 |
| 原像耐性(n=30、35、40) | 全比率がエンベロープ[0, 2]内 |
| NIST SP 800-22 STS(188テスト) | 全合格 |
| 137.8 GiBでの内部16テストスイート | 16/16 PASS |

ボーナス発見: nist-validation/CHI2_LIMIT_DISCOVERY.mdを参照 — 暗号学的に準拠したソース上での極端なスケールにおけるNIST SP 800-22カイ二乗飽和限界の最初の経験的再現可能実証。

## 標準と参考文献

- **アジア太平洋**: 個人情報保護法 日本、PIPA 韓国、個人資料保護法 台湾、PDPA シンガポール、PDPA タイ、個人データ保護令 ベトナム
- **NIST**: SP 800-22 Rev. 1a(Statistical Test Suite)、SP 800-208(Stateful Hash-Based Signatures)、IR 8105(Post-Quantum Report)
- **FIPS**: 180-4(Secure Hash Standard、比較用)
- **RFC**: 6234(US Secure Hash Algorithms)

## これが何でないか

このハッシュはまだ独立した学術的暗号解析を受けていません。新しいハッシュ関数と同様、公開査読の歴史を蓄積するまで、高リスクアプリケーションには展開しないでください。SHA-256には25年間の破られていない暗号解析の実績があります。KAYOLAR V3にはゼロです。非クリティカルなアプリケーションに使用し、その分析に貢献し、発見した弱点を報告してください。

## 暗号解析への招待

暗号解析者はKAYOLAR V3 PUREを攻撃することを招待されています。発見(ディスティングイッシャー、ラウンド削減攻撃、弱鍵クラスなど)はGitHub issuesを通じて歓迎されます。

## 著者

Alexandre Jean — 設計およびリファレンス実装、2026年4月。

## ライセンス

Apache License 2.0。LICENSEを参照。
KAYOLAREOF
echo "=== ファイル作成完了 ==="
wc -l /tmp/kayolar-v3-pure/README.ja.md

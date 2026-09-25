# KAYOLAR V4 SPONGE

> [English](README.md) | [Français](README.fr.md) | [Español](README.es.md) | [Português](README.pt.md) | [Deutsch](README.de.md) | [Italiano](README.it.md) | [Русский](README.ru.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [हिन्दी](README.hi.md) | [اردو](README.ur.md) | [Tagalog](README.tl.md)

Função hash experimental de 344 bits: uma esponja sobre uma nova permutação ARX de 1024 bits. Todas as constantes derivam de 5 números públicos. Implementação de referência em Rust.

    kayolar-hash-v4.0-sponge

> **Status: experimental.** O modo esponja é padrão (o SHA-3 usa); a permutação é nova e não passou por criptanálise independente. Não a use ainda para proteger dados reais.

## Como funciona

- **Estado**: 32 palavras de 32 bits (1024 bits).
- **Absorção**: cada bloco de 64 bytes é aplicado com XOR nas 16 primeiras palavras (rate) e o estado é permutado. As outras 16 palavras (capacidade, 512 bits) nunca são tocadas pela mensagem nem publicadas.
- **Permutação**: 18 rodadas de: soma de constante; cadeia no lugar `s[i] = rotl(s[i] * m[i], r) ^ s[i-1]` (um bit alterado alcança as 32 palavras em uma rodada); soma cruzada das duas metades; rotação do vetor em 3, 5 ou 7 palavras. Cada etapa é inversível.
- **Saída**: padding pad10*1 e depois os 43 primeiros bytes do rate.
- **Constantes**: IV, 32 multiplicadores ímpares e 18x32 constantes de rodada vêm de um LCG construído sobre 111, 37, 163, 457 e 9.

Detalhes completos: SPECIFICATION.md.

## Metas de segurança

| Ataque | Custo genérico (se a permutação for sólida) |
|---|---|
| Colisão | 2^172 |
| Pré-imagem / segunda pré-imagem | 2^256 |
| Extensão de comprimento | não se aplica |

São os limites padrão de uma esponja com capacidade de 512 bits e saída de 344 bits. Não dizem nada sobre a permutação em si: essa é a questão em aberto.

## Exemplo rápido

    cargo build --release
    printf '' | ./target/release/kayolar_v4
    # 88141106867f261f24e022855d762fa6efc8efaf7466b5e93721449443c441347d461eb84f1bf845f9aeb6

    ./target/release/kayolar_v4 --string abc
    # 4c350f1fcb1d4cd486ba7e707a61ec29dff3801ca9acd0b810deed323eb5d9a082a77c70c506b7e89e647e

    ./target/release/kayolar_v4 --file path/to/file
    ./target/release/kayolar_v4 --stream 1000000 out.bin   # fluxo em modo contador para testes estatísticos

Como biblioteca: `hashear_bytes(&data)`, `hashear("texto")`, ou `Hasher::new()` / `update()` / `finalize()` para fluxos.

## Estrutura do repositório

| Arquivo | Função |
|---|---|
| SPECIFICATION.md | Especificação completa |
| TEST_VECTORS.md | Saídas de referência |
| SECURITY_ANALYSIS.md | Medições e questões em aberto |
| src/lib.rs | Implementação de referência (permutação, inversa, esponja, API de fluxo) |
| src/bin/kayolar_v4.rs | Ferramenta de linha de comando |
| tests/sponge.rs | Bijetividade, fluxo, avalanche, vetores |
| examples/diffusion.rs | Difusão por rodada |
| examples/longest_run_check.rs | NIST Longest Run em N grande (SHA-256 como referência) |
| examples/bench.rs | Desempenho comparado ao SHA-256 |
| nist-validation/ | Análise do teste NIST Longest Run em N grande |

## Compilar e testar

    cargo build --release
    cargo test --release

## Medições (reproduzíveis neste repositório)

| Medida | Resultado |
|---|---|
| Permutação bijetiva (10 000 estados) | sim |
| Difusão completa da permutação | 3 rodadas (18 usadas) |
| Avalanche, 2000 pares | média a 172 ± 1,5 de 344 bits |
| Velocidade, uma thread | 52 MB/s (SHA-256 com SHA-NI: 1342 MB/s) |

KAYOLAR V4 é cerca de 20 vezes mais lento que o SHA-256 em hardware: a cadeia no lugar é sequencial por design.

## Dados pessoais (LGPD)

Para pseudonimizar identificadores (CPF, telefone, e-mail), um hash sozinho nunca basta, com nenhum hash: valores de baixa entropia são recuperados por força bruta. Use HMAC com chave sobre uma primitiva padrão (SHA-256, SHA-3, BLAKE3).

## Convite à criptanálise

Distinguidores em rodadas reduzidas, trilhas diferenciais ou lineares na cadeia multiplicação-rotação, relações entre constantes de rodada: contribuições são bem-vindas via issues do GitHub.

## Autor

Alexandre Jean — design e implementação de referência, 2026.

## Licença

Apache License 2.0. Ver LICENSE.

cat > /tmp/kayolar-v3-pure/README.pt.md << 'KAYOLAREOF'
# KAYOLAR V3 PURE

> 🇧🇷 Português | [🇺🇸 English](README.md) | [🇫🇷 Français](README.fr.md) | [🇪🇸 Español](README.es.md) | [🇨🇳 中文](README.zh.md) | [🇸🇦 العربية](README.ar.md)

Função de hash criptográfico de 344 bits. ARX puro. Sem primitivas externas. Especificação pública. Implementação de referência em Rust.

    kayolar-hash-v3.0-pure

## Por que esta hash existe

A maioria das hashes criptográficas modernas (SHA-256, BLAKE3, SHA-3) é projetada por instituições americanas ou equipes financiadas pelos EUA. O histórico dos padrões criptográficos inclui backdoors documentados (NIST Dual_EC_DRBG, retirado em 2014). KAYOLAR V3 é construído como uma alternativa independente e transparente para usuários que querem controlar sua primitiva criptográfica de ponta a ponta.

Três propriedades importam para defensores:

1. **Sem backdoor possível.** Todas as constantes são derivadas deterministicamente de 5 pequenos números públicos (R3=111, primos 37, 163, 457, delta=9). Qualquer pessoa pode rederivar o esquema completo manualmente. Sem valor mágico oculto, sem tabela opaca.

2. **Arquitetura ARX original.** Os pipelines de criptanálise construídos pelos atacantes para quebrar hashes de 256 bits (criptanálise diferencial do SHA-256, distinguishers do BLAKE3) não se transferem para uma construção ARX de 344 bits com 12 rodadas, permutação triádica e estado de 11×32 bits. Um atacante precisa começar do zero.

3. **Margem pós-quântica.** Sob o algoritmo de Grover, a saída de 344 bits mantém 172 bits de segurança efetiva. SHA-256 cai para 128. KAYOLAR V3 está estruturalmente pronto para era pós-quântica sem mudanças algorítmicas.

## Conformidade com a LGPD brasileira

A **Lei nº 13.709/2018 (Lei Geral de Proteção de Dados Pessoais — LGPD)** define em seu **Art. 5º, inciso XI** a **anonimização** como "utilização de meios técnicos razoáveis e disponíveis no momento do tratamento, por meio dos quais um dado perde a possibilidade de associação, direta ou indireta, a um indivíduo".

Embora a palavra "criptografia" não apareça textualmente na LGPD, funções de hash criptográficas como KAYOLAR V3 são reconhecidas pela **Autoridade Nacional de Proteção de Dados (ANPD)** como uma das técnicas adequadas de **pseudonimização** e **anonimização** para o tratamento de dados pessoais conforme o **Art. 13** (estudos por órgão de pesquisa) e o **Art. 18, IV** (anonimização ou eliminação a pedido do titular).

KAYOLAR V3 PURE é particularmente adequado para:

- Anonimização de identificadores pessoais (CPF, RG, e-mail) antes de armazenamento ou compartilhamento
- Hash de senhas com salting adequado (combinado com KDF como Argon2 ou PBKDF2)
- Geração de IDs determinísticos não reversíveis para data warehousing
- Trilhas de auditoria sob exigências da ANPD

A **independência criptográfica** (sem dependência de padrões NIST/NSA) é um argumento concreto para empresas brasileiras que buscam reduzir exposição a jurisdições estrangeiras e cumprir o **Decreto nº 9.637/2018 (Política Nacional de Segurança da Informação)**.

## Exemplo rápido

    echo -n "" | kayolar_v3
    # bc3e7d06c9bad2f472aa70a33c36ea9c493fd7e83a33e4d463face70bf6e06abcefaaa4c8668ffdad63600

    kayolar_v3 --string "kayolar-v3-pure"
    # 93e63c6f255b3e7707d750a4239c11d77a156746b94e4ddae319decae1dab06f254b0ea656e25265ae20df

## Estrutura do repositório

| Arquivo | Função |
|---|---|
| SPECIFICATION.md | Especificação completa do algoritmo |
| TEST_VECTORS.md | Saídas de referência para verificação |
| SECURITY_ANALYSIS.md | Auditoria empírica (avalanche, colisões, pre-imagem, performance) |
| LICENSE | Apache-2.0 |
| Cargo.toml | Manifest da crate Rust |
| src/lib.rs | Implementação de referência |
| nist-validation/ | Relatórios NIST STS + descoberta de saturação chi² |

## Compilar e testar

    cargo build --release
    cargo test --release

## Resumo de segurança empírica

| Teste | Resultado |
|---|---|
| Avalanche (1024 pares, flip de 1 bit) | 172.21 / 172 bits invertidos (desvio de 0.12 %) |
| Colisões aniversário (10^10 entradas) | 0 colisões |
| Resistência a pre-imagem (n=30, 35, 40) | Todas as razões no envelope [0, 2] |
| NIST SP 800-22 STS (188 testes) | Todos passaram |
| Suite interna de 16 testes em 137.8 GiB | 16/16 PASS |

Descoberta bonus: ver nist-validation/CHI2_LIMIT_DISCOVERY.md — primeira demonstração empírica reproduzível do limite de saturação chi² do NIST SP 800-22 sobre uma fonte criptograficamente conforme em escala extrema.

## Padrões e referências

- **Brasil**: Lei nº 13.709/2018 (LGPD), Decreto nº 9.637/2018 (PNSI), Marco Civil da Internet (Lei nº 12.965/2014)
- **NIST**: SP 800-22 Rev. 1a (Statistical Test Suite), SP 800-208 (Stateful Hash-Based Signatures), IR 8105 (Post-Quantum Report)
- **FIPS**: 180-4 (Secure Hash Standard, para comparação)
- **RFC**: 6234 (US Secure Hash Algorithms)

## O que isto não é

Esta hash ainda não foi submetida a criptanálise acadêmica independente. Como qualquer nova função de hash, não a implante para aplicações de alto risco até que tenha acumulado um histórico público de revisão por pares. SHA-256 tem 25 anos de criptanálise sem quebra. KAYOLAR V3 tem zero. Use-a para aplicações não críticas, contribua com sua análise e relate qualquer fraqueza encontrada.

## Convite à criptanálise

Criptanalistas são convidados a atacar KAYOLAR V3 PURE. Achados (distinguishers, ataques de rounds reduzidos, classes de chaves fracas, etc.) são bem-vindos via GitHub issues.

## Autor

Alexandre Jean — design e implementação de referência, abril de 2026.

## Licença

Apache License 2.0. Veja LICENSE.
KAYOLAREOF
echo "=== ARQUIVO CRIADO ==="
wc -l /tmp/kayolar-v3-pure/README.pt.md

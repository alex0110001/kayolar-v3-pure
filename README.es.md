cat > /tmp/kayolar-v3-pure/README.es.md << 'KAYOLAREOF'
# KAYOLAR V3 PURE

> [🇧🇷 Português](README.pt.md) | [🇺🇸 English](README.md) | [🇫🇷 Français](README.fr.md) | 🇪🇸 Español | [🇨🇳 中文](README.zh.md) | [🇸🇦 العربية](README.ar.md)

Función hash criptográfica de 344 bits. ARX puro. Sin primitivas externas. Especificación pública. Implementación de referencia en Rust.

    kayolar-hash-v3.0-pure

## Por qué existe esta hash

La mayoría de las hashes criptográficas modernas (SHA-256, BLAKE3, SHA-3) están diseñadas por instituciones estadounidenses o equipos financiados por EE.UU. La historia de los estándares criptográficos incluye backdoors documentados (NIST Dual_EC_DRBG, retirado en 2014). KAYOLAR V3 está construida como una alternativa independiente y transparente para usuarios que quieren controlar su primitiva criptográfica de extremo a extremo.

Tres propiedades importan para los defensores:

1. **Sin backdoor posible.** Todas las constantes derivan deterministícamente de 5 números públicos pequeños (R3=111, primos 37, 163, 457, delta=9). Cualquiera puede rederivar el esquema completo a mano. Sin valor mágico oculto, sin tabla opaca.

2. **Arquitectura ARX original.** Los pipelines criptoanalíticos construidos por atacantes para romper hashes de 256 bits (criptoanálisis diferencial de SHA-256, distinguishers de BLAKE3) no se transfieren a una construcción ARX de 344 bits con 12 rondas, permutación triádica y estado de 11×32 bits. Un atacante tiene que empezar de cero.

3. **Margen post-cuántico.** Bajo el algoritmo de Grover, la salida de 344 bits retiene 172 bits de seguridad efectiva. SHA-256 cae a 128. KAYOLAR V3 está estructuralmente preparada para la era post-cuántica sin cambios algorítmicos.

## Conformidad con leyes de protección de datos en LATAM

KAYOLAR V3 PURE puede usarse como técnica de **anonimización** y **seudonimización** bajo las legislaciones latinoamericanas de protección de datos personales:

- **México**: Ley Federal de Protección de Datos Personales en Posesión de los Particulares (LFPDPPP, 2010), Art. 19 (medidas de seguridad)
- **Argentina**: Ley 25.326 de Protección de los Datos Personales (2000), Art. 9 (seguridad de los datos)
- **Chile**: Ley 19.628 sobre Protección de la Vida Privada (1999) y Ley 21.719 (Nueva Ley de Protección de Datos Personales, 2024)
- **Colombia**: Ley 1581 de 2012 (Régimen General de Protección de Datos Personales)
- **Uruguay**: Ley 18.331 de Protección de Datos Personales (2008)
- **Perú**: Ley 29.733 de Protección de Datos Personales (2011)

KAYOLAR V3 PURE es particularmente adecuada para:

- Anonimización de identificadores personales (RFC, CURP, DNI, RUT) antes de almacenamiento o intercambio
- Hash de contraseñas con salting adecuado (combinado con KDF como Argon2 o PBKDF2)
- Generación de IDs determinísticos no reversibles para data warehousing
- Pistas de auditoría bajo requisitos regulatorios

La **independencia criptográfica** (sin dependencia de estándares NIST/NSA) es un argumento concreto para empresas latinoamericanas que buscan reducir la exposición a jurisdicciones extranjeras y reforzar la **soberanía digital regional**.

## Ejemplo rápido

    echo -n "" | kayolar_v3
    # bc3e7d06c9bad2f472aa70a33c36ea9c493fd7e83a33e4d463face70bf6e06abcefaaa4c8668ffdad63600

    kayolar_v3 --string "kayolar-v3-pure"
    # 93e63c6f255b3e7707d750a4239c11d77a156746b94e4ddae319decae1dab06f254b0ea656e25265ae20df

## Estructura del repositorio

| Archivo | Función |
|---|---|
| SPECIFICATION.md | Especificación completa del algoritmo |
| TEST_VECTORS.md | Salidas de referencia para verificación |
| SECURITY_ANALYSIS.md | Auditoría empírica (avalanche, colisiones, pre-imagen, rendimiento) |
| LICENSE | Apache-2.0 |
| Cargo.toml | Manifiesto de la crate Rust |
| src/lib.rs | Implementación de referencia |
| nist-validation/ | Reportes NIST STS + descubrimiento de saturación chi² |

## Compilar y probar

    cargo build --release
    cargo test --release

## Resumen de seguridad empírica

| Prueba | Resultado |
|---|---|
| Avalanche (1024 pares, flip de 1 bit) | 172.21 / 172 bits invertidos (desviación 0.12 %) |
| Colisiones cumpleaños (10^10 entradas) | 0 colisiones |
| Resistencia a pre-imagen (n=30, 35, 40) | Todas las razones en envelope [0, 2] |
| NIST SP 800-22 STS (188 pruebas) | Todas pasaron |
| Suite interna de 16 pruebas en 137.8 GiB | 16/16 PASS |

Descubrimiento bonus: ver nist-validation/CHI2_LIMIT_DISCOVERY.md — primera demostración empírica reproducible del límite de saturación chi² del NIST SP 800-22 sobre una fuente criptográficamente conforme a escala extrema.

## Estándares y referencias

- **LATAM**: LFPDPPP México, Ley 25.326 Argentina, Ley 21.719 Chile, Ley 1581 Colombia, Ley 18.331 Uruguay, Ley 29.733 Perú
- **NIST**: SP 800-22 Rev. 1a (Statistical Test Suite), SP 800-208 (Stateful Hash-Based Signatures), IR 8105 (Post-Quantum Report)
- **FIPS**: 180-4 (Secure Hash Standard, para comparación)
- **RFC**: 6234 (US Secure Hash Algorithms)

## Lo que esto no es

Esta hash aún no ha sido sometida a criptoanálisis académico independiente. Como con cualquier nueva función de hash, no la despliegue para aplicaciones de alto riesgo hasta que haya acumulado un historial público de revisión por pares. SHA-256 tiene 25 años de criptoanálisis sin ruptura. KAYOLAR V3 tiene cero. Úsela para aplicaciones no críticas, contribuya a su análisis y reporte cualquier debilidad que encuentre.

## Invitación al criptoanálisis

Se invita a los criptoanalistas a atacar KAYOLAR V3 PURE. Hallazgos (distinguishers, ataques de rondas reducidas, clases de claves débiles, etc.) son bienvenidos vía GitHub issues.

## Autor

Alexandre Jean — diseño e implementación de referencia, abril 2026.

## Licencia

Apache License 2.0. Vea LICENSE.
KAYOLAREOF
echo "=== ARCHIVO CREADO ==="
wc -l /tmp/kayolar-v3-pure/README.es.md

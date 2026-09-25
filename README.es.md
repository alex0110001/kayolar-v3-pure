# KAYOLAR V4 SPONGE

> [English](README.md) | [Français](README.fr.md) | [Español](README.es.md) | [Português](README.pt.md) | [Deutsch](README.de.md) | [Italiano](README.it.md) | [Русский](README.ru.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [हिन्दी](README.hi.md) | [اردو](README.ur.md) | [Tagalog](README.tl.md)

Función hash experimental de 344 bits: una esponja sobre una nueva permutación ARX de 1024 bits. Todas las constantes derivan de 5 números públicos. Implementación de referencia en Rust.

    kayolar-hash-v4.0-sponge

> **Estado: experimental.** El modo esponja es estándar (lo usa SHA-3); la permutación es nueva y no ha tenido criptoanálisis independiente. No la use todavía para proteger datos reales.

## Cómo funciona

- **Estado**: 32 palabras de 32 bits (1024 bits).
- **Absorción**: cada bloque de 64 bytes se aplica con XOR a las 16 primeras palabras (rate) y luego se permuta el estado. Las otras 16 palabras (capacidad, 512 bits) nunca las toca el mensaje ni salen.
- **Permutación**: 18 rondas de: suma de constante; cadena en sitio `s[i] = rotl(s[i] * m[i], r) ^ s[i-1]` (un bit cambiado alcanza las 32 palabras en una ronda); suma cruzada de las dos mitades; rotación del arreglo en 3, 5 o 7 palabras. Cada paso es invertible.
- **Salida**: relleno pad10*1 y luego los 43 primeros bytes del rate.
- **Constantes**: IV, 32 multiplicadores impares y 18x32 constantes de ronda salen de un LCG construido sobre 111, 37, 163, 457 y 9.

Detalles completos: SPECIFICATION.md.

## Objetivos de seguridad

| Ataque | Coste genérico (si la permutación es sólida) |
|---|---|
| Colisión | 2^172 |
| Preimagen / segunda preimagen | 2^256 |
| Extensión de longitud | no aplica |

Son las cotas estándar de una esponja con capacidad de 512 bits y salida de 344 bits. No dicen nada de la permutación en sí: esa es la pregunta abierta.

## Ejemplo rápido

    cargo build --release
    printf '' | ./target/release/kayolar_v4
    # 88141106867f261f24e022855d762fa6efc8efaf7466b5e93721449443c441347d461eb84f1bf845f9aeb6

    ./target/release/kayolar_v4 --string abc
    # 4c350f1fcb1d4cd486ba7e707a61ec29dff3801ca9acd0b810deed323eb5d9a082a77c70c506b7e89e647e

    ./target/release/kayolar_v4 --file path/to/file
    ./target/release/kayolar_v4 --stream 1000000 out.bin   # flujo en modo contador para pruebas estadísticas

Como biblioteca: `hashear_bytes(&data)`, `hashear("texto")`, o `Hasher::new()` / `update()` / `finalize()` para flujos.

## Estructura del repositorio

| Archivo | Función |
|---|---|
| SPECIFICATION.md | Especificación completa |
| TEST_VECTORS.md | Salidas de referencia |
| SECURITY_ANALYSIS.md | Mediciones y preguntas abiertas |
| src/lib.rs | Implementación de referencia (permutación, inversa, esponja, API de flujo) |
| src/bin/kayolar_v4.rs | Herramienta de línea de comandos |
| tests/sponge.rs | Biyectividad, flujo, avalancha, vectores |
| examples/diffusion.rs | Difusión por ronda |
| examples/longest_run_check.rs | NIST Longest Run a gran N (SHA-256 como referencia) |
| examples/bench.rs | Rendimiento frente a SHA-256 |
| nist-validation/ | Análisis de la prueba NIST Longest Run a gran N |

## Compilar y probar

    cargo build --release
    cargo test --release

## Mediciones (reproducibles en este repositorio)

| Medida | Resultado |
|---|---|
| Permutación biyectiva (10 000 estados) | sí |
| Difusión completa de la permutación | 3 rondas (se usan 18) |
| Avalancha, 2000 pares | media a 172 ± 1,5 de 344 bits |
| Velocidad, un hilo | 52 MB/s (SHA-256 con SHA-NI: 1342 MB/s) |

KAYOLAR V4 es unas 20 veces más lenta que SHA-256 por hardware: la cadena en sitio es secuencial por diseño.

## Datos personales

Para seudonimizar identificadores (teléfono, correo, DNI), un hash por sí solo nunca basta, sea cual sea el hash: los valores de baja entropía se recuperan por fuerza bruta. Use un HMAC con clave sobre una primitiva estándar (SHA-256, SHA-3, BLAKE3).

## Invitación al criptoanálisis

Distinguidores en rondas reducidas, caminos diferenciales o lineales en la cadena multiplicación-rotación, relaciones entre constantes de ronda: se aceptan aportes vía issues de GitHub.

## Autor

Alexandre Jean — diseño e implementación de referencia, 2026.

## Licencia

Apache License 2.0. Ver LICENSE.

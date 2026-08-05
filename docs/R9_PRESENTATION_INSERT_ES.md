# Inserto de presentación — R9 (3 diapositivas)

## Diapositiva 1 — La idea probada y la cadena completa

**Idea:** tomar un punto de referencia LLP del 2HDM que sea corregido y teóricamente válido, y
llevarlo de extremo a extremo hasta una búsqueda real del LHC.

**La cadena funciona completa:**

> 2HDMC → UFO → MadGraph → Pythia → recast ATLAS DV+jets

- Se eligió **un** punto de referencia validado: `H2scan_mH150_tb300000`, Tipo I, alineación exacta
  (s_{β−α} = 1), tanβ = 3 × 10⁵.
- El acoplamiento trilineal h–H2–H2 se toma **del modelo**, no se ajusta a mano.
- La vida media, la anchura y las razones de desintegración provienen del mismo cálculo 2HDMC.
- El resultado llega hasta un número físico: eventos esperados en la región Trackless con 139 fb⁻¹.

*Reparto de responsabilidades:* `dihiggs` = modelo 2HDMC y acoplamiento · `dihiggs_ufo` = UFO y
convención GHphiphi · `dihiggs_hep_cross` = sección eficaz, escalado y umbrales ·
`dihiggs_llp_recast` = aceptancia validada.

---

## Diapositiva 2 — El resultado R8 validado

| Cantidad | Valor |
|---|---|
| m_H2 | 150 GeV |
| cτ | 4.326 mm |
| Trackless A × eff | **1.573386 %** |
| σ visible | 0.00207493 fb |
| Eventos esperados con 139 fb⁻¹ | **0.288** |
| Estadística High-p_T | insuficiente (`INSUFFICIENT_MC_STATISTICS`) |
| Exclusión | **no se reclama ninguna** (`exclusion_status = NOT_RUN`) |

**Conclusión principal:**

> La señal **sí es aceptada** por el análisis — la aceptancia del 1.57 % es completamente normal
> para un vértice desplazado. Lo que falla es que **el ritmo de producción derivado del modelo es
> demasiado pequeño** para este punto de referencia.

---

## Diapositiva 3 — El umbral y la respuesta teórica

**1. Umbral requerido** (a m_H2, cτ, BR y aceptancia fijos):

| N eventos | factor de ritmo | κ_g = \|g\|/\|g₀\| | \|g_hH2H2\| requerido |
|---:|---:|---:|---:|
| 1 | ×3.467 | 1.862 | **118.41 GeV** |
| 3 | ×10.402 | 3.225 | 205.09 GeV |
| 10 | ×34.672 | 5.888 | 374.45 GeV |

Partimos de \|g₀\| = 63.59 GeV. *(Escalas de ritmo ilustrativas, no criterios de exclusión: el
umbral oficial de ATLAS no pudo leerse de una fuente oficial en este entorno.)*

**2. Validación del escalado:** σ ∝ κ_g² de forma **exacta** (p = 2). GHphiphi aparece en un solo
acoplamiento del UFO → un solo vértice → el único diagrama de `g g > H > h2 h2`; la anchura del
mediador es una constante externa. No hay interferencia ni cambio de espacio fásico.

**3. ¿Puede el 2HDM alcanzarlo?** Se identificó por **medición** la única coordenada que mueve el
trilineal: **M² = m₁₂²/(s_β c_β)**. (λ₆ no lo mueve en absoluto; λ₁ es solo una
reparametrización de M².) Escaneando 7 puntos:

- Ventana **teóricamente válida** completa: κ_g ∈ [1 − 8.6 × 10⁻¹¹, 1 + 2.7 × 10⁻¹⁰].
- Fuera de ella: λ₁ ≈ −3 × 10¹⁰ → fallan positividad, unitariedad y perturbatividad.
- **cτ y BR no cambian**: cτ varía < 6 × 10⁻⁵, BR(H2→bb) se mantiene en 0.7567. No hace falta un
  nuevo recast.

**4. Por qué está bloqueado:** con tanβ = 3 × 10⁵, la relación
2(m_H2² − M²) = 2v²/tan²β · [λ₁ − m_h²/v² + 1.5 λ₆ tanβ] fija
**\|g\| → m_h²/v = 63.59 GeV**. Y ese mismo tanβ enorme es el que produce cτ ∝ tan²β, es decir, la
vida media de milímetros que hace de esto un LLP. **El parámetro que da la vida media es el que
bloquea el acoplamiento.**

### Respuesta directa

> **La idea original es viable solo por encima de un umbral de acoplamiento cuantificado
> (\|g\| ≥ 118.4 GeV, κ_g ≥ 1.862), y ese umbral NO es alcanzable en la dirección teóricamente
> válida probada:** el 2HDM permite variar κ_g en 3.6 × 10⁻¹⁰, mientras que se necesita un factor
> 1.862. El punto de referencia está a un factor **3.5 en ritmo** de un solo evento, y esa brecha no
> puede cerrarse con este tanβ sin destruir la vida media.

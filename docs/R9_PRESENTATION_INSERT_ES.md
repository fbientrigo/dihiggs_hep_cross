# Inserto de presentación — R9

## Diapositiva 1 — De la idea al recast completo

**Pregunta:** ¿un escalar \(H_2\) long-lived del 2HDM puede producir una señal
observable en la búsqueda ATLAS DV+jets?

```text
2HDMC → UFO → MadGraph → Pythia → recast ATLAS DV+jets
```

- Punto: `H2scan_mH150_tb300000`, \(m_{H_2}=150\) GeV,
  \(c\tau=4.326\) mm.
- Acoplamiento, lifetime y branching ratios derivados del mismo punto 2HDMC.
- El resultado llega hasta una aceptancia y una tasa física esperada.

## Diapositiva 2 — Resultado validado R8

| Cantidad | Resultado |
|---|---:|
| Trackless \(A\times\epsilon\) | **1.573386 %** |
| \(\sigma_{visible}\) | 0.00207493 fb |
| Eventos esperados a 139 fb\(^{-1}\) | **0.288** |
| High-\(p_T\) | estadística MC insuficiente |
| Exclusión R8 | no evaluada |

**Lectura:** la señal sí atraviesa el análisis. La aceptancia es no nula y
MC-estadísticamente resuelta. El problema es la tasa de producción derivada
del modelo.

## Diapositiva 3 — Umbral oficial y respuesta teórica

ATLAS, Tabla 6, región **Trackless jet SR**:

```text
observados = 0
fondo = 0.83 +0.51/-0.53
S95 observado = 3.0 eventos
límite σvisible = 0.022 fb
```

Para pasar de 0.288 a 3.0 eventos:

| Cantidad | Requerido |
|---|---:|
| Factor de tasa | **×10.402** |
| \(\kappa_g=|g|/|g_0|\) | **3.225** |
| \(|g_{hH_2H_2}|\) | **205.09 GeV** |
| Valor actual | 63.59 GeV |

El escalado \(\sigma\propto\kappa_g^2\) es estructuralmente exacto para el
UFO y proceso congelados.

Se varió solo \(M^2=m_{12}^2/(s_\beta c_\beta)\) en la slice fija

```text
mH2=150 GeV, mA=mH±=450 GeV, tanβ=3×10^5,
sin(β−α)=1, λ6=10^-10, λ7=0.
```

La ventana teóricamente válida da
\(\kappa_g\in[1-8.6\times10^{-11},1+2.7\times10^{-10}]\).
Al aumentar \(M^2\) falla positividad; al disminuirlo falla perturbatividad.

> **Respuesta:** el umbral oficial requiere \(|g|\simeq205.1\) GeV, pero no
> es alcanzable variando \(M^2\) en esta slice fija. El cuello de botella es
> la tasa de producción, no la aceptancia ni el lifetime dentro de la ventana
> válida.

# R9 — Umbral de sensibilidad del acoplamiento \(h-H_2-H_2\)

**Benchmark:** `H2scan_mH150_tb300000`  
**Estado:** `COMPLETE`  
**Conclusión de alcance:** `THRESHOLD_NOT_REACHABLE_IN_THE_TESTED_FIXED_SLICE`

## 1. Pregunta

R8 validó la cadena

```text
2HDMC → UFO → MadGraph → Pythia → recast ATLAS DV+jets
```

para un punto con \(m_{H_2}=150\) GeV y \(c\tau=4.326\) mm. La región
Trackless tiene una aceptancia no nula y estadísticamente resuelta,
\(A\times\epsilon=1.573386\%\), pero el punto predice solo

\[
N_0 = 0.288415
\]

eventos a \(139\,\mathrm{fb}^{-1}\).

R9 pregunta cuánto debe crecer el acoplamiento y si ese crecimiento es
alcanzable en la **slice fija estudiada**.

## 2. Escalado del acoplamiento

En el UFO y proceso congelados:

- `GHphiphi` aparece en un único acoplamiento;
- ese acoplamiento entra en un único vértice \(Hh_2h_2\);
- el proceso `g g > H > h2 h2` tiene un solo diagrama relevante;
- el ancho del mediador es externo y fijo;
- no hay interferencia ni cambio de espacio de fase.

Por ello,

\[
\sigma(\kappa_g)=\kappa_g^2\sigma_0
\]

es exacto dentro de este contrato. La validación numérica con cuatro runs
MadGraph queda pendiente para ejecución local; no es la base de la conclusión.

## 3. Umbral oficial de ATLAS

La Tabla 6 de ATLAS, *JHEP* 06 (2023) 200,
arXiv:2301.13866v3, reporta para **Trackless jet SR**:

| Cantidad | Valor |
|---|---:|
| Eventos observados | 0 |
| Fondo esperado | \(0.83^{+0.51}_{-0.53}\) |
| \(S^{95}_{obs}\) | 3.0 eventos |
| \(S^{95}_{exp}\) | \(3.4^{+1.3}_{-0.3}\) eventos |
| Límite observado en \(\sigma_{vis}\) | 0.022 fb |

Usando el valor exacto \(3/139\):

\[
\sigma_{vis}^{95}=0.021582733812950\,\mathrm{fb}.
\]

Respecto del benchmark:

\[
R_\sigma = \frac{3.0}{0.2884150102}=10.401678,
\qquad
\kappa_g=\sqrt{R_\sigma}=3.225163,
\]

\[
|g_{hH_2H_2}|_{req}=205.093\,\mathrm{GeV}.
\]

El umbral experimental corresponde por tanto a la fila ilustrativa de
**tres eventos**, no a la de un evento.

## 4. Alcanzabilidad en la slice estudiada

Se mantuvo fijo:

```text
mH2 = 150 GeV
mA = mH± = 450 GeV
tanβ = 3×10^5
sin(β−α) = 1
λ6 = 10^-10
λ7 = 0
```

y se varió únicamente \(m_{12}^2\), equivalentemente \(M^2\).

El scan de siete puntos encontró tres puntos teóricamente válidos:

\[
\kappa_g\in
[0.999999999914,\ 1.000000000274].
\]

El máximo válido es

\[
|g|_{max}=63.5914252182\,\mathrm{GeV},
\]

muy por debajo de \(205.093\) GeV.

- Al aumentar \(M^2\), falla primero **positividad**.
- Al disminuir \(M^2\), falla primero **perturbatividad**.
- Los puntos que alcanzan el umbral requieren
  \(\lambda_1\sim -3\times10^{10}\) y no son físicos.

La vida media y \(BR(H_2\to b\bar b)\) permanecen estables dentro de la
ventana válida, por lo que no se requiere un nuevo recast.

## 5. Interpretación

El resultado no demuestra que el umbral sea imposible en todo el 2HDM.
Demuestra que **no es alcanzable variando \(M^2\) en esta slice fija**.

El cuello de botella es la tasa de producción. En este benchmark, el gran
\(\tan\beta\) suprime los anchos fermiónicos Type-I y permite una vida media
milimétrica; no se establece aquí una ley global
\(c\tau\propto\tan^2\beta\).

## 6. Conclusión para la reunión

> La señal pasa el recast, pero el benchmark produce 0.288 eventos. El límite
> model-independent observado de ATLAS permite 3.0 eventos en Trackless.
> Alcanzarlo exige multiplicar la tasa por 10.4 y aumentar
> \(|g_{hH_2H_2}|\) de 63.6 a 205.1 GeV. En la slice fija estudiada, la
> región teóricamente válida mantiene el acoplamiento esencialmente fijo, de
> modo que el umbral no puede alcanzarse variando solamente \(M^2\).

## 7. Pendiente local no bloqueante

Ejecutar los cuatro puntos MadGraph \(\kappa_g=0.5,1,2,4\) con el deck
corregido. Esto comprueba operacionalmente el escalado estructural, pero no
cambia la conclusión de alcanzabilidad.

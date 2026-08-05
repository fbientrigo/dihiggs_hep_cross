# Diapositivas de Presentación — R10: Exploración Fenomenológica Efectiva en $(c\tau, g_{hH_2H_2}, \mathrm{BR}_{b\bar{b}})$

---

## Diapositiva 1: Variables Efectivas y Flujo de Trabajo Factorizado

### Marco de Exploración Independiente
* **Parámetros Efectivos Independientes**:
  * $c\tau_{\mathrm{mm}}$: Longitud propia de decaimiento del escalar desplazado $H_2$ ($12$ puntos de $0.3\text{ mm}$ a $1000\text{ mm} = 1\text{ m}$).
  * $g_{hH_2H_2}$ [GeV]: Acoplamiento trilineal de producción $h \to H_2 H_2$ ($6$ puntos de $40$ a $300\text{ GeV}$).
  * $\mathrm{BR}(H_2 \to b\bar{b})$: Fracción de ramificación física al estado final $b\bar{b}$ ($5$ puntos de $0.1$ a $1.0$).
* **Proceso Fijo**: $pp \to H_2 H_2 \to (b\bar{b})(b\bar{b})$ a $\sqrt{s} = 13$ TeV, $m_{H_2} = 150$ GeV, $L = 139\text{ fb}^{-1}$.
* **Etiquetado Obligatorio**: Todos los puntos se clasifican como `EFFECTIVE_PHENOMENOLOGICAL`. No derivan de $\tan\beta$ o $m_{12}^2$ ni imponen restricciones teóricas del 2HDM (no mapeados aún a puntos 2HDM válidos).

### Factorización de Selección y Eficiencia
$$\sigma_{\text{visible}}(c\tau, g, \mathrm{BR}_{b\bar{b}}) = \sigma_{\text{producción}}(g) \times 1000\,\frac{\text{fb}}{\text{pb}} \times \mathrm{BR}(H_2 \to b\bar{b})^2 \times (A \times \epsilon)_{\text{Trackless}}(c\tau)$$

$$N_{\text{esperado}}(c\tau, g, \mathrm{BR}_{b\bar{b}}) = 139\text{ fb}^{-1} \times \sigma_{\text{visible}}(c\tau, g, \mathrm{BR}_{b\bar{b}})$$

* **Predicción Estructural de Sección Eficaz**: La normalización $\sigma(g) = \sigma_0 (g/g_0)^2$ utiliza la escala cuadrática analítica exacta anclada al punto de referencia validado (`STRUCTURAL_PREDICTION_ONLY`).
* **Muestra Condicional Forzada**: Muestra Pythia $H_2 \to b\bar{b}$ forzada al 100% (2000 eventos/punto), aplicando $\mathrm{BR}_{b\bar{b}}^2$ en la normalización algebraica sobre la malla de 360 puntos.

---

## Diapositiva 2: Eficiencia Trackless en el Régimen de Centímetros a Metros ($c\tau$)

![Eficiencia Trackless vs ctau](file:///home/fabi/atlas_dihiggs/hep_cross/results/r10_effective_ctau_g_br_scan/efficiency_vs_ctau.png)

### Hallazgos Clave de Aceptación y Alcance Físico
* **Comportamiento No Monótono y Alcance a 1 metro**:
  * $c\tau = 0.3\text{ mm}$: 0 eventos seleccionados de 2000; la eficiencia no está resuelta y se registra un límite superior al 95% CL ($< 0.00150$).
  * $c\tau = 4.33\text{ mm}$ (Ancla R8/R9): $A \times \epsilon = 0.015734$ ($N_{\text{sel}} = 40$).
  * **Meseta de Eficiencia Estadísticamente Compatible ($c\tau = 10\text{--}30\text{ mm}$)**: Eficiencia entre **1.86%** ($c\tau = 10\text{ mm}$, $N_{\text{sel}} = 47$) y **1.86%** ($c\tau = 30\text{ mm}$, $N_{\text{sel}} = 48$).
  * **Escala de Metros ($c\tau = 100\text{--}1000\text{ mm}$)**:
    * $10\text{ cm}$ ($100\text{ mm}$): $A \times \epsilon = 0.014253$ ($N_{\text{sel}} = 47$).
    * $20\text{ cm}$ ($200\text{ mm}$): $A \times \epsilon = 0.009507$ ($N_{\text{sel}} = 40$).
    * $50\text{ cm}$ ($500\text{ mm}$): $A \times \epsilon = 0.003869$ ($N_{\text{sel}} = 24$).
    * $70\text{ cm}$ ($700\text{ mm}$): $A \times \epsilon = 0.003478$ ($N_{\text{sel}} = 17$).
    * **$1\text{ m}$ ($1000\text{ mm}$)**: $A \times \epsilon = 0.002464$ ($N_{\text{sel}} = 15$), **manteniendo sensibilidad de 1 evento** ($N = 1.76$ para $g = 300\text{ GeV}$).
* **Calidad Estadística**: Todos los puntos con $c\tau \ge 1.0\text{ mm}$ tienen $\ge 10$ eventos seleccionados y están etiquetados como `VALIDATED`.

---

## Diapositiva 3: Mapa de Sensibilidad Efectiva en la Malla de 360 Puntos

![Sensibilidad Efectiva en ctau vs g](file:///home/fabi/atlas_dihiggs/hep_cross/results/r10_effective_ctau_g_br_scan/nexpected_ctau_vs_g_br_baseline.png)

### Cobertura Experimental en la Malla Extendida (360 Puntos)
* **Punto de Ancla Validado (R8/R9)**:
  * $c\tau_0 = 4.33\text{ mm}, g_0 = 63.59\text{ GeV}, \mathrm{BR}_0 = 0.757 \implies N_{\text{esperado}} = 0.288$ eventos (fuera del área de exclusión).
* **Umbral de 1 Evento Esperado ($N \ge 1.0$)**:
  * **68 puntos efectivos** en la malla alcanzan o superan $N_{\text{esperado}} \ge 1.0$ (extendiéndose hasta $c\tau = 1000\text{ mm} = 1\text{ m}$).
* **Umbral de Exclusión Observable ($S_{95} = 3.0$ eventos)**:
  * **26 puntos efectivos** alcanzan o superan el umbral $S_{95} = 3.0$ eventos (extendiéndose hasta $c\tau \approx 200\text{ mm} = 20\text{ cm}$).
  * El máximo absoluto de la malla (a $\mathrm{BR} = 1.0$, $g = 300\text{ GeV}$, $c\tau = 10\text{ mm}$) alcanza **$N = 13.27$ eventos**.

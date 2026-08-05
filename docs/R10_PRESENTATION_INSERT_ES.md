# Diapositivas de Presentación — R10: Exploración Fenomenológica Efectiva en $(c\tau, g_{hH_2H_2}, \mathrm{BR}_{b\bar{b}})$

---

## Diapositiva 1: Variables Efectivas y Flujo de Trabajo Factorizado

### Marco de Exploración Independiente
* **Parámetros Efectivos Independientes**:
  * $c\tau_{\mathrm{mm}}$: Longitud propia de decaimiento del escalar desplazado $H_2$.
  * $g_{hH_2H_2}$ [GeV]: Acoplamiento trilineal de producción $h \to H_2 H_2$.
  * $\mathrm{BR}(H_2 \to b\bar{b})$: Fracción de ramificación física al estado final $b\bar{b}$.
* **Proceso Fijo**: $pp \to H_2 H_2 \to (b\bar{b})(b\bar{b})$ a $\sqrt{s} = 13$ TeV, $m_{H_2} = 150$ GeV, $L = 139\text{ fb}^{-1}$.
* **Etiquetado Obligatorio**: Todos los puntos se clasifican como `EFFECTIVE_PHENOMENOLOGICAL`. No derivan de $\tan\beta$ o $m_{12}^2$ ni imponen restricciones teóricas del 2HDM (no mapeados aún a puntos 2HDM válidos).

### Factorización de Selección y Eficiencia
$$\sigma_{\text{visible}}(c\tau, g, \mathrm{BR}_{b\bar{b}}) = \sigma_{\text{producción}}(g) \times 1000\,\frac{\text{fb}}{\text{pb}} \times \mathrm{BR}(H_2 \to b\bar{b})^2 \times (A \times \epsilon)_{\text{Trackless}}(c\tau)$$

$$N_{\text{esperado}}(c\tau, g, \mathrm{BR}_{b\bar{b}}) = 139\text{ fb}^{-1} \times \sigma_{\text{visible}}(c\tau, g, \mathrm{BR}_{b\bar{b}})$$

* **Predicción Estructural de Sección Eficaz**: La normalización $\sigma(g) = \sigma_0 (g/g_0)^2$ utiliza la escala cuadrática analítica exacta anclada al punto de referencia validado (`STRUCTURAL_PREDICTION_ONLY`).
* **Muestra Condicional Forzada**: Muestra Pythia $H_2 \to b\bar{b}$ forzada al 100% (2000 eventos/punto), aplicando $\mathrm{BR}_{b\bar{b}}^2$ en la normalización algebraica sobre la malla de 240 puntos.

---

## Diapositiva 2: Eficiencia Trackless en Función del Tiempo de Vida ($c\tau$)

![Eficiencia Trackless vs ctau](file:///home/fabi/atlas_dihiggs/hep_cross/results/r10_effective_ctau_g_br_scan/efficiency_vs_ctau.png)

### Hallazgos Clave de Aceptación
* **Comportamiento No Monótono**:
  * $c\tau = 0.3\text{ mm}$: 0 eventos seleccionados de 2000; la eficiencia no está resuelta y se requiere un límite superior.
  * $c\tau = 4.33\text{ mm}$ (Ancla R8/R9): $A \times \epsilon = 0.015734$ ($N_{\text{sel}} = 40$).
  * **Meseta de Eficiencia Estadísticamente Compatible ($c\tau = 10\text{--}30\text{ mm}$)**: Eficiencia entre **1.86%** ($c\tau = 10\text{ mm}$, $N_{\text{sel}} = 47$) y **1.86%** ($c\tau = 30\text{ mm}$, $N_{\text{sel}} = 48$).
  * $c\tau = 300\text{ mm}$: Disminución a **0.69%**, consistente con un mayor número de decaimientos ocurriendo fuera del volumen fiducial de vértices desplazados.
* **Calidad Estadística**: Todos los puntos con $c\tau \ge 1.0\text{ mm}$ tienen $\ge 10$ eventos seleccionados y están etiquetados como `VALIDATED`.

---

## Diapositiva 3: Mapa de Sensibilidad Efectiva en el Plano $(c\tau, g_{hH_2H_2})$

![Sensibilidad Efectiva en ctau vs g](file:///home/fabi/atlas_dihiggs/hep_cross/results/r10_effective_ctau_g_br_scan/nexpected_ctau_vs_g_br_baseline.png)

### Regiones Experimentalmente Relevantes en la Malla de 240 Puntos
* **Punto de Ancla Validado (R8/R9)**:
  * $c\tau_0 = 4.33\text{ mm}, g_0 = 63.59\text{ GeV}, \mathrm{BR}_0 = 0.757 \implies N_{\text{esperado}} = 0.288$ eventos (fuera del área de exclusión).
* **Umbral de 1 Evento Esperado ($N \ge 1.0$)**:
  * **54 puntos efectivos** en la malla alcanzan o superan $N_{\text{esperado}} \ge 1.0$.
* **Umbral de Exclusión Observable ($S_{95} = 3.0$ eventos)**:
  * **23 puntos efectivos** alcanzan o superan el umbral $S_{95} = 3.0$ eventos.
  * Para el $\mathrm{BR}$ de ancla ($0.757$), el máximo rinde **$N = 7.60$ eventos** a $g = 300\text{ GeV}$ y $c\tau = 10\text{ mm}$.
  * El máximo absoluto de la malla (a $\mathrm{BR} = 1.0$, $g = 300\text{ GeV}$, $c\tau = 10\text{ mm}$) alcanza **$N = 13.27$ eventos**.

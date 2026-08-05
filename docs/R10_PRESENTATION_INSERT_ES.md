# Diapositivas de Presentación — R10: Exploración Fenomenológica Efectiva en $(c\tau, g_{hH_2H_2}, \mathrm{BR}_{b\bar{b}})$

---

## Diapositiva 1: Variables Efectivas y Flujo de Trabajo Factorizado

### Marco de Exploración Independiente
* **Parámetros Efectivos Independientes**:
  * $c\tau_{\mathrm{mm}}$: Longitud propia de decaimiento del escalar desplazado $H_2$.
  * $g_{hH_2H_2}$ [GeV]: Acoplamiento trilineal de producción $h \to H_2 H_2$.
  * $\mathrm{BR}(H_2 \to b\bar{b})$: Fracción de ramificación física al estado final $b\bar{b}$.
* **Proceso Fijo**: $pp \to H_2 H_2 \to (b\bar{b})(b\bar{b})$ a $\sqrt{s} = 13$ TeV, $m_{H_2} = 150$ GeV, $L = 139\text{ fb}^{-1}$.
* **Etiquetado Obligatorio**: Todos los puntos se clasifican como `EFFECTIVE_PHENOMENOLOGICAL`. No derivan de $tan\beta$ o $m_{12}^2$ ni imponen restricciones teóricas del 2HDM.

### Factorización de Selección y Eficiencia
$$\sigma_{\text{visible}}(c\tau, g, \mathrm{BR}_{b\bar{b}}) = \sigma_{\text{producción}}(g) \times 1000\,\frac{\text{fb}}{\text{pb}} \times \mathrm{BR}(H_2 \to b\bar{b})^2 \times (A \times \epsilon)_{\text{Trackless}}(c\tau)$$

$$N_{\text{esperado}}(c\tau, g, \mathrm{BR}_{b\bar{b}}) = 139\text{ fb}^{-1} \times \sigma_{\text{visible}}(c\tau, g, \mathrm{BR}_{b\bar{b}})$$

* **Evaluación Eficiente**: Muestra forzada $H_2 \to b\bar{b}$ al 100% en simulación (2000 eventos/punto de $c\tau$), escalado analítico en $g$ y $\mathrm{BR}_{b\bar{b}}$ sobre una malla cartesiana de 240 puntos.

---

## Diapositiva 2: Eficiencia Trackless en Función del Tiempo de Vida ($c\tau$)

![Eficiencia Trackless vs ctau](file:///home/fabi/atlas_dihiggs/hep_cross/results/r10_effective_ctau_g_br_scan/efficiency_vs_ctau.png)

### hallazgos Clave de Aceptación
* **Comportamiento No Monótono**:
  * $c\tau = 0.3\text{ mm}$: Prácticamente cero aceptación ($A \times \epsilon = 0.0000$, $N_{\text{sel}} = 0$).
  * $c\tau = 4.33\text{ mm}$ (Ancla R8/R9): $A \times \epsilon = 0.015734$ ($N_{\text{sel}} = 40$).
  * **Ventana Óptima ($c\tau = 10\text{--}30\text{ mm}$)**: Eficiencia máxima del **1.86%** ($A \times \epsilon = 0.018625$, $N_{\text{sel}} = 48$).
  * $c\tau = 300\text{ mm}$: Caída a **0.69%** debido a decaimientos fuera del volumen del detector de trazas.
* **Calidad Estadística**: Todos los puntos con $c\tau \ge 1.0\text{ mm}$ superan los 10 eventos seleccionados y están marcados como `VALIDATED`.

---

## Diapositiva 3: Mapa de Sensibilidad Efectiva en el Plano $(c\tau, g_{hH_2H_2})$

![Sensibilidad Efectiva en ctau vs g](file:///home/fabi/atlas_dihiggs/hep_cross/results/r10_effective_ctau_g_br_scan/nexpected_ctau_vs_g_br_baseline.png)

### Regiones Experimentalmente Relevantes ($\mathrm{BR}_{b\bar{b}} = 0.757$)
* **Punto de Ancla Validado (R8/R9)**:
  * $c\tau_0 = 4.33\text{ mm}, g_0 = 63.59\text{ GeV} \implies N_{\text{esperado}} = 0.288$ eventos (por debajo del límite observable).
* **Umbral de 1 Evento Esperado ($N \ge 1$)**:
  * Se alcanza con $g \ge 150\text{ GeV}$ en la región de tiempo de vida $c\tau \in [3, 100]\text{ mm}$.
* **Umbral de Exclusión Observable ($S_{95} = 3.0$ eventos)**:
  * Se alcanza exactamente en $g \approx 205.1\text{ GeV}$ para el $c\tau_0$ de ancla ($205.1\text{ GeV} \implies N = 3.00$).
  * Para $g = 300\text{ GeV}$ y $c\tau \in [3, 30]\text{ mm}$, el número de eventos esperados alcanza hasta **$N = 18.6$**, superando ampliamente el límite experimental de ATLAS ($S_{95} = 3$).

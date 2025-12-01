# 🔬 Laboratorio 3: Caracterización de un Sistema LTI (Circuito RC)

[![Course](https://img.shields.io/badge/Curso-Señales%20y%20Sistemas%202025-blue)](/)
[![Project Status](https://img.shields.io/badge/Estado-Completado-green)](/)

## 📝 Introducción

Este proyecto documenta el **Laboratorio 3** de la asignatura **Señales y Sistemas**. El objetivo principal fue construir y analizar un **Circuito RC** para modelar y caracterizar un **Sistema Lineal e Invariante en el Tiempo (LTI)**.

El trabajo se centró en la validación de conceptos de identificación de sistemas, comparando las **respuestas teóricas** obtenidas a partir del modelo matemático con las **mediciones experimentales** del circuito físico.

## 🎯 Objetivo

El objetivo de este laboratorio fue **validar los conceptos de identificación de sistemas** (LTI) abordados en la materia, mediante la realización de medidas experimentales para caracterizar el sistema a través de su **respuesta al impulso** $h(t)$ y su **respuesta en frecuencia** $H(j\omega)$.

## ⚙️ Sistema Estudiado: Circuito RC

El sistema físico analizado fue un circuito RC simple, donde la **entrada** $V(t)$ es el voltaje aplicado y la **salida** $V_c(t)$ es el voltaje en el capacitor.


El sistema se describe mediante la siguiente **Ecuación Diferencial Lineal de Coeficientes Constantes**:

$$
V(t) = RC\frac{dV_c}{dt} + V_c(t)
$$

## 🧪 Metodología y Actividades

El laboratorio se dividió en dos actividades principales:

### Actividad 1: Respuesta Temporal e Impulso

Se estudió la respuesta del sistema frente a diferentes señales de entrada, analizando la salida tanto teórica como empíricamente:

* **Entradas utilizadas**: Impulso, Escalón y Pulso Rectangular.
* **Resultados clave**: Se analizó la constante de tiempo ($\tau$) del circuito y su relación con la respuesta transitoria del sistema.

### Actividad 2: Respuesta en Frecuencia ($H(j\omega)$)

Se evaluó la respuesta en frecuencia del circuito ($|H(j\omega)|$ y $\arg(H(j\omega))$) para diferentes configuraciones de componentes y un rango de frecuencias.

| Parámetros del Circuito | Rango de Frecuencias |
| :--- | :--- |
| **Circuito 1** | $R=1.6k\Omega$ y $C=2.2\mu F$ |
| **Circuito 2** | $R=160\Omega$ y $C=2.2\mu F$ |
| **Frecuencias** | De $5\text{ Hz}$ a $5000\text{ Hz}$ |

Se registraron las amplitudes y el retraso temporal (Delay) entre la señal de entrada y la de salida para completar las tablas de medición.

## 🛠️ Herramientas y Requisitos

Para replicar el trabajo o revisar los resultados:

### Hardware (Experimental)
* **Circuito Físico**: Protoboard, Resistencia ($R$) y Capacitor ($C$).
* **Generador de Funciones**: Para inyectar las señales de entrada (senoidales, pulsos, etc.).
* **Osciloscopio Digital**: Utilizado para la medición de amplitud y retraso (GW Instek, GDS-1000A-U Series).

### Software (Teórico y Gráfico)
* **Herramienta Informática**: Utilizada para la predicción teórica y la graficación comparativa de datos. (Comúnmente se usa MATLAB o Python/NumPy/SciPy).
* **GeoGebra**: Utilizado para la visualización de funciones y datos.

## 🔑 Conclusiones

La experiencia permitió **validar los conceptos teóricos** sobre el comportamiento de sistemas LTI, concretamente el circuito RC, mediante la experimentación. Aunque se encontraron algunas discrepancias menores atribuibles a imperfecciones del circuito o el proceso de medida (uso de cursores), se logró **fortalecer la comprensión de los modelos matemáticos** aplicados a sistemas físicos dinámicos.

## 📂 Estructura del Repositorio

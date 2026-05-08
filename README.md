# Sistema Paralelo y Distribuido de Detección de Fraude Bancario en Tiempo Real

## Descripción

Este proyecto implementa un sistema concurrente y paralelo de detección de fraude bancario en tiempo real utilizando Python.

El sistema simula múltiples cajeros automáticos (ATMs) generando transacciones simultáneamente y analiza posibles anomalías financieras mediante procesamiento paralelo y técnicas de concurrencia avanzadas.

El proyecto combina distintas tecnologías de programación paralela y distribuida:

- Asincronía con `asyncio`
- Paralelismo real con `multiprocessing`
- Comunicación entre procesos (IPC)
- Memoria compartida
- Exclusión mutua y sincronización
- Patrón productor-consumidor

El objetivo principal es demostrar el uso conjunto de varios paradigmas de concurrencia aplicados a un caso realista de procesamiento masivo de transacciones bancarias.

---

# Requisitos

Para ejecutar el proyecto se necesita:

- Python 3.10 o superior
- pip
- Biblioteca NumPy

---

# Instalación

## 1. Clonar o descargar el proyecto

```bash
git clone <url-del-repositorio>
cd proyecto-fraude
```

También se puede descargar el archivo `.zip` del proyecto y descomprimirlo manualmente.

---

## 2. Crear entorno virtual (opcional pero recomendado)

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3. Instalar dependencias

```bash
pip install numpy
```

---

# Ejecución

Para ejecutar el sistema:

```bash
python entregaindividualfinal.py
```
> Nota:
> El programa utiliza multiprocessing, por lo que debe ejecutarse directamente desde el archivo principal `entregaindividualfinal.py`.

---

# Funcionamiento General

El sistema sigue el siguiente flujo:

1. Múltiples cajeros automáticos generan transacciones de forma asíncrona.
2. Las transacciones se almacenan en una cola concurrente.
3. Un dispatcher agrupa las transacciones en lotes.
4. Los lotes se procesan en paralelo utilizando múltiples procesos.
5. Cada proceso calcula un score de anomalía para detectar posibles fraudes.
6. Si se detecta una transacción sospechosa:
   - la cuenta se añade a una blacklist compartida,
   - se envía una alerta al monitor central.
7. El monitor imprime las alertas en tiempo real.
8. Finalmente se muestran métricas de rendimiento del sistema.

---

# Tecnologías y Técnicas Utilizadas

## Asyncio

Se utiliza `asyncio` para simular múltiples fuentes de datos concurrentes sin bloquear el programa principal.

## Multiprocessing

El análisis matemático de fraude se ejecuta utilizando múltiples procesos para aprovechar todos los núcleos disponibles del procesador.

## Shared Memory

El histórico de transacciones se comparte entre procesos usando memoria compartida para evitar copias innecesarias de datos.

## IPC (Inter Process Communication)

Los procesos se comunican mediante colas compartidas (`Queue`) para enviar alertas de fraude al monitor central.

## Sincronización

Se utilizan locks (`Lock`) para evitar condiciones de carrera al acceder a estructuras compartidas.

---

# Ejemplo de Ejecución

## Alertas de fraude

```text
[ALERTA] Fraude detectado
   Cuenta: 7421
   Score: 521.82
   Transacción: TX-ATM-4-17
   Cantidad: 4921.22€
   Ubicación: (74.20, -110.55)
   Hora: 2026-05-08 18:22:14
```

---

## Métricas de rendimiento

```text
============================================================
ANÁLISIS DE RENDIMIENTO - SISTEMA DE DETECCIÓN PARALELO
Total Transacciones: 1500
Tiempo total: 2.1481 segundos
Throughput: 698.29 tx/seg
Cuentas en lista negra: 93
============================================================
```

---

# Características Implementadas

El proyecto incluye:

- Generación asíncrona de transacciones.
- Procesamiento paralelo CPU-bound.
- Comunicación entre procesos.
- Uso de memoria compartida.
- Exclusión mutua.
- Patrón productor-consumidor.
- Monitorización en tiempo real.
- Análisis básico de rendimiento.

---

# Estructura del Proyecto

```text
proyecto/
│
├── entregaindividualfinal.py
├── README.md
└── Informe_Tecnico_Deteccion_Fraude_Paralela.pdf
```

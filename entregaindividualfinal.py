import asyncio
import multiprocessing
import time
import random
import numpy as np 
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import shared_memory
from dataclasses import dataclass
from typing import List, Tuple
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

@dataclass
class Transaction:
    tx_id: str
    account_id: int 
    amount: float
    location: Tuple[float, float]
    timestamp: float

# MODELO MATEMÁTICO 

def calculate_advanced_anomaly_score(tx: Transaction, history_data: np.ndarray, p: int = 3) -> float:
    """
    Calcula el score de anomalía basado en Minkowski. 
    Vectorizado con NumPy para simular carga real de alta intensidad (O(N)).
    """
    tx_vec = np.array([tx.amount, tx.location[0], tx.location[1]])
    
    # Cálculo de distancia de Minkowski: sum(|a - b|^p)^(1/p)
    diff = np.abs(history_data - tx_vec)
    distances = np.sum(diff**p, axis=1)**(1/p)
    
    # Aproximación a Local Outlier Factor (K-Nearest Neighbors)
    k = 20
    nearest_distances = np.partition(distances, k)[:k]
    return np.mean(nearest_distances)

# ESTADO COMPARTIDO Y WORKERS (Paralelismo)
_shared_blacklist = None
_shared_lock = None
_shm_info = None  
_result_queue = None

def init_worker(blacklist, lock, shm_info, res_queue):
    global _shared_blacklist, _shared_lock, _shm_info, _result_queue
    _shared_blacklist = blacklist
    _shared_lock = lock
    _shm_info = shm_info 
    _result_queue = res_queue

def process_batch(batch: List[Transaction]):
    shm_name, shape, dtype = _shm_info
    existing_shm = shared_memory.SharedMemory(name=shm_name)
    history_ref = np.ndarray(shape, dtype=dtype, buffer=existing_shm.buf)
    
    fraud_count = 0
    THRESHOLD = 450.0
    
    for tx in batch:
        with _shared_lock:
            if tx.account_id in _shared_blacklist: continue

        score = calculate_advanced_anomaly_score(tx, history_ref)

        if score > THRESHOLD:
            with _shared_lock:
                _shared_blacklist[tx.account_id] = score
            _result_queue.put((tx.account_id,score,tx.tx_id,tx.amount,tx.location,tx.timestamp))
            fraud_count += 1
            
    existing_shm.close() 
    return fraud_count


# MONITOR DE ALERTAS (Consumidor/Lector)

def alert_monitor_process(res_queue, stop_event):
    logging.info("Monitor de Fraude iniciado (Proceso Independiente).")
    while not stop_event.is_set() or not res_queue.empty():
        try:
            acc_id, score, tx_id, amount, location, timestamp = res_queue.get(timeout=0.2)
            readable_time = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            print(
            f"[ALERTA] Fraude detectado\n"
            f"   Cuenta: {acc_id}\n"
            f"   Score: {score:.2f}\n"
            f"   Transacción: {tx_id}\n"
            f"   Cantidad: {amount:.2f}€\n"
            f"   Ubicación: ({location[0]:.2f}, {location[1]:.2f})\n"
            f"   Hora: {readable_time}\n")
        except:
            continue
    logging.info("Monitor de Fraude cerrado.")

# GENERADOR ASÍNCRONO (Asyncio - Concurrencia I/O)

async def transaction_producer(name: str, out_queue: asyncio.Queue, count: int):
    """Simula múltiples fuentes de datos (ATMs) de forma asíncrona."""
    for i in range(count):
        await asyncio.sleep(random.uniform(0.001, 0.005)) # Simulación latencia de red
        tx = Transaction(
            tx_id=f"TX-{name}-{i}",
            account_id=random.randint(1, 10000),
            amount=random.uniform(1.0, 5000.0),
            location=(random.uniform(-90, 90), random.uniform(-180, 180)),
            timestamp=time.time()
        )
        await out_queue.put(tx)

# COORDINADOR PRINCIPAL
async def main():
    N_TRANSACTIONS_PER_ATM = 100
    N_ATMS = 15
    N_WORKERS = multiprocessing.cpu_count()

    # NUEVO BLOQUE DE MEMORIA COMPARTIDA
    history_raw = np.random.rand(50000, 3).astype(np.float64) * 1000
    
    shm = shared_memory.SharedMemory(create=True, size=history_raw.nbytes)
   
    history_shared = np.ndarray(history_raw.shape, dtype=history_raw.dtype, buffer=shm.buf)
    
    history_shared[:] = history_raw[:]
    
    #Contiene la "dirección" para los procesos hijos
    shm_info = (shm.name, history_raw.shape, history_raw.dtype)

    # Sincronización e IPC
    manager = multiprocessing.Manager()
    shared_blacklist = manager.dict()
    shared_lock = manager.Lock()
    result_queue = manager.Queue()
    stop_event = manager.Event()

    # Proceso Monitor
    monitor = multiprocessing.Process(target=alert_monitor_process, args=(result_queue, stop_event))
    monitor.start()

    start_time = time.perf_counter()
    
    # Uso de ProcessPoolExecutor para gestión de procesos worker
    with ProcessPoolExecutor(max_workers=N_WORKERS, initializer=init_worker, 
                         initargs=(shared_blacklist, shared_lock, shm_info, result_queue)) as executor:
        
        tx_queue = asyncio.Queue()
        loop = asyncio.get_running_loop()

        producers_tasks = [asyncio.create_task(transaction_producer(f"ATM-{i}", tx_queue, N_TRANSACTIONS_PER_ATM)) 
                          for i in range(N_ATMS)]
        
        async def dispatcher():
            pending_tasks = []
            await asyncio.gather(*producers_tasks)
            
            while not tx_queue.empty():
                batch = []
                while len(batch) < 50 and not tx_queue.empty():
                    batch.append(tx_queue.get_nowait())
                
                if batch:
                    task = loop.run_in_executor(executor, process_batch, batch)
                    pending_tasks.append(task)
            
            if pending_tasks:
                await asyncio.gather(*pending_tasks)

        await dispatcher()
        

    stop_event.set()
    monitor.join()
    # Para Liberar RAM del sistema 
    shm.close()
    try:
        shm.unlink()
    except Exception:
        pass
    
    duration = time.perf_counter() - start_time
    print("\n" + "="*60)
    print(f"ANÁLISIS DE RENDIMIENTO - SISTEMA DE DETECCIÓN PARALELO")
    print(f"Total Transacciones: {N_ATMS * N_TRANSACTIONS_PER_ATM}")
    print(f"Tiempo total: {duration:.4f} segundos")
    print(f"Throughput: {(N_ATMS * N_TRANSACTIONS_PER_ATM)/duration:.2f} tx/seg")
    print(f"Cuentas en lista negra: {len(shared_blacklist)}")
    print("="*60)
    print("\n" + "="*60)
    print(f"ANÁLISIS DE RENDIMIENTO - SISTEMA DE DETECCIÓN PARALELO")
    print(f"Total Transacciones: {N_ATMS * N_TRANSACTIONS_PER_ATM}")
    print(f"Tiempo total: {duration:.4f} segundos")
    print(f"Throughput: {(N_ATMS * N_TRANSACTIONS_PER_ATM)/duration:.2f} tx/seg")
    print(f"Cuentas en lista negra: {len(shared_blacklist)}")
    print("="*60)

    
if __name__ == "__main__":
    multiprocessing.freeze_support()
    asyncio.run(main())
import threading
import time
import random

# Estructura para manejar la conectividad entre nodos
connected_nodes = {
    0: [1, 2],
    1: [0],
    2: [0],
    3: [4],
    4: [3]
}

# Simular latencia de red aleatoria
def latencia_red():
    latencia = random.uniform(0.1, 0.5)
    time.sleep(latencia)
    return latencia

# Algoritmo de replicación de datos entre nodos (consistencia eventual)
class Node:
    def __init__(self, node_id):
        self.node_id = node_id
        self.data = {}
        self.log = []

    def put(self, key, value):
        latency = latencia_red()
        self.data[key] = value
        self.log.append((key, value))
        print(f"Nodo {self.node_id} ha puesto datos para Nodo {key[-1]} con latencia {latency:.4f} segundos")

    def get(self, key):
        return self.data.get(key, None)

    def replicate(self, other_node):
        for entry in self.log:
            other_node.data[entry[0]] = entry[1]
        other_node.log.extend(self.log)

# Implementación básica de Raft para consenso distribuido
class RaftNode(Node):
    def __init__(self, node_id):
        super().__init__(node_id)
        self.current_term = 0
        self.voted_for = None
        self.log = []

    def request_vote(self, term, candidate_id):
        if term > self.current_term:
            self.current_term = term
            self.voted_for = candidate_id
            return True
        return False

    def append_entries(self, term, leader_id, prev_log_index, prev_log_term, entries, leader_commit):
        if term >= self.current_term:
            self.current_term = term
            self.log.extend(entries)
            return True
        return False

    def replicate(self, other_node):
        entries = []
        for entry in self.log:
            entries.append(entry)
            if len(entries) == 5:  # Simular replicación de lotes de entradas
                other_node.append_entries(self.current_term, self.node_id, 0, 0, entries, 0)
                entries = []
        if entries:
            other_node.append_entries(self.current_term, self.node_id, 0, 0, entries, 0)

# Función para simular una partición de red
def simulate_particio_red():
    time.sleep(random.uniform(2, 5))
    print("¡Se ha producido una partición de red!")

# Función para simular la recuperación de la red
def simulate_recuperacion_red():
    time.sleep(random.uniform(2, 5))
    print("La red se ha recuperado.")

# Función para ejecutar un nodo con posibles fallos
def nodos_posibles_fallos(node):
    while True:
        # Simular fallos aleatorios en el nodo
        time.sleep(random.uniform(1, 3))
        if random.random() < 0.3:  # Probabilidad de 30% de fallo
            print(f"Nodo {node.node_id} ha fallado.")
            time.sleep(random.uniform(1, 3))
            print(f"Nodo {node.node_id} está reiniciando...")

# Función para ejecutar la simulación de red
def simulacion(max_iterations):
    nodes = [RaftNode(i) for i in range(len(connected_nodes))]
    threads = []

    # Crear hilos para ejecutar nodos con posibles fallos
    for node in nodes:
        thread = threading.Thread(target=nodos_posibles_fallos, args=(node,))
        thread.start()
        threads.append(thread)

    # Iterar sobre un número máximo de iteraciones
    for _ in range(max_iterations):
        # Simular operaciones entre nodos conectados
        for node in nodes:
            for recipient_id in connected_nodes[node.node_id]:
                node.put(f'key{recipient_id}', f'value{recipient_id}')

        # Simular partición de red
        print("¡Se ha producido una partición de red!")
        simulate_particio_red()

        # Simular replicación de datos en nodos afectados
        for node in nodes:
            if node.node_id == 3:
                node.replicate(nodes[4])

        # Simular recuperación de la red
        print("La red se está recuperando...")
        simulate_recuperacion_red()

        time.sleep(2) 

# Ejecutar la simulación con un máximo de 5 iteraciones
if __name__ == "__main__":
    max_iterations = 5
    simulacion(max_iterations)
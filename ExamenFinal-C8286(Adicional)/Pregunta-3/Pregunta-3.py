import threading
import time
import random


class Message:
    def __init__(self, sender, content, timestamp):
        self.sender = sender
        self.content = content
        self.timestamp = timestamp

class Node:
    def __init__(self, node_id, total_nodes, network):
        self.node_id = node_id
        self.total_nodes = total_nodes
        self.network = network
        self.clock = 0
        self.mutex = RicartAgrawalaMutex(node_id, total_nodes, network)
        self.processes = {}

    def send_message(self, recipient_id, content):
        message = Message(self.node_id, content, self.clock)
        recipient_node = self.network.get_node_by_id(recipient_id)
        recipient_node.receive_message(message)


    def send_reply(self, target_id):
        for node in self.network.nodes:
            if node.node_id == target_id:
                node.receive_reply(self.node_id)

    def receive_message(self, message):
        self.clock = max(self.clock, message.timestamp) + 1
        print(f"Mensaje recibido en Nodo {self.node_id}: {message.content}")

    def request_cs(self):
        self.mutex.request_access()

    def receive_request(self, request_clock, request_node_id):
        self.mutex.receive_request(request_clock, request_node_id)

    def receive_reply(self, sender_id):
        self.mutex.receive_reply(sender_id)

    def release_cs(self):
        self.mutex.leave_critical_section()

    def synchronize_clocks(self):
        # Implementación básica de sincronización de relojes
        max_clock = max([node.clock for node in self.network.nodes])
        self.clock = max_clock

    def garbage_collect(self):
        # Implementación básica de recolección de basura utilizando el algoritmo de Cheney
        collector = CheneyCollector(size=100)  # Tamaño de la memoria ficticio
        # Simulación de asignación y recolección de memoria
        for i in range(3):  # Simular 3 asignaciones
            addr = collector.allocate(f"Objeto {i}")
            print(f"Nodo {self.node_id} asignó objeto en dirección {addr}")
        collector.collect()
        print(f"Nodo {self.node_id} recolectó basura")

    def terminate_process_detection(self):
        # Implementación básica de detección de terminación de procesos distribuidos
        if not self.processes:
           return
        active_processes = [p for p in self.processes.values() if p.active]
        if not active_processes:
            print(f"Nodo {self.node_id}: Todos los procesos han terminado.")

    def add_process(self, process_id, neighbors):
        self.processes[process_id] = Process(process_id, neighbors)

    def start_processes(self):
        for process in self.processes.values():
            process.send_message(process.neighbors[0])

    def receive_process_message(self, sender_id, process_id):
        if process_id not in self.processes:
            self.add_process(process_id, neighbors=[sender_id])
        else:
            self.processes[process_id].send_message(self, sender_id)

    def remove_process(self, process_id):
        del self.processes[process_id]

# Algoritmo de Dijkstra-Scholten :

class Process:
    def __init__(self, process_id, neighbors):
        self.process_id = process_id
        self.neighbors = neighbors
        self.parent = None
        self.children = set()
        self.active = True

    def send_message(self, recipient):
        recipient.receive_message(self, self.process_id)

    def receive_message(self, sender, sender_id):
        if self.parent is None:
            self.parent = sender
        self.children.add(sender_id)
        self.process_task()

    def process_task(self):
        # Simulate task processing
        self.active = False
        self.check_termination()

    def check_termination(self):
        if not self.active and not self.children:
            if self.parent:
                self.parent.receive_termination(self.process_id)

    def receive_termination(self, child_id):
        self.children.remove(child_id)
        self.check_termination()


#Algoritmo RicartAgrawalaMutex

class RicartAgrawalaMutex:
    def __init__(self, node_id, num_nodes, network):
        self.node_id = node_id
        self.num_nodes = num_nodes
        self.clock = 0  # Reloj lógico del nodo
        self.request_queue = []  # Cola de solicitudes de acceso
        self.replies_received = 0  # Contador de respuestas recibidas
        self.network = network  # Referencia a la red de nodos

    def request_access(self):
        self.clock += 1  # Incrementa el reloj lógico antes de enviar la solicitud
        self.request_queue.append((self.clock, self.node_id))  # Añade la solicitud a la cola de solicitudes
        # Envía una solicitud de acceso a todos los demás nodos
        for node in self.network.nodes:
            if node.node_id != self.node_id:
                node.receive_request(self.clock, self.node_id)

    def receive_request(self, timestamp, sender_id):
        self.clock = max(self.clock, timestamp) + 1  # Actualiza el reloj lógico del nodo
        self.request_queue.append((timestamp, sender_id))  # Añade la solicitud a la cola de solicitudes
        self.request_queue.sort()  # Ordena la cola de solicitudes por timestamp
        self.send_reply(sender_id)  # Envía una respuesta al nodo solicitante

    def send_reply(self, target_id):
        for node in self.network.nodes:
            if node.node_id == target_id:
                node.receive_reply(self.node_id)  # Envía la respuesta al nodo destinatario

    def receive_reply(self, sender_id):
        self.replies_received += 1  # Incrementa el contador de respuestas recibidas
        # Si ha recibido respuestas de todos los demás nodos, ingresa a la sección crítica
        if self.replies_received == self.num_nodes - 1:
            self.enter_critical_section()

    def enter_critical_section(self):
        print(f"Nodo {self.node_id} ingresando a la sección crítica")
        self.leave_critical_section()

    def leave_critical_section(self):
        self.replies_received = 0  # Reinicia el contador de respuestas recibidas
        # Filtra la cola de solicitudes para eliminar la solicitud del propio nodo
        self.request_queue = [(t, n) for t, n in self.request_queue if n != self.node_id]
         # Verifica si hay nodos en la cola de solicitudes restantes para enviar respuestas
        if self.request_queue:
            timestamp, node_id = self.request_queue[0]  # Obtiene la primera solicitud en la cola
            self.send_reply(node_id)

        print(f"Nodo {self.node_id} dejando la sección crítica")



# Algoritmo de recolección de basura (Cheney)

class CheneyCollector:
    def __init__(self, size):
        self.size = size
        self.from_space = [None] * size
        self.to_space = [None] * size
        self.free_ptr = 0

    def allocate(self, obj):
        if self.free_ptr >= self.size:
            self.collect()
        addr = self.free_ptr
        self.from_space[addr] = obj
        self.free_ptr += 1
        return addr

    def collect(self):
        self.to_space = [None] * self.size
        self.free_ptr = 0
        for obj in self.from_space:
            if obj is not None:
                self.copy(obj)
        self.from_space, self.to_space = self.to_space, self.from_space

    def copy(self, obj):
        addr = self.free_ptr
        self.to_space[addr] = obj
        self.free_ptr += 1
        return addr




class Network:
    def __init__(self, num_nodes):
        self.num_nodes = num_nodes
        self.nodes = [Node(node_id, num_nodes, self) for node_id in range(num_nodes)]

    def get_node_by_id(self, node_id):
        return self.nodes[node_id]

    def start_network(self):
        for node in self.nodes:
            node.start_processes()

    def stop_network(self):
        for node in self.nodes:
            node.terminate_process_detection()
            node.garbage_collect()
        print("Red de nodos detenida.")

    def simulate_tasks(self):
        # Sincronizar los relojes de los nodos
        for node in self.nodes:
            node.synchronize_clocks()

        # Realizar solicitudes de exclusión mutua para acceder a recursos compartidos
        for node in self.nodes:
            node.request_cs()
            # Simular operaciones críticas aquí
            node.release_cs()

        # Realizar la recolección de basura en los nodos
        for node in self.nodes:
            node.garbage_collect()
            

        # Detener la red de nodos de manera ordenada
        self.stop_network()


# Ejemplo de uso
if __name__ == "__main__":
    network = Network(5)  # Crear una red con 5 nodos
    network.simulate_tasks()  # Ejecutar la simulación de tareas científicas

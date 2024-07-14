import threading
import time
import random
from collections import defaultdict

#Algoritmo Chandy-lamport

class Process:
    def __init__(self, process_id):
        self.process_id = process_id
        self.state = None
        self.channels = defaultdict(list)
        self.neighbors = []
        self.marker_received = {}
        self.local_snapshot = None
        self.lock = threading.Lock()

    def set_neighbors(self, neighbors):
        self.neighbors = neighbors
        for neighbor in neighbors:
            self.marker_received[neighbor.process_id] = False

    # Inicia una instantánea local del proceso
    def initiate_snapshot(self):
        with self.lock:
            self.local_snapshot = self.state
            print(f"Robot {self.process_id} taking local snapshot: {self.local_snapshot}")

    # Envía mensajes marcadores a los procesos vecinos
    def send_marker_messages(self):
        for neighbor in self.neighbors:
            self.send_message(neighbor, 'MARKER')

    def send_message(self, neighbor, message_type, content=None):
        message = (message_type, self.process_id, content)
        neighbor.receive_message(message)

    # Recibe mensajes y procesa marcadores
    def receive_message(self, message):
        message_type, sender_id, content = message
        with self.lock:
            if message_type == 'MARKER':
                if not self.marker_received[sender_id]:
                    self.marker_received[sender_id] = True
                    if self.local_snapshot is None:
                        self.local_snapshot = self.state
                        print(f"Robot {self.process_id} taking local snapshot: {self.local_snapshot}")
                        self.send_marker_messages()
                    else:
                        self.channels[sender_id].append(content)
                else:
                    self.channels[sender_id].append(content)
            else:
                if self.local_snapshot is not None:
                    self.channels[sender_id].append(content)
                else:
                    self.process_message(message)

    def process_message(self, message):
        # Simulate processing of a normal message
        print(f"Robot {self.process_id} received message from Robot {message[1]}: {message[2]}")

    def update_state(self, new_state):
        self.state = new_state


#Algoritmo de Raymond


class RaymondMutex:
    def __init__(self, node_id, parent=None):
        self.node_id = node_id
        self.parent = parent
        self.token_holder = (parent is None)
        self.request_queue = []

    def request_access(self):
        # Solicita acceso al recurso crítico
        if self.token_holder:
            self.enter_critical_section()
        else:
            self.request_queue.append(self.node_id)
            self.send_request_to_parent()

    def send_request_to_parent(self):
        if self.parent:
            self.parent.receive_request(self)

    def receive_request(self, requester):
        # Recibe solicitudes y maneja el envío del token
        if not self.token_holder:
            self.request_queue.append(requester.node_id)
            self.send_request_to_parent()
        elif requester.node_id == self.node_id:
            self.enter_critical_section()
        else:
            self.send_token(requester)

    def send_token(self, requester):
        self.token_holder = False
        requester.receive_token(self)

    def send_token_to_next_in_queue(self):
        next_node_id = self.request_queue.pop(0)
        next_node = [node for node in nodes if node.node_id == next_node_id][0]
        self.send_token(next_node)

    def enter_critical_section(self):
        # Entra a la sección crítica
        print(f"El Robot {self.node_id} ingresando a la seccion critica")
        self.leave_critical_section()

    def leave_critical_section(self):
         # Sale de la sección crítica y pasa el token si es necesario
        print(f"El Robot {self.node_id} dejando critical section")
        if self.request_queue:
            self.send_token_to_next_in_queue()


#Relojes Vectoriales

class VectorClock:
    def __init__(self, num_nodes, node_id):
        self.clock = [0] * num_nodes
        self.node_id = node_id

    def tick(self):
        self.clock[self.node_id] += 1

    def send_event(self):
        # Simula el envío de un evento y actualiza el reloj
        self.tick()
        return self.clock[:]

    def receive_event(self, received_vector):
        # Recibe un evento y actualiza el reloj vectorial
        for i in range(len(self.clock)):
            self.clock[i] = max(self.clock[i], received_vector[i])
        self.clock[self.node_id] += 1




#Recolerctor_Basura geracional

class GenerationalCollector:
    def __init__(self, size):
        # Inicializa el colector generacional con dos generaciones: joven y vieja
        self.size = size
        self.young_gen = [None] * size  
        self.old_gen = [None] * size    
        self.young_ptr = 0  
        self.old_ptr = 0    

    def allocate(self, obj, old=False):
        # Asigna un objeto en la generación especificada (joven por defecto)
        if old:
            # Asignación en la generación vieja
            if self.old_ptr >= self.size:
                # Si la generación vieja está llena, recolectar basura
                self.collect_old()
            addr = self.old_ptr
            self.old_gen[addr] = obj
            self.old_ptr += 1
        else:
            # Asignación en la generación joven
            if self.young_ptr >= self.size:
                # Si la generación joven está llena, recolectar basura
                self.collect_young()
            addr = self.young_ptr
            self.young_gen[addr] = obj
            self.young_ptr += 1
        return addr


    def collect_young(self):
        self.old_gen = self.old_gen + [obj for obj in self.young_gen if obj is not None]

        # Reinicia la generación joven
        self.young_gen = [None] * self.size
        self.young_ptr = 0

    def collect_old(self):
        # Recolección de basura en la generación vieja
        self.old_gen = [obj for obj in self.old_gen if obj is not None]
        self.old_ptr = len(self.old_gen)
        # Ajusta el tamaño de la generación vieja al tamaño original
        self.old_gen += [None] * (self.size - self.old_ptr)


#Sistema de coordinación de tareas en una red de robots industriales
if __name__=='__main__':

    #Instantáneas del estado global de los robots durante la ejecución de n tareas
    #En este caso 3 tareas
    processes = [Process(i) for i in range(3)]
    for i, process in enumerate(processes):
        neighbors = [p for j, p in enumerate(processes) if i != j]
        process.set_neighbors(neighbors)

    
    processes[0].update_state("State A")
    processes[1].update_state("State B")
    processes[2].update_state("State C")
    # Ejecución de toma de instantáneas
    processes[0].initiate_snapshot()

    time.sleep(1)
    processes[1].send_message(processes[0], 'MESSAGE', "Message 1 from R1 to R0")
    time.sleep(1)
    processes[2].send_message(processes[0], 'MESSAGE', "Message 2 from R2 to R0")
    time.sleep(1)
    processes[2].send_message(processes[1], 'MESSAGE', "Message 3 from R2 to R1")
    

    #Cordinación de recursos compartidos
    nodes = [RaymondMutex(i) for i in range(3)]
    nodes[0].parent = nodes[1]
    nodes[1].parent = nodes[2]

    # Simular que robot 0 quiere ingresar a la secciòn critica
    nodes[0].request_access()
    time.sleep(2)
    nodes[0].leave_critical_section()
        
    #Actualiza cada robot para mantener y utlizar relojes en la comunicación
    num_nodes = len(nodes)
    node1 = VectorClock(num_nodes, 0)
    node2 = VectorClock(num_nodes, 1)
    node3 = VectorClock(num_nodes, 2)

    # Evento en el nodo 1
    node1.tick()
    print(f" Reloj Robot 1 : {node1.clock}")

    # Ejecución de relojes vectoriales
    # Nodo 1 envía un mensaje a nodo 2
    msg = node1.send_event()
    node2.receive_event(msg)
    print(f"Reloj Robot 2 despues de recibir: {node2.clock}")

    # Evento en el nodo 3
    node3.tick()
    print(f"Reloj Robot 3 : {node3.clock}")
    
    #Gestión eficiente de la memoria en los nodos de control de los robots.
    # Ejecución de recolector de basura generacional
    collector = GenerationalCollector(10)
    addr1 = collector.allocate("obj1")
    print(f"Asignado en el obj1: {addr1}")
    collector.collect_young()
    print("Se completa la recoleccion de basura de la generacion joven")
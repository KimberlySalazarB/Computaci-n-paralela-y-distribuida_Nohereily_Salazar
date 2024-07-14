import asyncio
from queue import PriorityQueue
import threading
import logging

#Configuracion del bucle de eventos encargado de monitorear las corrutinas
#Con el formato de mensajes log que mostrará el mensaje
logging.basicConfig(level=logging.DEBUG, format=' %(message)s')

# Definimos el sistema de JupyterNotebook
class Jupyter_Notebook:
    def __init__(self):
        self.celdas = []
        self.evento_prio = PriorityQueue()
        self.lock = threading.Lock()
    
    # Se crea una corrutina que se encargará de la ejecución de celda
    async def ejecuta_celda(self, celda):
        try:
            await asyncio.sleep(2)  # Simula el tiempo de ejecución de la celda
            resultado = eval(celda['code'])  # Evalúa el código de la celda
            with self.lock:
                celda['output'] = resultado
                logging.debug(f"Ejecutada celda {celda['id']}:{resultado}")

        except Exception as e:
            logging.error(f"Error en ejecutar celda {celda['id']}: {e}")
    
    # Añadir celda a la lista de celdas
    def add_celda(self, codigo):
        with self.lock:
            celda_id = len(self.celdas) + 1
            celda = {'id': celda_id, 'code': codigo,'output':None}
            self.celdas.append(celda)
            logging.debug(f"Añadida nueva celda {celda_id}: {codigo}")
    
    # Manejar eventos de adición y ejecución de celdas
    def manejar_eventos(self, evento):
        try:
            if evento['type'] == 'execute':
                celda_id = evento['celda_id']
                with self.lock:
                    celda = next((c for c in self.celdas if c['id'] == celda_id), None)
                if celda:
                    asyncio.create_task(self.ejecuta_celda(celda))
            elif evento['type'] == 'add_cell':
                code = evento['code']
                self.add_celda(code)  
            else:
                logging.error(f"Tipo de evento desconocido {evento['type']}")

        except Exception as e:
            logging.error(f"Error en manejar el evento {evento['type']}: {e}")

    # Corrutina que se encarga de obtener y manejar eventos de la cola de eventos
    async def event_loop(self):
        while True:
            prioridad, evento = await self.obtener_evento()
            self.manejar_eventos(evento)
    
    # Corrutina que permite obtener el siguiente evento de la cola
    async def obtener_evento(self):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.evento_prio.get)
         
    # Añadir eventos a la cola de eventos con prioridad
    def add_evento(self, prioridad: int, event):
        self.evento_prio.put((prioridad, event))

# Ejemplo de añadir eventos a cola
async def main():
    jupy_notebook = Jupyter_Notebook()
    
    # Agregar eventos con diferentes prioridades y tipos
    jupy_notebook.add_evento(2,{'type': 'add_cell', 'code': 'print("Hola Mundo")'})
    jupy_notebook.add_evento(3,{'type': 'execute', 'celda_id': 1})
    jupy_notebook.add_evento(1,{'type': 'add_cell', 'code': '2 + 3'})
    jupy_notebook.add_evento(4,{'type': 'execute', 'celda_id': 2})
    jupy_notebook.add_evento(0,{'type': 'add_cell', 'code': '2/0'})
    jupy_notebook.add_evento(5,{'type': 'execute', 'celda_id': 3})


    await jupy_notebook.event_loop()

# Inicia el bucle de eventos del jupyter_notebook
if __name__ == "__main__":
    asyncio.run(main())








    

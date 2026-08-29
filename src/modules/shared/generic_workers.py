from pathlib import Path

from PySide6.QtCore import QObject, Signal, QRunnable

class WorkerSignals(QObject):
        
    finished = Signal(bytes, str) ## Podría hacerte un tipo de señal genérico
    error = Signal(str, str) ## Podría hacerte un tipo de señal genérico
    
class ServiceCallWorker(QRunnable):
    def __init__(self, service_function, image_path: Path, element_id: str):
        super().__init__()
        self.service_function = service_function
        self.image_path = image_path
        self.element_id = element_id
        self.signals = WorkerSignals()
        self.is_cancelled = False

    def cancel(self):
        self.is_cancelled = True

    def run(self):
        try:
            result = self.service_function(self.image_path)
            if self.is_cancelled: return
            self.signals.finished.emit(result, self.element_id)
        except Exception as error:
            self.signals.error.emit(str(error), self.element_id) 
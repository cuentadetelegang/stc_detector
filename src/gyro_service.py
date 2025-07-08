from kivy.clock import Clock
import random

class GyroService:
    def __init__(self, on_data, interval=0.05):
        self.on_data = on_data      
        self.interval = interval    
        self._event = None
        self._sensor = None         

    def start(self):
        try:
            from plyer import gyroscope
            gyroscope.enable()
            self._sensor = gyroscope
        except Exception:
            self._sensor = None     

        self._event = Clock.schedule_interval(self._read, self.interval)

    def stop(self):
        if self._event:
            self._event.cancel()
        if self._sensor:
            try:
                self._sensor.disable()
            except Exception:
                pass

    def _read(self, _dt):
        if self._sensor:
            x, y, z = self._sensor.rotation
            if (x, y, z) != (None, None, None):
                self.on_data(x, y, z)
        else:                       
            x = round(random.uniform(-3, 3), 2)
            y = round(random.uniform(-3, 3), 2)
            z = round(random.uniform(-3, 3), 2)
            self.on_data(x, y, z)



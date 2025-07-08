from kivy.app import App
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.graphics import Color, Rectangle

from db_manager import DatabaseManager
from gyro_service import GyroService
from stc_detector import calcular_riesgo


GREEN      = (.19, .74, .47, 1)
DARKGREEN  = (.10, .45, .28, 1)
TEXT_DARK  = (.15, .15, .15, 1)
LIGHT_GREY = (.95, .95, .95, 1)
Window.clearcolor = (1, 1, 1, 1)


def titulo(texto):
    cab = AnchorLayout(size_hint_y=None, height=dp(60))
    lab = Label(text=texto, color=(1, 1, 1, 1), font_size='20sp')
    cab.add_widget(lab)
    with cab.canvas.before:
        Color(*DARKGREEN)
        rect = Rectangle(size=cab.size, pos=cab.pos)
    cab.bind(pos=lambda *_: setattr(rect, 'pos', cab.pos),
             size=lambda *_: setattr(rect, 'size', cab.size))
    return cab


def campo(hint, **kw):
    return TextInput(
        hint_text=hint, multiline=False, **kw,
        background_color=LIGHT_GREY,
        foreground_color=TEXT_DARK,
        cursor_color=TEXT_DARK,
        padding=[10, 10, 10, 10],
        size_hint_y=None, height=dp(40)
    )


class MenuScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)

        anchor = AnchorLayout(anchor_x='center', anchor_y='top',
                              padding=[0, dp(10), 0, 0])

        box = BoxLayout(orientation='vertical',
                        padding=dp(25), spacing=dp(20),
                        size_hint=(1, None))

        box.add_widget(titulo('Detección de STC'))

        btn_nuevo = Button(text='Registrar nueva prueba',
                           background_color=GREEN, color=(1, 1, 1, 1),
                           size_hint_y=None, height=dp(50))
        btn_nuevo.bind(on_release=lambda *_:
                       setattr(self.manager, 'current', 'registro'))
        box.add_widget(btn_nuevo)

        btn_hist = Button(text='Ver historial',
                          background_color=GREEN, color=(1, 1, 1, 1),
                          size_hint_y=None, height=dp(50))
        btn_hist.bind(on_release=lambda *_:
                      setattr(self.manager, 'current', 'historial'))
        box.add_widget(btn_hist)

        box.height = dp(60) + 2 * dp(50) + 2 * dp(20)
        anchor.add_widget(box)
        self.add_widget(anchor)


class RegistroScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = BoxLayout(orientation='vertical',
                         padding=dp(25), spacing=dp(15))
        root.add_widget(titulo('Registro de paciente'))

        self.nombre = campo('Nombre completo')
        self.edad   = campo('Edad', input_filter='int')

        # Spinners
        self.genero = Spinner(text='Género',
                              values=['Masculino', 'Femenino'],
                              size_hint_y=None, height=dp(40),
                              background_color=LIGHT_GREY,
                              color=TEXT_DARK)
        self.mano   = Spinner(text='Mano dominante',
                              values=['Derecha', 'Izquierda'],
                              size_hint_y=None, height=dp(40),
                              background_color=LIGHT_GREY,
                              color=TEXT_DARK)

        for w in (self.nombre, self.edad, self.genero, self.mano):
            root.add_widget(w)

        self.aviso = Label(text='', color=(1, 0, 0, 1),
                           size_hint_y=None, height=dp(20))
        root.add_widget(self.aviso)

        btn = Button(text='Guardar y continuar',
                     background_color=GREEN, color=(1, 1, 1, 1),
                     size_hint_y=None, height=dp(50))
        btn.bind(on_release=self.guardar)
        root.add_widget(btn)
        self.add_widget(root)

    def guardar(self, _):
        if not all((self.nombre.text, self.edad.text,
                    self.genero.text in ('Masculino', 'Femenino'),
                    self.mano.text in ('Derecha', 'Izquierda'))):
            self.aviso.text = ' Completa todos los campos'
            return
        self.aviso.text = ''
        app = App.get_running_app()
        app.id_paciente = app.db.agregar_paciente(
            nombre=self.nombre.text,
            edad=int(self.edad.text),
            genero=self.genero.text,
            mano=self.mano.text
        )
        app.muestras = []
        app.sm.current = 'prueba'


class PruebaScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = BoxLayout(orientation='vertical',
                         padding=dp(25), spacing=dp(20))
        root.add_widget(titulo('Prueba'))

        self.lbl = Label(text="Pulsa 'Iniciar' y manten la mano lo mas quiera posible por 10 s.",
                         color=TEXT_DARK, font_size='18sp',
                         size_hint_y=None, height=dp(60))
        root.add_widget(self.lbl)

        self.btn = Button(text='Iniciar', background_color=GREEN,
                          color=(1, 1, 1, 1), size_hint_y=None,
                          height=dp(50))
        self.btn.bind(on_release=self.toggle)
        root.add_widget(self.btn)

        self.hist_btn = Button(text='Ver historial',
                               background_color=DARKGREEN,
                               color=(1, 1, 1, 1),
                               size_hint_y=None, height=dp(45))
        self.hist_btn.bind(on_release=lambda *_:
                           setattr(self.manager, 'current', 'historial'))
        root.add_widget(self.hist_btn)

        self.add_widget(root)

    def toggle(self, _):
        app = App.get_running_app()
        if self.btn.text == 'Iniciar':
            self.lbl.text = 'Capturando datos...'
            self.btn.text = 'Detener'
            app.muestras = []
            app.id_prueba = app.db.crear_prueba(app.id_paciente)
            try:
                app.gyro = GyroService(app._on_muestra)
                app.gyro.start()
            except Exception:
                pass
        else:
            try:
                app.gyro.stop()
            except Exception:
                pass
            idx = calcular_riesgo(app.muestras) if app.muestras else 0.3
            idx = max(0.1, min(idx, 1.0))   
            app.db.guardar_resultado(app.id_prueba, idx)

            if idx >= 0.6:
                self.lbl.color = (1, 0, 0, 1)
                self.lbl.text = f'Índice {idx:.2f}\nPosible STC'
            else:
                self.lbl.color = (0, .6, 0, 1)
                self.lbl.text = f'Índice {idx:.2f}\nResultado normal'
            self.btn.text = 'Iniciar'


class HistorialScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = BoxLayout(orientation='vertical',
                         padding=dp(25), spacing=dp(15))
        root.add_widget(titulo('Historial'))

        self.buscar = campo('Nombre exacto')
        root.add_widget(self.buscar)

        btn_buscar = Button(text='Buscar', background_color=GREEN,
                            color=(1, 1, 1, 1), size_hint_y=None,
                            height=dp(45))
        btn_buscar.bind(on_release=self.cargar)
        root.add_widget(btn_buscar)

        scroll = ScrollView()
        self.grid = GridLayout(cols=1, spacing=dp(8),
                               size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        scroll.add_widget(self.grid)
        root.add_widget(scroll)

        btn_back = Button(text='Volver', background_color=DARKGREEN,
                          color=(1, 1, 1, 1), size_hint_y=None,
                          height=dp(45))
        btn_back.bind(on_release=lambda *_:
                      setattr(self.manager, 'current', 'menu'))
        root.add_widget(btn_back)
        self.add_widget(root)

    def _msg(self, texto, color=(1, 0, 0, 1)):
        self.grid.add_widget(Label(text=texto, color=color,
                                   size_hint_y=None, height=dp(24)))

    def cargar(self, _):
        self.grid.clear_widgets()
        nombre = self.buscar.text.strip()
        if not nombre:
            self._msg('Introduce un nombre')
            return

        app = App.get_running_app()
        app.db.conectar()
        cur = app.db.conn.cursor()

        cur.execute(
            "SELECT id_paciente FROM pacientes WHERE nombre=%s",
            (nombre,)
        )
        ids = [row[0] for row in cur.fetchall()]

        if not ids:
            self._msg('No encontrado')
            return

        if len(ids) > 1:
            self._msg(f'⚠️ {len(ids)} pacientes con ese nombre:', color=(1, .5, 0, 1))
            for i in ids:
                self._msg(f'ID {i}', color=TEXT_DARK)
            self._msg('Refina tu búsqueda', color=TEXT_DARK)
            return

        id_pac = ids[0]
        historial = app.db.obtener_historial(id_pac)
        if not historial:
            self._msg('Sin pruebas registradas', color=TEXT_DARK)
            return

        for fecha, res in historial:
            txt = f"{fecha.strftime('%d/%m %H:%M')}  →  {res}"
            self.grid.add_widget(
                Label(text=txt, color=TEXT_DARK,
                      size_hint_y=None, height=dp(24))
            )


class STCApp(App):
    def build(self):
        self.db = DatabaseManager()
        self.id_paciente = None
        self.id_prueba = None
        self.muestras = []

        self.sm = ScreenManager(transition=SlideTransition(duration=.3))
        self.sm.add_widget(MenuScreen(name='menu'))
        self.sm.add_widget(RegistroScreen(name='registro'))
        self.sm.add_widget(PruebaScreen(name='prueba'))
        self.sm.add_widget(HistorialScreen(name='historial'))
        return self.sm

    def _on_muestra(self, x, y, z):
        self.muestras.append((x, y, z))
        self.db.guardar_muestra(self.id_prueba, x, y, z)


if __name__ == '__main__':
    STCApp().run()


import numpy as np

from urh.cythonext import signalFunctions
from urh.signalprocessing.Signal import Signal
from urh.ui.painting.SceneManager import SceneManager


class SignalSceneManager(SceneManager):
    def __init__(self, signal: Signal, parent, scene_type=0):
        super().__init__(parent)
        self.signal = signal
        self.scene_type = scene_type  # 0 = Analog Signal, 1 = QuadDemodView, 2 = QuadDemodView 2nd signal (for (O-)QPSK)

    def show_scene_section(self, x1: float, x2: float, subpath_ranges=None, colors=None):
        print("SignalSceneManager::show_scene_section() scene={0}".format(self.scene_type))
        if self.scene_type == 0:
            self.plot_data = self.signal.real_plot_data
        elif self.scene_type < 2:
            self.plot_data = self.signal.qad
        else:
            self.plot_data = self.signal.qad_2
        super().show_scene_section(x1, x2, subpath_ranges=subpath_ranges, colors=colors)

    def init_scene(self):
        stored_minimum, stored_maximum = self.minimum, self.maximum

        print("SignalSceneManager::init_scene() scene={0}".format(self.scene_type))
        if self.scene_type == 0:
            # Ensure Real plot have same y Axis
            self.plot_data = self.signal.real_plot_data
        else:
            mod_type = self.scene_type - 1 if self.scene_type < 2 else 0
            noise_val = signalFunctions.get_noise_for_mod_type(mod_type)
            # Bypass Min/Max calculation
            if noise_val == 0:
                # ASK
                self.minimum, self.maximum = 0, self.padding * np.max(self.signal.qad)
            else:
                self.minimum, self.maximum = 0, self.padding * noise_val

            self.plot_data = self.signal.qad if self.scene_type < 2 else self.signal.qad_2

        super().init_scene(apply_padding=self.scene_type == 0)
        self.minimum, self.maximum = stored_minimum, stored_maximum

        self.line_item.setLine(0, 0, 0, 0)  # Hide Axis

        if self.scene_type == 0:
            self.scene.draw_noise_area(self.signal.noise_min_plot, self.signal.noise_max_plot - self.signal.noise_min_plot)
        elif self.scene_type < 2:
            self.scene.draw_sep_area(-self.signal.qad_center)
        else:
            self.scene.draw_sep_area(-self.signal.qad_2_center)

    def scene(self, value):
        self.scene = value

    def eliminate(self):
        super().eliminate()
        # do not eliminate the signal here, as it would cause data loss in tree models!
        # if hasattr(self.signal, "eliminate"):
        #    self.signal.eliminate()
        self.signal = None

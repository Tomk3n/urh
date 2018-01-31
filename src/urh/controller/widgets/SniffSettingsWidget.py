import os
from PyQt5.QtCore import pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import QWidget, QCompleter, QDirModel

from urh import constants
from urh.dev.BackendHandler import BackendHandler
from urh.signalprocessing.ProtocolSniffer import ProtocolSniffer
from urh.ui.ui_send_recv_sniff_settings import Ui_SniffSettings
from urh.util.Errors import Errors
from urh.util.ProjectManager import ProjectManager


class SniffSettingsWidget(QWidget):
    sniff_setting_edited = pyqtSignal()
    sniff_file_edited = pyqtSignal()
    sniff_parameters_changed = pyqtSignal(dict)

    def __init__(self, device_name: str, project_manager: ProjectManager, signal=None, backend_handler=None,
                 network_raw_mode=False, real_time=False, parent=None):
        super().__init__(parent)
        self.ui = Ui_SniffSettings()
        self.ui.setupUi(self)

        self.project_manager = project_manager

        for encoding in self.project_manager.decodings:
            self.ui.comboBox_sniff_encoding.addItem(encoding.name)

        self.bootstrap(project_manager.device_conf, signal, enforce_default=True)

        self.sniffer = ProtocolSniffer(bit_len=self.ui.spinbox_sniff_BitLen.value(),
                                       center=self.ui.spinbox_sniff_Center.value(),
                                       noise=self.ui.spinbox_sniff_Noise.value(),
                                       tolerance=self.ui.spinbox_sniff_ErrorTolerance.value(),
                                       modulation_type=self.ui.combox_sniff_Modulation.currentIndex(),
                                       device=device_name,
                                       backend_handler=BackendHandler() if backend_handler is None else backend_handler,
                                       network_raw_mode=network_raw_mode,
                                       real_time=real_time)

        self.create_connects()
        self.ui.comboBox_sniff_encoding.currentIndexChanged.emit(self.ui.comboBox_sniff_encoding.currentIndex())
        self.ui.comboBox_sniff_viewtype.setCurrentIndex(constants.SETTINGS.value('default_view', 0, int))

        # Auto Complete like a Boss
        completer = QCompleter()
        completer.setModel(QDirModel(completer))
        self.ui.lineEdit_sniff_OutputFile.setCompleter(completer)

    def bootstrap(self, conf_dict: dict, signal=None, enforce_default=False):
        def set_val(widget, key: str, default):
            try:
                value = conf_dict[key]
            except KeyError:
                value = default if enforce_default else None

            if value is not None:
                if hasattr(widget, "setValue"):
                    widget.setValue(value)
                elif hasattr(widget, "setCurrentIndex"):
                    widget.setCurrentIndex(value)

        set_val(self.ui.spinbox_sniff_BitLen, "bit_len",  signal.bit_len if signal else 100)
        set_val(self.ui.spinbox_sniff_Center, "center", signal.qad_center if signal else 0.02)
        set_val(self.ui.spinbox_sniff_ErrorTolerance, "tolerance", signal.tolerance if signal else 5)
        set_val(self.ui.spinbox_sniff_Noise, "noise", signal.noise_threshold if signal else 0.001)
        set_val(self.ui.combox_sniff_Modulation, "modulation_index", signal.modulation_type if signal else 1)
        self.ui.comboBox_sniff_encoding.setCurrentText(conf_dict.get("decoding_name", ""))

        self.emit_editing_finished_signals()

    def create_connects(self):
        self.ui.spinbox_sniff_Noise.editingFinished.connect(self.on_noise_edited)
        self.ui.spinbox_sniff_Center.editingFinished.connect(self.on_center_edited)
        self.ui.spinbox_sniff_BitLen.editingFinished.connect(self.on_bit_len_edited)
        self.ui.spinbox_sniff_ErrorTolerance.editingFinished.connect(self.on_tolerance_edited)
        self.ui.combox_sniff_Modulation.currentIndexChanged.connect(self.on_modulation_changed)
        self.ui.comboBox_sniff_viewtype.currentIndexChanged.connect(self.on_view_type_changed)
        self.ui.lineEdit_sniff_OutputFile.editingFinished.connect(self.on_line_edit_output_file_editing_finished)
        self.ui.comboBox_sniff_encoding.currentIndexChanged.connect(self.on_combobox_sniff_encoding_index_changed)
        self.ui.checkBox_sniff_Timestamp.clicked.connect(self.on_checkbox_sniff_timestamp_clicked)

    def emit_editing_finished_signals(self):
        self.ui.spinbox_sniff_Noise.editingFinished.emit()
        self.ui.spinbox_sniff_Center.editingFinished.emit()
        self.ui.spinbox_sniff_BitLen.editingFinished.emit()
        self.ui.spinbox_sniff_ErrorTolerance.editingFinished.emit()
        self.ui.lineEdit_sniff_OutputFile.editingFinished.emit()

    def emit_sniff_parameters_changed(self):
        self.sniff_parameters_changed.emit(dict(bit_len=self.sniffer.signal.bit_len,
                                                center=self.sniffer.signal.qad_center,
                                                noise=self.sniffer.signal.noise_threshold,
                                                tolerance=self.sniffer.signal.tolerance,
                                                modulation_index=self.sniffer.signal.modulation_type,
                                                decoding_name=self.sniffer.decoder.name))

    @pyqtSlot()
    def on_noise_edited(self):
        self.sniffer.signal._noise_threshold = self.ui.spinbox_sniff_Noise.value()
        self.sniff_setting_edited.emit()

    @pyqtSlot()
    def on_center_edited(self):
        self.sniffer.signal.qad_center = self.ui.spinbox_sniff_Center.value()
        self.sniff_setting_edited.emit()

    @pyqtSlot()
    def on_bit_len_edited(self):
        self.sniffer.signal.bit_len = self.ui.spinbox_sniff_BitLen.value()
        self.sniff_setting_edited.emit()

    @pyqtSlot()
    def on_tolerance_edited(self):
        self.sniffer.signal.tolerance = self.ui.spinbox_sniff_ErrorTolerance.value()
        self.sniff_setting_edited.emit()

    @pyqtSlot(int)
    def on_modulation_changed(self, new_index: int):
        self.sniffer.signal.silent_set_modulation_type(new_index)
        self.sniff_setting_edited.emit()

    @pyqtSlot()
    def on_view_type_changed(self):
        self.sniff_setting_edited.emit()

    @pyqtSlot(int)
    def on_combobox_sniff_encoding_index_changed(self, index: int):
        if self.sniffer.decoder != self.project_manager.decodings[index]:
            self.sniffer.set_decoder_for_messages(self.project_manager.decodings[index])
            self.sniffer.decoder = self.project_manager.decodings[index]
            self.sniff_setting_edited.emit()

    @pyqtSlot()
    def on_line_edit_output_file_editing_finished(self):
        self.ui.lineEdit_sniff_OutputFile.setStyleSheet("")
        text = self.ui.lineEdit_sniff_OutputFile.text()
        if text and not text.endswith(".txt"):
            text += ".txt"
            self.ui.lineEdit_sniff_OutputFile.setText(text)

        if text and not os.path.isfile(text):
            try:
                open(text, "w").close()
            except Exception as e:
                self.ui.lineEdit_sniff_OutputFile.setStyleSheet("color:red;")
                return

        self.sniffer.sniff_file = text
        self.sniff_file_edited.emit()

    @pyqtSlot()
    def on_checkbox_sniff_timestamp_clicked(self):
        self.sniff_setting_edited.emit()

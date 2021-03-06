import os
import sys
import copy
import json
import time
import base64
import pkgutil

import logging
log = logging.getLogger(__name__)
logging.basicConfig(format='%(levelname)s: [%(filename)s:%(lineno)d] %(message)s', level=logging.INFO)

import argparse
import nostalgic
from enum import Enum
from .translation_dict import TranslationDict
from PySide2 import QtCore, QtWidgets, QtGui
from .widgets import TabSafeLineEdit, TextLabel


###########
# Globals #
###########
IS_DEV_DEBUG = True if os.getenv('DEV_DEBUG') in ['1', 'true', 'True'] else False

if IS_DEV_DEBUG:
    def my_excepthook(etype, value, tb):
        print(f"", flush=True)
        import traceback
        traceback.print_exception(etype, value, tb)
        print(f"Entering post-mortem debugger...\n", flush=True)
        import pdb; pdb.pm()

    sys.excepthook = my_excepthook

BLACK = QtGui.QColor(0, 0, 0)
GRAY  = QtGui.QColor(190, 190, 190)

APPLICATION_NAME       = "T-Rex Typer"
APPLICATION_ICON_BYTES = pkgutil.get_data(__name__, "resources/trex_w_board_48.png")

if sys.platform == "linux":
    SETTINGS_PATH = os.path.join(os.path.expanduser("~"), f".config/{APPLICATION_NAME}")

SETTINGS = nostalgic.Configuration(os.path.join(SETTINGS_PATH, f"{APPLICATION_NAME}.ini"))


class RunState(Enum):
    COMPLETE   = 0
    PRACTICING = 1
    READY      = 2


class SettingsWindow(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.settings = SETTINGS

        self.setMinimumWidth(600)

        self._modified = False
        self.setWindowTitle(f'Settings')
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)

        self.init_widgets()
        self.init_layout()

    def init_widgets(self):

        # wpm threshold
        self.wpm_threshold_label = QtWidgets.QLabel("WPM Miss Threshold:")
        self.wpm_threshold_label.setToolTip("Count multi-strokes slower than this as a miss")
        self.wpm_threshold_spinbox = QtWidgets.QSpinBox()
        self.settings.add_setting(
            "wpm_threshold",
            default=30,
            setter=self.wpm_threshold_spinbox.setValue,
            getter=self.wpm_threshold_spinbox.value)
        self.wpm_threshold_spinbox.setToolTip("Words per Minute")
        self.wpm_threshold_spinbox.setRange(0, 400)
        self.wpm_threshold_spinbox.setValue(self.settings.wpm_threshold)
        self.wpm_threshold_spinbox.valueChanged.connect(self.on_change)

        # dictionary directory
        self.dictionary_directory_label = QtWidgets.QLabel("Dictionary Directory:")
        self.dictionary_directory_label.setToolTip("Plover dictionary directory")
        self.dictionary_directory_line_edit = QtWidgets.QLineEdit()
        self.settings.add_setting(
            "dictionary_directory",
            default=os.path.expanduser("~"),
            setter=self.dictionary_directory_line_edit.setText,
            getter=self.dictionary_directory_line_edit.text)
        self.dictionary_directory_line_edit.textEdited.connect(self.on_change)

        # lesson directory
        self.lesson_directory_label = QtWidgets.QLabel("Lesson Directory:")
        # self.lesson_directory_label.setToolTip("Lesson directory")
        self.lesson_directory_line_edit = QtWidgets.QLineEdit()
        self.settings.add_setting(
            "lesson_directory",
            default=os.path.expanduser("~"),
            setter=self.lesson_directory_line_edit.setText,
            getter=self.lesson_directory_line_edit.text)
        self.lesson_directory_line_edit.textEdited.connect(self.on_change)

        # restore defaults
        self.restore_defaults_link = QtWidgets.QLabel('<a href=".">Restore defaults</a>')
        self.restore_defaults_link.setToolTip("Restore default settings")
        self.restore_defaults_link.linkActivated.connect(self.on_restore_defaults_link_activated)

        # button box
        self.button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok |
            QtWidgets.QDialogButtonBox.Cancel |
            QtWidgets.QDialogButtonBox.Apply)

        self.ok_button = self.button_box.buttons()[0]
        self.ok_button.setToolTip("Save changes and close window")
        self.button_box.accepted.connect(self.on_ok_clicked)

        self.cancel_button = self.button_box.buttons()[1]
        self.cancel_button.setToolTip("Close window without applying changes")
        self.button_box.rejected.connect(self.close)

        self.apply_button = self.button_box.buttons()[2]
        self.apply_button.setToolTip("Save changes")
        self.apply_button.setEnabled(False)

        self.apply_button.clicked.connect(self.apply_settings)

    def init_layout(self):
        self.grid_layout = QtWidgets.QGridLayout()

        # wpm threshold
        self.grid_layout.addWidget(self.wpm_threshold_label, 0, 0)
        self.grid_layout.addWidget(self.wpm_threshold_spinbox, 0, 1)
        # dictionary directory
        self.grid_layout.addWidget(self.dictionary_directory_label, 1, 0)
        self.grid_layout.addWidget(self.dictionary_directory_line_edit, 1, 1)
        # lesson directory
        self.grid_layout.addWidget(self.lesson_directory_label, 2, 0)
        self.grid_layout.addWidget(self.lesson_directory_line_edit, 2, 1)

        # restore defaults
        self.restore_defaults_layout = QtWidgets.QHBoxLayout()
        self.restore_defaults_layout.addWidget(QtWidgets.QWidget(), stretch=1)
        self.restore_defaults_layout.addWidget(self.restore_defaults_link)

        # button box
        self.button_layout = QtWidgets.QHBoxLayout()
        self.button_layout.addWidget(QtWidgets.QWidget(), stretch=1)
        self.button_layout.addWidget(self.button_box)

        # layout
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addLayout(self.grid_layout)
        self.layout.addWidget(QtWidgets.QWidget(), stretch=1)
        self.layout.addLayout(self.restore_defaults_layout)
        self.layout.addLayout(self.button_layout)
        self.setLayout(self.layout)

    def toggle_modified(self, status=True):
        if isinstance(status, bool):
            self._modified = not status

        if not self._modified:
            self.apply_button.setEnabled(True)
            self.setWindowTitle(f"Settings*")
            self._modified = True
        else:
            self.apply_button.setEnabled(False)
            self.setWindowTitle(f"Settings")
            self._modified = False

    def on_change(self, *args):
        if not self._modified:
            self.toggle_modified()

    def restore_defaults(self):
        non_application_keys = [k for k in self.settings._settings.keys() if k[:12] != 'application_']
        self.settings.set(keys=non_application_keys, use_defaults=True)
        self.toggle_modified(True)

    def apply_settings(self):
        self.settings.write()
        self.toggle_modified(False)
        log.info(f"Saved settings: {self.settings.config_file}")

    def on_restore_defaults_link_activated(self):
        self.restore_defaults()

    def on_ok_clicked(self):
        self.apply_settings()
        self.close()

    def closeEvent(self, event):
        event.accept()


class AboutWindow(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle(f'About {APPLICATION_NAME}')
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)

        self.init_widgets()
        self.init_layout()

    def init_widgets(self):
        self.icon_pixmap = QtGui.QPixmap()
        self.icon_pixmap.loadFromData(APPLICATION_ICON_BYTES)
        self.icon_label = QtWidgets.QLabel()
        self.icon_label.setPixmap(self.icon_pixmap)

        self.body_title = QtWidgets.QLabel(f'<h1>About</h1>')

        body_text = (
            f'<p>The {APPLICATION_NAME} is made by Matt Trzcinski.</p>'
            f'<hr>'
            f'<p>'
            f'<a href="https://icons8.com/icon/5vV_csnCe5Q2/kawaii-dinosaur">kawaii-dinosaur</a> and '
            f'<a href="https://icons8.com/icon/87796/keyboard">keyboard</a> by <a href="https://icons8.com">Icons8</a>.'
            f'</p>'
        )

        self.body = QtWidgets.QLabel(body_text)
        self.body.setOpenExternalLinks(True)
        self.body.setTextInteractionFlags(self.body.textInteractionFlags() |
                                          QtCore.Qt.TextSelectableByMouse)
        self.body.linkHovered.connect(self.on_hover)

    def init_layout(self):
        self.title_layout = QtWidgets.QHBoxLayout()
        self.title_layout.addWidget(self.icon_label)
        self.title_layout.addWidget(self.body_title)
        self.title_layout.addWidget(QtWidgets.QWidget(), stretch=1)

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addLayout(self.title_layout)
        self.layout.addWidget(self.body, stretch=1)
        self.setLayout(self.layout)

    def on_hover(self, link):
        if link:
            QtWidgets.QToolTip.showText(QtGui.QCursor.pos(), link)
        else:
            QtWidgets.QToolTip.hideText()

    def closeEvent(self, event):
        self.hide()


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle(APPLICATION_NAME)
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)

        self._dictionary = {}
        self.lesson_file = None

        self.text_raw     = ''
        self.text_split   = ()
        self.live_split   = []
        self.current_unit = ''

        self.missed      = 0
        self.last_time   = 0
        self.maybe_miss  = False
        self.is_miss     = False
        self.is_new_unit = True

        # Settings
        # NOTE: settings may be defined elsewhere because of
        # dependencies
        self.settings = SETTINGS

        self.settings.add_setting(
            "application_geometry",
            default=self.saveGeometry(),
            setter =self._set_geometry,
            getter =self._get_geometry)
        self.settings.add_setting(
            "application_state",
            default=self.saveState(),
            setter =self._set_state,
            getter =self._get_state)
        self.settings.add_setting(
            "application_size",
            default=[640, 480],
            setter =self._set_size,
            getter =self._get_size)
        self.settings.add_setting(
            "application_pos",
            default=self.pos(),
            setter =self._set_pos,
            getter =self._get_pos)
        self.settings.add_setting(
            "application_maximized",
            default=False,
            setter =self._set_maximized,
            getter =self._get_maximized)

        self.init_widgets()
        self.init_layout()

        self._load_settings(sync=True)
        self.settings_window.toggle_modified(False)

        # Debug
        if IS_DEV_DEBUG:
            self.line_edit.setFocus()
            self.settings.dictionary_directory = "/home/ahab/Projects/t_rex_typer/scratch/"
            self.settings.lesson_directory     = "/home/ahab/Projects/t_rex_typer/scratch/"
            self.on_settings_action()

        else:
            self.text_editor.setFocus()

    ##############
    # Properties #
    ##############
    def _get_run_state(self):
        return self._run_state

    def _set_run_state(self, value):
        self._run_state = value
        log.debug(f"{self._run_state=}")

    run_state = property(_get_run_state, _set_run_state)

    def init_widgets(self):

        ########
        # menu #
        ########

        self.open_action = QtWidgets.QAction('&Open', self)
        self.open_action.setShortcut('Ctrl+O')
        self.open_action.setToolTip('Open..')
        self.open_action.triggered.connect(self.on_open)

        self.save_action = QtWidgets.QAction('&Save', self)
        self.save_action.setEnabled(False)
        self.save_action.setShortcut('Ctrl+S')
        self.save_action.setToolTip('Save')
        self.save_action.triggered.connect(self.on_save)

        self.save_as_action = QtWidgets.QAction('Save &As..', self)
        self.save_as_action.setToolTip('Save As')
        self.save_as_action.setEnabled(False)
        self.save_as_action.triggered.connect(self.on_save_as)

        self.load_dictionary_action = QtWidgets.QAction('Load Dictionary..', self)
        self.load_dictionary_action.setToolTip('Load and replace the current dictionary')
        self.load_dictionary_action.triggered.connect(self.on_load_dictionary)

        self.settings_action = QtWidgets.QAction('&Settings..', self)
        self.settings_action.triggered.connect(self.on_settings_action)

        self.exit_action = QtWidgets.QAction('&Exit', self)
        if IS_DEV_DEBUG:
            self.exit_action.setShortcut("Escape")
        self.exit_action.setToolTip('Exit application')
        self.exit_action.triggered.connect(self.close)

        self.about_action = QtWidgets.QAction('&About', self)
        self.about_action.triggered.connect(self.on_about_action)

        self.menu_bar = self.menuBar()

        self.file_menu = self.menu_bar.addMenu('&File')
        self.file_menu.setToolTipsVisible(True)
        self.file_menu.aboutToShow.connect(self.on_file_menu_about_to_show)
        self.file_menu.addAction(self.open_action)
        self.file_menu.addAction(self.save_action)
        self.file_menu.addAction(self.save_as_action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.load_dictionary_action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.settings_action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.exit_action)

        self.help_menu = self.menu_bar.addMenu('&Help')
        self.help_menu.setToolTipsVisible(True)
        self.help_menu.addAction(self.about_action)

        ############
        # Non-menu #
        ############

        # no parent so that a separate window is used
        self.about_window = AboutWindow()
        self.settings_window = SettingsWindow()

        # Text viewer
        self.text_viewer = TextLabel(self)

        # Line edit
        self.line_edit = TabSafeLineEdit()
        self.line_edit.setEnabled(False)

        # setText doesn't trigger edited signal (only changed signal)
        self.line_edit.textEdited.connect(self.on_line_edit_text_edited)

        # Steno label
        self.steno_label = QtWidgets.QLabel('')

        # Text edit
        self.text_editor = QtWidgets.QTextEdit()
        self.text_editor.setPlaceholderText('Put practice words here..')
        self.text_editor.textChanged.connect(self.on_text_edit_changed)

        # start
        self.restart_button = QtWidgets.QPushButton("Restart")
        self.restart_button.pressed.connect(self.on_restart_button_pressed)

        if IS_DEV_DEBUG:
            text = ("It's the case that every effort has been made to 'replicate' this text as"
                    "faithfully as possible, including inconsistencies in spelling"
                    "and hyphenation.  Some corrections of spelling and punctuation"
                    "have been made. They are listed at the end of the text.")

            text = "this is a test"

            self.text_editor.setText(text)

    def init_layout(self):

        self.setGeometry(300, 300, 800, 400)

        # Frame top left
        self.ftl_layout = QtWidgets.QVBoxLayout()
        self.ftl_layout.setContentsMargins(2, 2, 2, 2)
        self.ftl_layout.addWidget(QtWidgets.QWidget(), stretch=1)
        self.ftl_layout.addWidget(self.text_viewer)

        self.frame_top_left = QtWidgets.QFrame()
        self.frame_top_left.setLayout(self.ftl_layout)

        # Frame middle left
        self.fml_layout = QtWidgets.QVBoxLayout()
        self.fml_layout.setContentsMargins(2, 2, 2, 2)
        self.fml_layout.addWidget(self.line_edit)
        self.fml_layout.addWidget(self.steno_label)
        self.fml_layout.addWidget(QtWidgets.QWidget(), stretch=1)

        self.frame_middle_left = QtWidgets.QFrame()
        self.frame_middle_left.setLayout(self.fml_layout)

        # Frame bottom left
        self.fbl_layout = QtWidgets.QVBoxLayout()
        self.fbl_layout.setContentsMargins(2, 2, 2, 2)
        self.fbl_layout.addWidget(self.text_editor)

        self.frame_bottom_left = QtWidgets.QFrame()
        self.frame_bottom_left.setLayout(self.fbl_layout)

        # Frame left
        self.fl_layout = QtWidgets.QVBoxLayout()
        self.fl_layout.setContentsMargins(0, 0, 0, 0)

        self.frame_left = QtWidgets.QFrame()
        self.frame_left.setLayout(self.fl_layout)
        self.frame_left.setFrameStyle(QtWidgets.QFrame.Box | QtWidgets.QFrame.Sunken)

        # Frame right
        self.fr_layout = QtWidgets.QVBoxLayout()
        self.fr_layout.setContentsMargins(0, 0, 0, 0)
        self.fr_layout.addWidget(self.restart_button)

        self.frame_right = QtWidgets.QFrame()
        self.frame_right.setLayout(self.fr_layout)
        self.frame_right.setFrameStyle(QtWidgets.QFrame.Box | QtWidgets.QFrame.Sunken)

        # Place frames in splitters
        self.splitter_h = QtWidgets.QSplitter(QtCore.Qt.Vertical)

        self.settings.add_setting(
            "application_splitter_h_state",
            default=self.splitter_h.saveState(),
            setter=self._set_splitter_h_state,
            getter=self._get_splitter_h_state)

        self.splitter_v = QtWidgets.QSplitter(QtCore.Qt.Horizontal)

        self.settings.add_setting(
            "application_splitter_v_state",
            default=self.splitter_v.saveState(),
            setter=self._set_splitter_v_state,
            getter=self._get_splitter_v_state)

        self.splitter_h.addWidget(self.frame_top_left)
        self.splitter_h.addWidget(self.frame_middle_left)
        self.splitter_h.addWidget(self.frame_bottom_left)
        self.fl_layout.addWidget(self.splitter_h)

        self.splitter_v.addWidget(self.frame_left)
        self.splitter_v.addWidget(self.frame_right)

        # Central widget
        self.central_layout = QtWidgets.QHBoxLayout()
        self.central_layout.setContentsMargins(5, 5, 5, 5)
        self.central_layout.addWidget(self.splitter_v)
        self.central_widget = QtWidgets.QWidget()
        self.central_widget.setLayout(self.central_layout)
        self.setCentralWidget(self.central_widget)

    ############
    # Settings #
    ############
    def _set_geometry(self, value):
        # settings are written to disk as text, geometry is a byte array
        geometry_bytes = base64.b64decode(value)
        self.restoreGeometry(geometry_bytes)

    def _get_geometry(self):
        # settings are written to disk as text, geometry is a byte array
        geometry_ascii = base64.b64encode(bytes(self.saveGeometry())).decode('ascii')
        json_encoded = json.dumps(geometry_ascii)
        return json_encoded

    def _set_state(self, value):
        # settings are written to disk as text, state is a byte array
        state_bytes = base64.b64decode(value)
        self.restoreState(state_bytes)

    def _get_state(self):
        # settings are written to disk as text, state is a byte array
        state_ascii = base64.b64encode(bytes(self.saveState())).decode('ascii')
        json_encoded = json.dumps(state_ascii)
        return json_encoded

    def _set_size(self, value):
        if value:
            self.resize(*value)

    def _get_size(self):
        # Must return a serializable value
        return self.size().toTuple()

    def _set_pos(self, value):
        if value:
            self.move(*value)

    def _get_pos(self):
        # Must return a serializable value
        return self.pos().toTuple()

    def _set_maximized(self, value):
        if value:
            self.showMaximized()

    def _get_maximized(self):
        return self.isMaximized()

    def _set_splitter_h_state(self, value):
        state_bytes = base64.b64decode(value)
        self.splitter_h.restoreState(state_bytes)

    def _get_splitter_h_state(self):
        # settings are written to disk as text, state is a byte array
        state_ascii = base64.b64encode(bytes(self.splitter_h.saveState())).decode('ascii')
        json_encoded = json.dumps(state_ascii)
        return json_encoded

    def _set_splitter_v_state(self, value):
        # settings are written to disk as text, state is a byte array
        state_bytes = base64.b64decode(value)
        self.splitter_v.restoreState(state_bytes)

    def _get_splitter_v_state(self):
        # settings are written to disk as text, state must be a byte array
        state_ascii = base64.b64encode(bytes(self.splitter_v.saveState())).decode('ascii')
        json_encoded = json.dumps(state_ascii)
        return json_encoded

    ###################
    # General methods #
    ###################
    def set_window_title(self, string=''):
        self.setWindowTitle(f'{APPLICATION_NAME} - ' + str(string))

    def on_file_menu_about_to_show(self):
        if self.lesson_file:
            self.save_action.setEnabled(True)

    def on_open(self):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            caption='Open Lesson File',
            dir=self.settings.lesson_directory,
            filter='Text Files (*.txt);;All (*.*)')

        try:
            with open(filename, 'r') as f:
                trimmed_content = f.read()

            self.text_editor.setPlainText(trimmed_content)
            self.lesson_file = filename
            self.settings.lesson_directory = os.path.dirname(filename)
            self.set_window_title(self.lesson_file)
        except (FileNotFoundError):
            pass

    def _save_file(self, filename):
        text = self.text_editor.toPlainText()
        try:
            with open(filename, 'w') as f:
                f.write(text)

            log.info(f"Saved: {filename}")
            self.set_window_title(filename)
            self.text_editor.document().setModified(False)
        except Exception as err:
            self.message_box = QtWidgets.QMessageBox()
            self.message_box.setText('Error: ' + str(err))
            self.message_box.show()

    def on_save(self):
        self._save_file(self.lesson_file)

    def on_save_as(self):
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            caption="Save As..",
            dir=self.settings.lesson_directory,
            filter="Text files (*.txt);;All files (*.*)")

        if filename:
            self._save_file(filename)
            self.lesson_file = filename

    def on_load_dictionary(self):
        filenames, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self,
            caption='Open one or more Plover dictionary files',
            dir=self.settings.dictionary_directory,
            filter='JSON Files (*.json);;All (*.*)')

        self._dictionary = TranslationDict.load(filenames)
        log.debug(f"Loaded dictionaries: {filenames}")

    def on_settings_action(self):
        non_application_keys = [k for k in self.settings._settings.keys() if k[:12] != 'application_']
        self.settings.set(non_application_keys)
        self.settings_window.toggle_modified(False)

        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()

    def on_about_action(self):
        self.about_window.show()
        self.about_window.raise_()
        self.about_window.activateWindow()

    def _reset(self):
        self.text_viewer.clear()
        self.line_edit.clear()
        self.missed = 0
        self.last_time = 0
        self.is_new_unit = True

        if self.text_split:
            self.live_split   = list(self.text_split)
            self.current_unit = self.text_split[0]

            cursor = self.text_viewer.textCursor()
            cursor.setPosition(0)
            text_format = cursor.charFormat()
            text_format.setForeground(QtGui.QBrush(BLACK))
            text_format.setFontUnderline(True)
            cursor.insertText(self.current_unit, text_format)
            text_format.setFontUnderline(False)
            cursor.insertText(' '+' '.join(self.text_split[1:]), text_format)
            cursor.setPosition(0)
            self.text_viewer.setTextCursor(cursor)

            self.line_edit.setEnabled(True)

            self.run_state = RunState.READY

    def on_text_edit_changed(self):

        title = ''
        if self.lesson_file:
            title += self.lesson_file

        if self.text_editor.document().isModified():
            title += '*'

        self.set_window_title(title)

        self.save_as_action.setEnabled(True)

        self.text_raw   = self.text_editor.toPlainText()
        self.text_split = tuple(TranslationDict.split_into_strokable_units(self.text_raw))

        self._reset()

    def on_restart_button_pressed(self):
        self._reset()

    def on_line_edit_text_edited(self, content):

        if self.run_state == RunState.COMPLETE:
            return
        elif self.run_state != RunState.PRACTICING:
            self.run_state = RunState.PRACTICING

        self.is_new_unit = False

        delta = abs(time.time()-self.last_time)

        # Accuracy measured on a per unit basis.  Without stroke information,
        # it's impossible to know whether text is a misstroke or simply part
        # of a multi-stroke phrase???Plover may delete entire words as part of a
        # multi-stroke sequence (e.g. "LEBG/TOR"->"lecture"->"elector").
        # Assuming the average word length in English is 5 characters, time in
        # seconds between characters /dt/ expressed in words given per minute
        # /w/ is dt = 12/w.  So, 0.4s is 30wpm.  self.settings.time_between_strokes
        # represents the minimum acceptable speed.
        time_between_strokes = 12 / self.settings.wpm_threshold
        if not self.is_miss and self.maybe_miss and delta > time_between_strokes:
            # since self.maybe_miss only gets set once per unit, each
            # unit has a maximum of 1 possible miss
            self.missed += 1
            # print(f"[MISS]", flush=True)
            self.is_miss = True

        self.last_time = time.time()

        # in steno, there are different ways to write something like a
        # double quote.  One stroke puts a space first to manage
        # sentance spacing.  Another puts a space after.  A leading
        # space would mess with the trimmed_content comparison if we
        # didn't trim.
        trimmed_content = content.strip()
        # print(f"{trimmed_content}", flush=True)

        # position is "between" characters; index is "on" characters
        line_edit_cursor_position = self.line_edit.cursorPosition()
        line_edit_cursor_index = self.line_edit.cursorPosition() - 1

        cursor = QtGui.QTextCursor(self.text_viewer.document())
        text_format = cursor.charFormat()

        if trimmed_content:

            # match; advance or finish
            if trimmed_content == self.current_unit:
                self.live_split.pop(0)
                self.text_viewer.clear()

                self.maybe_miss  = False
                self.is_miss     = False
                self.is_new_unit = True

                # advance to next unit
                if self.live_split:
                    self.current_unit = self.live_split[0]

                    text_format.setFontUnderline(True)
                    text_format.setForeground(QtGui.QBrush(BLACK))
                    cursor.setCharFormat(text_format)
                    cursor.insertText(self.current_unit)
                    text_format.setFontUnderline(False)
                    cursor.setCharFormat(text_format)
                    cursor.insertText(' '+' '.join(self.live_split[1:]))

                    self.line_edit.clear()

                # finish
                else:
                    total_number_units = len(self.text_split)
                    correct = (total_number_units - self.missed)
                    accuracy = correct / total_number_units
                    cursor.insertText(f"CONGRATS! Accuracy: {accuracy*100:.0f}% Missed: {self.missed}")
                    self.line_edit.clear()
                    self.line_edit.setEnabled(False)
                    self.run_state = RunState.COMPLETE

            # contents don't match current unit
            else:
                if not self.is_miss and len(trimmed_content) > len(self.current_unit):
                    self.maybe_miss = True

                cursor.setPosition(1)

                for i, c in enumerate(self.current_unit):
                    color = BLACK

                    if i < len(trimmed_content):
                        if trimmed_content[i] == c:
                            color = GRAY
                        else:
                            # contents have non-matching char
                            if not self.is_miss:
                                self.maybe_miss = True

                    cursor.deletePreviousChar()
                    text_format.setForeground(QtGui.QBrush(color))
                    cursor.insertText(c, text_format)
                    cursor.setPosition(cursor.position()+1)

        # no content???user deleted all input.
        else:
            if not self.is_new_unit:
                # already started and then returned to position 0
                self.maybe_miss = True

            # recolor first char
            cursor.setPosition(1)
            cursor.deletePreviousChar()
            text_format.setForeground(QtGui.QBrush(BLACK))
            cursor.insertText(self.current_unit[0], text_format)

        # print(f"maybe: {self.maybe_miss}", flush=True)

    def _load_settings(self, sync=True):
        self.settings.read(sync=sync)
        log.info(f"Loaded settings: {self.settings.config_file}")

    def _save_settings(self, sync=True):
        self.settings.write(sync=sync)
        log.info(f"Saved settings: {self.settings.config_file}")

    def closeEvent(self, event):
        # must save before objects (like the SettingsWindow) are
        # destroyed
        self._save_settings(sync=True)

        # since MainWindow is not parent, must close manually
        self.about_window.close()
        del self.about_window

        self.settings_window.close()
        del self.settings_window

        event.accept()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--log-level",
                        help="set log level.  Default is 'info'.  Use 'debug' for more logging.",
                        choices=['info', 'debug'], type=str)
    args = parser.parse_args()

    if IS_DEV_DEBUG or args.log_level == 'debug':
        log.setLevel(logging.DEBUG)
        logging.getLogger("settings").setLevel(logging.DEBUG)
        log.warning(f'RUNNING IN DEBUG MODE')

    app = QtWidgets.QApplication(sys.argv)

    # do this here because QApplication must exist
    icon_pixmap = QtGui.QPixmap()
    icon_pixmap.loadFromData(APPLICATION_ICON_BYTES)
    app.setWindowIcon(QtGui.QIcon(icon_pixmap))

    main_window = MainWindow()
    main_window.show()

    sys.exit(app.exec_())

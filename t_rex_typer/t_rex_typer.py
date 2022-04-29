import os
import sys
import copy

import logging
log = logging.getLogger(__name__)
logging.basicConfig(format='%(levelname)s: [%(filename)s:%(lineno)d] %(message)s', level=logging.INFO)

import argparse
from enum import Enum
from translation_dict import TranslationDict
from PySide2 import QtCore, QtWidgets, QtGui


def my_excepthook(etype, value, tb):
    print(f"", flush=True)
    import traceback
    traceback.print_exception(etype, value, tb)
    print(f"Entering post-mortem debugger...\n", flush=True)
    import pdb; pdb.pm()

sys.excepthook = my_excepthook

BLACK = QtGui.QColor(0, 0, 0)
GRAY  = QtGui.QColor(190, 190, 190)

APPLICATION_NAME  = "T-Rex Typer"
APPLICATION_ICON  = "resources/trex_w_board_48.png"
DEFAULT_DIRECTORY = os.path.expanduser("~")
IS_DEV_DEBUG = True if os.getenv('DEV_DEBUG').lower() in ['1', 'true'] else False


class RunState(Enum):
    COMPLETE   = 0
    PRACTICING = 1
    READY      = 2


class TextLabel(QtWidgets.QTextEdit):

    def __init__(self, text='', parent=None):
        super().__init__()

        if parent:
            color = parent.palette().background().color()
        else:
            color = QtGui.QColor(239, 239, 239)  # the default light gray

        p =  self.viewport().palette()
        p.setColor(self.viewport().backgroundRole(), color)
        self.viewport().setPalette(p)

        self.document().setDocumentMargin(0)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.setReadOnly(True)

        # TODO this is set one time. If the font is changed, the font_metrics
        # object is not updated nor is the height.  This also prevents the
        # widget from resizing as might be expected_char when compared to a QLabel.
        font_metrics = QtGui.QFontMetrics(self.font())
        height = font_metrics.height() + (self.frameWidth()) * 2
        self.setFixedHeight(height)


class AboutWindow(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle(f'About {APPLICATION_NAME}')

        self.init_widgets()
        self.init_layout()

    def init_widgets(self):
        self.body_title = QtWidgets.QLabel(f'<h1><img src="{APPLICATION_ICON}">About</h1>')

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
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.body_title)
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

        self.current_file = None

        self.text_raw = ''
        self.text_split = ()
        self.live_split = []
        self.current_unit = ''

        self.init_widgets()
        self.init_layout()

        self.line_edit.setFocus()
        self.run_state = RunState.READY

    def get_run_state(self):
        return self._run_state

    def set_run_state(self, value):
        self._run_state = value
        log.debug(f"{self._run_state=}")

    run_state = property(get_run_state, set_run_state)

    def init_widgets(self):

        # menu
        self.open_file_action = QtWidgets.QAction('&Open', self)
        self.open_file_action.setShortcut('Ctrl+O')
        self.open_file_action.setStatusTip('Open...')
        self.open_file_action.triggered.connect(self.on_open_file)

        self.save_file_action = QtWidgets.QAction('&Save', self)
        self.save_file_action.setEnabled(False)
        self.save_file_action.setShortcut('Ctrl+S')
        self.save_file_action.setStatusTip('Save')
        self.save_file_action.triggered.connect(self.on_save_file)

        self.save_file_as_action = QtWidgets.QAction('Save &As...', self)
        self.save_file_as_action.setStatusTip('Save As')
        self.save_file_as_action.setEnabled(False)
        self.save_file_as_action.triggered.connect(self.on_save_file_as)

        self.exit_action = QtWidgets.QAction('&Exit', self)
        self.exit_action.setShortcut("Escape")
        self.exit_action.setStatusTip('Exit application')
        self.exit_action.triggered.connect(self.close)

        self.about_action = QtWidgets.QAction('&About', self)
        self.about_action.triggered.connect(self.on_about)

        self.menu_bar = self.menuBar()

        self.file_menu = self.menu_bar.addMenu('&File')
        self.file_menu.aboutToShow.connect(self.on_file_menu_about_to_show)
        self.file_menu.addAction(self.open_file_action)
        self.file_menu.addAction(self.save_file_action)
        self.file_menu.addAction(self.save_file_as_action)
        self.file_menu.addAction(self.exit_action)

        self.help_menu = self.menu_bar.addMenu('&Help')
        self.help_menu.addAction(self.about_action)

        # no parent so that a separate window is used
        self.about_window = AboutWindow()

        # Text viewer
        self.text_viewer = TextLabel(self)

        # Line edit
        self.line_edit = QtWidgets.QLineEdit()

        # setText doesn't trigger edited signal (only changed signal)
        self.line_edit.textEdited.connect(self.on_line_edit_text_edited)

        # Steno label
        # TODO
        self.steno_label = QtWidgets.QLabel('PHROFR')
        self.steno_label.hide()

        # Text edit
        self.text_editor = QtWidgets.QTextEdit()
        self.text_editor.setPlaceholderText('Put practice words here...')
        self.text_editor.textChanged.connect(self.on_text_edit_changed)

        text = ("It's the case that every effort has been made to 'replicate' this text as")
                # "faithfully as possible, including inconsistencies in spelling"
                # "and hyphenation.  Some corrections of spelling and punctuation"
                # "have been made. They are listed at the end of the text.")

        text = "this is a test"

        self.text_editor.setText(text)

        # start
        self.restart_button = QtWidgets.QPushButton("Restart")
        self.restart_button.pressed.connect(self.on_restart_button_pressed)

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
        self.splitter_v = QtWidgets.QSplitter(QtCore.Qt.Horizontal)

        self.splitter_h.addWidget(self.frame_top_left)
        self.splitter_h.addWidget(self.frame_middle_left)
        self.splitter_h.addWidget(self.frame_bottom_left)
        self.fl_layout.addWidget(self.splitter_h)

        self.splitter_v.addWidget(self.frame_left)
        self.splitter_v.addWidget(self.frame_right)
        self.splitter_v.setStretchFactor(1, 1)

        # Central widget
        self.central_layout = QtWidgets.QHBoxLayout()
        self.central_layout.setContentsMargins(5, 5, 5, 5)
        self.central_layout.addWidget(self.splitter_v, stretch=1)

        self.central_widget = QtWidgets.QWidget()
        self.central_widget.setLayout(self.central_layout)
        self.setCentralWidget(self.central_widget)

    def set_window_title(self, string=''):
        self.setWindowTitle(f'{APPLICATION_NAME} - ' + str(string))

    def on_file_menu_about_to_show(self):
        if self.current_file:
            self.save_file_action.setEnabled(True)

    def on_open_file(self):
        # TODO need a "most recent directory" for open and save as.

        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            caption='Open File',
            dir=DEFAULT_DIRECTORY,
            filter='Text Files (*.txt);;All (*.*)')

        try:
            with open(filename, 'r') as f:
                content = f.read()

            self.text_editor.setPlainText(content)
            self.current_file = filename
            self.set_window_title(self.current_file)
        except (FileNotFoundError):
            pass

    def _on_save_file(self, filename):
        text = self.text_editor.toPlainText()
        try:
            with open(filename, 'w') as f:
                f.write(text)

            self.set_window_title(filename)
        except Exception as err:
            self.message_box = QtWidgets.QMessageBox()
            self.message_box.setText('Error: ' + str(err))
            self.message_box.show()

    def on_save_file(self):
        self._on_save_file(self.current_file)

    def on_save_file_as(self):
        # TODO global or text edit local save shortcut
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            caption="Save As...",
            dir=DEFAULT_DIRECTORY,
            filter="Text files (*.txt);;All files (*.*)")

        if filename:
            self._on_save_file(filename)
            self.current_file = filename

    def on_about(self):
        self.about_window.show()

    def _reset(self):
        self.live_split   = list(self.text_split)
        self.current_unit = self.text_split[0]

        self.text_viewer.clear()
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
        title = '*'
        if self.current_file:
            title = self.current_file + '*'

        self.set_window_title(title)

        self.save_file_as_action.setEnabled(True)

        self.text_raw     = self.text_editor.toPlainText()
        self.text_split   = tuple(TranslationDict.split_into_strokable_units(self.text_raw))

        self._reset()

    def on_restart_button_pressed(self):
        self._reset()

    def on_line_edit_text_edited(self, content):

        if self.run_state == RunState.COMPLETE:
            return
        elif self.run_state != RunState.PRACTICING:
            self.run_state = RunState.PRACTICING

        # in steno, there are different ways to write something like a double
        # quote.  One stroke puts a space first to manage sentance spacing.
        # Another puts a space after.  A leading space would mess with the
        # content comparison if we didn't trim.  The user would begin using the
        # wrong stroke for the situation which is the opposite purpose of this
        # tool.
        trimmed_content = content.strip()

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

                # words are left in the split
                # setup next unit
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

                # no words left; done
                else:
                    cursor.insertText("CONGRATS!")
                    self.line_edit.clear()
                    self.line_edit.setEnabled(False)
                    self.run_state = RunState.COMPLETE

            # contents don't match
            # color the first unit
            else:
                cursor.setPosition(1)

                for i, c in enumerate(self.current_unit):
                    color = BLACK

                    if i < len(content) and content[i] == c:
                        color = GRAY

                    cursor.deletePreviousChar()
                    text_format.setForeground(QtGui.QBrush(color))
                    cursor.insertText(c, text_format)
                    cursor.setPosition(cursor.position()+1)

        # no content–user deleted all input.  The line edit content changed, but
        # the content is an empty string.  However, the viewer shows gray since
        # they had previously entered something.  This case handles recoloring
        # the first char.
        else:
            cursor.setPosition(1)
            cursor.deletePreviousChar()
            text_format.setForeground(QtGui.QBrush(BLACK))
            cursor.insertText(self.current_unit[0], text_format)

    def closeEvent(self, event):
        # since MainWindow is not parent, must close manually
        self.about_window.close()
        del self.about_window

        event.accept()


if __name__ == '__main__':

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
    app.setWindowIcon(QtGui.QIcon(APPLICATION_ICON))

    main_window = MainWindow()
    main_window.show()

    sys.exit(app.exec_())

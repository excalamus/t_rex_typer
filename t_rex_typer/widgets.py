from PySide2 import QtCore, QtWidgets, QtGui


class ElidingLabel(QtWidgets.QLabel):
    """Label with text elision.

    QLabel which will elide text too long to fit the widget.  Based on:
    https://doc.qt.io/qt-5/qtwidgets-widgets-elidedlabel-example.html

    Parameters
    ----------
    text : str

        Label text.

    mode : QtCore.Qt.TextElideMode

       Specify where ellipsis should appear when displaying texts that
       don’t fit.

       Default is QtCore.Qt.ElideMiddle.

       Possible modes:
         QtCore.Qt.ElideLeft
         QtCore.Qt.ElideMiddle
         QtCore.Qt.ElideRight

    parent : QWidget

       Parent widget.  Default is None.

    f : Qt.WindowFlags()

       https://doc-snapshots.qt.io/qtforpython-5.15/PySide2/QtCore/Qt.html#PySide2.QtCore.PySide2.QtCore.Qt.WindowType

    """

    elision_changed = QtCore.Signal(bool)

    def __init__(self, text='', mode=QtCore.Qt.ElideMiddle, **kwargs):
        super().__init__(**kwargs)

        self._mode = mode
        self.is_elided = False

        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.setText(text)

    def setText(self, text):
        self._contents = text
        self.update()

    def text(self):
        return self._contents

    def minimumSizeHint(self):
        # make sure label doesn't clip vertically
        metrics = QtGui.QFontMetrics(self.font())
        return QtCore.QSize(0, metrics.height())

    def paintEvent(self, event):
        super().paintEvent(event)

        did_elide = False

        painter = QtGui.QPainter(self)
        font_metrics = painter.fontMetrics()
        text_width = font_metrics.horizontalAdvance(self.text())

        # layout phase
        text_layout = QtGui.QTextLayout(self._contents, painter.font())
        text_layout.beginLayout()

        while True:

            line = text_layout.createLine()

            if not line.isValid():
                break

            line.setLineWidth(self.width())

            if text_width >= self.width():
                elided_line = font_metrics.elidedText(self._contents, self._mode, self.width())
                painter.drawText(QtCore.QPoint(0, font_metrics.ascent()), elided_line)
                did_elide = line.isValid()
                break
            else:
                line.draw(painter, QtCore.QPoint(0, 0))

        text_layout.endLayout()

        self.elision_changed.emit(did_elide)

        if did_elide != self.is_elided:
            self.is_elided = did_elide
            self.elision_changed.emit(did_elide)

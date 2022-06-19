import sys
from PySide2 import QtCore, QtWidgets, QtGui


# dimensions given in pixels
KEY_WIDTH   = 11
KEY_HEIGHT  = 11
KEY_BOARDER = 1  # 2
KEY_SPACING = 1  # 0
FONT_SIZE   = 8


class KeyPath(QtGui.QPainterPath):

    def __init__(self, start_point=QtCore.QPointF(0.0, 0.0), size=QtCore.QSize(KEY_WIDTH, KEY_HEIGHT)):
        super().__init__(start_point)

        self.start_point = start_point
        self.size = size
        self.rect = QtCore.QRectF(self.start_point, self.size)

        self.moveTo(start_point)
        self.addRoundedRect(self.rect, 2.0, 2.0)


class Key(QtWidgets.QWidget):

    def __init__(self, letter):
        super().__init__()

        self.letter = letter
        self.size_ = QtCore.QSize(KEY_WIDTH, KEY_HEIGHT)

        self.color = QtCore.Qt.lightGray

    def minimumSizeHint(self):
        return self.size_ + QtCore.QSize(KEY_BOARDER, KEY_BOARDER)

    def sizeHint(self):
        return self.size_ + QtCore.QSize(KEY_BOARDER, KEY_BOARDER)

    def set_color(self, color):
        self.color = color
        self.update()

    # TODO implement proper color management using QPalette
    # def mousePressEvent(self, event):
    #     self.setBackgroundRole(QtGui.QPalette.Base)
    #     if self.color == QtCore.Qt.gray:
    #         self.set_color(QtGui.QColor(122, 163, 39))
    #     else:
    #         self.set_color(QtCore.Qt.gray)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.HighQualityAntialiasing)

        pen = QtGui.QPen()
        pen.setColor(QtCore.Qt.black)
        pen.setWidth(KEY_BOARDER)
        pen.setStyle(QtCore.Qt.SolidLine)
        pen.setCapStyle(QtCore.Qt.RoundCap)
        pen.setJoinStyle(QtCore.Qt.RoundJoin)

        painter.setPen(pen)

        brush = QtGui.QBrush()
        brush.setStyle(QtCore.Qt.SolidPattern)
        brush.setColor(self.color)

        painter.setBrush(brush)

        path = KeyPath(QtCore.QPointF(0.0, 0.0), self.size_)
        painter.drawPath(path)

        font = painter.font()
        font.setPixelSize(FONT_SIZE)
        font.setWeight(QtGui.QFont.Medium)
        painter.setFont(font)

        rect = path.boundingRect()
        painter.drawText(rect, QtCore.Qt.AlignCenter, self.letter)


class TallKey(Key):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.size_ = QtCore.QSize(10, 22)
        w = KEY_WIDTH
        h = 2*KEY_HEIGHT + KEY_BOARDER + KEY_SPACING
        self.size_ = QtCore.QSize(w, h)


class WideKey(Key):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.size_ = QtCore.QSize(120, 10)
        w = 10*KEY_WIDTH + 9*KEY_SPACING + 10*KEY_BOARDER
        h = KEY_HEIGHT
        self.size_ = QtCore.QSize(w, h)


class StenoBoard(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()

        QtWidgets.QShortcut(QtGui.QKeySequence("Escape"), self, self.close)
        self.resize(500, 500)

        self.number_bar = WideKey("#    ")  # align symbol with *-key

        self.s_left  = TallKey("S")
        self.t_left  = Key("T")
        self.p_left  = Key("P")
        self.h       = Key("H")

        self.k       = Key("K")
        self.w       = Key("W")
        self.r_left  = Key("R")

        self.a = Key("A")
        self.o = Key("O")

        self.star    = TallKey("*")

        self.e = Key("E")
        self.u = Key("U")

        self.f       = Key("F")
        self.p_right = Key("P")
        self.l       = Key("L")
        self.t_right = Key("T")
        self.d       = Key("D")

        self.r_right = Key("R")
        self.b       = Key("B")
        self.g       = Key("G")
        self.s_right = Key("S")
        self.z       = Key("Z")

        # left
        self.left_top_layout = QtWidgets.QHBoxLayout()
        self.left_top_layout.setContentsMargins(0, 0, 0, 0)
        self.left_top_layout.setSpacing(KEY_SPACING)
        self.left_top_layout.addWidget(self.t_left)
        self.left_top_layout.addWidget(self.p_left)
        self.left_top_layout.addWidget(self.h)

        self.left_bottom_layout = QtWidgets.QHBoxLayout()
        self.left_bottom_layout.setContentsMargins(0, 0, 0, 0)
        self.left_bottom_layout.setSpacing(KEY_SPACING)
        self.left_bottom_layout.addWidget(self.k)
        self.left_bottom_layout.addWidget(self.w)
        self.left_bottom_layout.addWidget(self.r_left)

        self.left_stack_layout = QtWidgets.QVBoxLayout()
        self.left_stack_layout.setContentsMargins(0, 0, 0, 0)
        self.left_stack_layout.setSpacing(KEY_SPACING)
        self.left_stack_layout.addLayout(self.left_top_layout)
        self.left_stack_layout.addLayout(self.left_bottom_layout)
        self.left_stack_layout.addWidget(QtWidgets.QWidget(), stretch=1)

        self.left_outer_layout = QtWidgets.QHBoxLayout()
        self.left_outer_layout.setContentsMargins(0, 0, 0, 0)
        self.left_outer_layout.setSpacing(KEY_SPACING)
        self.left_outer_layout.addWidget(self.s_left)
        self.left_outer_layout.addLayout(self.left_stack_layout)
        self.left_outer_layout.addWidget(QtWidgets.QWidget(), stretch=1)

        # right
        self.right_top_layout = QtWidgets.QHBoxLayout()
        self.right_top_layout.setContentsMargins(0, 0, 0, 0)
        self.right_top_layout.setSpacing(KEY_SPACING)
        self.right_top_layout.addWidget(self.f)
        self.right_top_layout.addWidget(self.p_right)
        self.right_top_layout.addWidget(self.l)
        self.right_top_layout.addWidget(self.t_right)
        self.right_top_layout.addWidget(self.d)

        self.right_bottom_layout = QtWidgets.QHBoxLayout()
        self.right_bottom_layout.setContentsMargins(0, 0, 0, 0)
        self.right_bottom_layout.setSpacing(KEY_SPACING)
        self.right_bottom_layout.addWidget(self.r_right)
        self.right_bottom_layout.addWidget(self.b)
        self.right_bottom_layout.addWidget(self.g)
        self.right_bottom_layout.addWidget(self.s_right)
        self.right_bottom_layout.addWidget(self.z)

        self.right_layout = QtWidgets.QVBoxLayout()
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.right_layout.setSpacing(KEY_SPACING)
        self.right_layout.addLayout(self.right_top_layout)
        self.right_layout.addLayout(self.right_bottom_layout)
        self.right_layout.addWidget(QtWidgets.QWidget(), stretch=1)

        # home
        self.home_layout = QtWidgets.QHBoxLayout()
        self.home_layout.setContentsMargins(0, 0, 0, 0)
        self.home_layout.setSpacing(KEY_SPACING)
        self.home_layout.addLayout(self.left_outer_layout)
        self.home_layout.addWidget(self.star)
        self.home_layout.addLayout(self.right_layout)
        self.home_layout.addWidget(QtWidgets.QWidget(), stretch=1)

        # thumb
        self.thumb_layout = QtWidgets.QHBoxLayout()
        self.thumb_layout.setContentsMargins(0, 0, 0, 0)
        self.thumb_layout.setSpacing(KEY_SPACING)
        left_offset = 2*KEY_WIDTH + 2*KEY_BOARDER + 2*KEY_SPACING
        self.thumb_layout.addSpacerItem(QtWidgets.QSpacerItem(left_offset, 0))
        self.thumb_layout.addWidget(self.a)
        self.thumb_layout.addWidget(self.o)
        middle_offset = KEY_WIDTH + KEY_BOARDER + 2*KEY_SPACING
        self.thumb_layout.addSpacerItem(QtWidgets.QSpacerItem(middle_offset, 0))
        self.thumb_layout.addWidget(self.e)
        self.thumb_layout.addWidget(self.u)
        self.thumb_layout.addWidget(QtWidgets.QWidget(), stretch=1)

        # board
        self.board_layout = QtWidgets.QVBoxLayout()
        self.board_layout.setContentsMargins(0, 0, 0, 0)
        self.board_layout.setSpacing(KEY_SPACING)
        self.board_layout.addWidget(self.number_bar)
        self.board_layout.addLayout(self.home_layout)
        self.board_layout.addLayout(self.thumb_layout)
        self.board_layout.addWidget(QtWidgets.QWidget(), stretch=1)

        self.setLayout(self.board_layout)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    steno_board = StenoBoard()
    steno_board.show()

    sys.exit(app.exec_())

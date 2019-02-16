from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets


class EscapableQListWidget(QtWidgets.QListWidget):

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.clearSelection()

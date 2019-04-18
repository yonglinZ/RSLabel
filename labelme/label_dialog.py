from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

import labelme.utils
# TODO(unknown):
# - Calculate optimal position so as not to go out of screen area.


class LabelQLineEdit(QtWidgets.QLineEdit):
    def setListWidget(self, list_widget):
        self.list_widget = list_widget

    def keyPressEvent(self, e):
        if e.key() in [QtCore.Qt.Key_Up, QtCore.Qt.Key_Down]:
            self.list_widget.keyPressEvent(e)
        else:
            super(LabelQLineEdit, self).keyPressEvent(e)


class LabelDialog(QtWidgets.QDialog):
    def __init__(self,
                 text="Enter object label",
                 parent=None,
                 labels=None,
                 sort_labels=True,
                 show_text_field=True,
                 completion='startswith',
                 fit_to_content=None):
        if fit_to_content is None:
            fit_to_content = {'row': False, 'column': True}
        self._fit_to_content = fit_to_content

        super(LabelDialog, self).__init__(parent)
        self.edit = LabelQLineEdit()
        self.edit.setPlaceholderText(text)
        self.edit.setValidator(labelme.utils.labelValidator())
        self.edit.editingFinished.connect(self.postProcess)
        layout = QtWidgets.QVBoxLayout()
        if show_text_field:
            layout.addWidget(self.edit)
        # buttons
        self.buttonBox = bb = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal,
            self,
        )
        bb.button(bb.Ok).setIcon(labelme.utils.newIcon('done'))
        bb.button(bb.Cancel).setIcon(labelme.utils.newIcon('undo'))
        bb.accepted.connect(self.validate)
        bb.rejected.connect(self.reject)
        hlayout = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel('置信度')
        self.probability = QtWidgets.QSpinBox()
        self.probability.setMaximum(10)
        self.probability.setMinimum(0)
        self.probability.setValue(10)
        hlayout.addWidget(label)
        hlayout.addWidget(self.probability)
        hlayout.addWidget(bb)
        layout.addLayout(hlayout)
        # label_list
        self.labelList = QtWidgets.QListWidget()
        if self._fit_to_content['row']:
            self.labelList.setHorizontalScrollBarPolicy(
                QtCore.Qt.ScrollBarAlwaysOff)
        if self._fit_to_content['column']:
            self.labelList.setVerticalScrollBarPolicy(
                QtCore.Qt.ScrollBarAlwaysOff)
        self._sort_labels = sort_labels
        if labels:
            self.labelList.addItems(labels)
        if self._sort_labels:
            self.labelList.sortItems()
        else:
            self.labelList.setDragDropMode(
                QtWidgets.QAbstractItemView.InternalMove)
        self.labelList.currentItemChanged.connect(self.labelSelected)
        self.labelList.itemDoubleClicked.connect(self.doubleClicked)
        self.edit.setListWidget(self.labelList)
        layout.addWidget(self.labelList)
        self.setLayout(layout)
        # completion
        completer = QtWidgets.QCompleter()
        if completion == 'startswith':
            completer.setCompletionMode(QtWidgets.QCompleter.InlineCompletion)
            # Default settings.
            # completer.setFilterMode(QtCore.Qt.MatchStartsWith)
        elif completion == 'contains':
            completer.setCompletionMode(QtWidgets.QCompleter.PopupCompletion)
            completer.setFilterMode(QtCore.Qt.MatchContains)
        else:
            raise ValueError('Unsupported completion: {}'.format(completion))
        completer.setModel(self.labelList.model())
        self.edit.setCompleter(completer)

    def addLabelHistory(self, label):
        if self.labelList.findItems(label, QtCore.Qt.MatchExactly):
            return
        self.labelList.addItem(label)
        if self._sort_labels:
            self.labelList.sortItems()

    def labelSelected(self, item):
        self.edit.setText(item.text())

    def validate(self):
        text = self.edit.text()
        if hasattr(text, 'strip'):
            text = text.strip()
        else:
            text = text.trimmed()
        if text:
            self.accept()

    def postProcess(self):
        text = self.edit.text()
        if hasattr(text, 'strip'):
            text = text.strip()
        else:
            text = text.trimmed()
        self.edit.setText(text)

    def popUp(self, text=None, probability=None, move=True):
        if self._fit_to_content['row']:
            self.labelList.setMinimumHeight(
                self.labelList.sizeHintForRow(0) * self.labelList.count() + 2)
        if self._fit_to_content['column']:
            self.labelList.setMinimumWidth(
                self.labelList.sizeHintForColumn(0) + 2)
        # if text is None, the previous label in self.edit is kept
        if text is None:
            text = self.edit.text()
        self.edit.setText(text)
        self.edit.setSelection(0, len(text))
        items = self.labelList.findItems(text, QtCore.Qt.MatchFixedString)
        if items:
            assert len(items) == 1
            self.labelList.setCurrentItem(items[0])
            row = self.labelList.row(items[0])
            self.edit.completer().setCurrentRow(row)
        self.edit.setFocus(QtCore.Qt.PopupFocusReason)
        if move:
            self.move(QtGui.QCursor.pos())
        if probability is not None:
            self.probability.setValue(probability)
        return (self.edit.text(), self.probability.value()) if self.exec_() else None

    def doubleClicked(self):
        print('*selected item is', self.labelList.currentItem().text())
        text = self.edit.text()
        if hasattr(text, 'strip'):
            text = text.strip()
        else:
            text = text.trimmed()
        if text:
            self.accept()


if __name__ == '__main__':
    import sys
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
    from PyQt5.QtWidgets import *
    app = QApplication(sys.argv)
    w = LabelDialog()
    w.show()
    sys.exit(app.exec())

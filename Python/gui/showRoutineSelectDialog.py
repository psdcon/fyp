import json

from PyQt5.QtCore import QRegExp, QSortFilterProxyModel, Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QMenu

from gui.routineSelectDialogUi import *
from helpers import consts


# Work around the fact that QSortFilterProxyModel always filters datetime
# values in QtCore.Qt.ISODate format, but the tree views display using
# QtCore.Qt.DefaultLocaleShortDate format.
class MySortFilterProxyModel(QSortFilterProxyModel):
    # Custom sort function so that the int column gets sorted as numeric rather than alphabetic. i.e. 1, 10 11, etc
    def lessThan(self, left_index, right_index):
        left_var = left_index.data(Qt.DisplayRole)
        right_var = right_index.data(Qt.DisplayRole)
        # Cast to an int if possible. If it fails, defaults to normal sorting.
        try:
            return int(left_var) < int(right_var)
        except (ValueError, TypeError):
            pass

        return left_var < right_var


class RoutineSelectDialog(QDialog, Ui_routineSelectDialog):
    def __init__(self):
        super(RoutineSelectDialog, self).__init__()

        # Data variables
        self.untrackedIndexes = []
        self.routinesSelected = []


        # GUI Stuff
        self.setupUi(self)

        # Create sort filter model from custom model
        self.proxyModel = MySortFilterProxyModel()
        self.proxyModel.setDynamicSortFilter(True)

        # TableView stuff
        self.proxyView.setModel(self.proxyModel)

        # Competition filter combo box options
        self.filterCompetitionComboBox.addItem("")
        for comp in consts.comps:
            self.filterCompetitionComboBox.addItem(comp)

        # Event handlers
        self.proxyView.selectionModel().selectionChanged.connect(self.checkSelectedRoutines)
        self.selectUntrackedButton.clicked.connect(self.checkUntrackedRoutines)
        self.lastSelectionButton.clicked.connect(self.selectLastSelection)

        # Set default sort order to be by id
        self.proxyView.sortByColumn(0, Qt.AscendingOrder)

    # "Click" Handler
    # Checks checkbox on selection. Kind of a hacky UX
    def checkSelectedRoutines(self):
        for i in self.proxyView.selectedIndexes():
            item = self.model.item(i.row(), 0)
            item.setCheckState(Qt.Checked)

    # Button Handlers
    def checkUntrackedRoutines(self):
        for i in self.untrackedIndexes:
            item = self.model.item(i, 0)
            item.setCheckState(Qt.Checked)

    # Load selection from file.
    def selectLastSelection(self):
        try:
            with open(consts.lastSelectionFilePath, 'r') as lastSelectionFile:
                self.routinesSelected = json.load(lastSelectionFile)
                for i in self.routinesSelected:
                    item = self.model.item(i, 0)
                    item.setCheckState(Qt.Checked)
        except IOError:
            self.routinesSelected = []

    # Context menu event handler
    def unCheckSelected(self):
        for i in self.proxyView.selectedIndexes():
            item = self.model.item(i.row(), 0)
            item.setCheckState(Qt.Unchecked)

    # Create context menu
    def contextMenuEvent(self, event):
        menu = QMenu(self)
        uncheckAction = menu.addAction("Uncheck Selected")

        action = menu.exec_(self.mapToGlobal(event.pos()))
        if action == uncheckAction:
            self.unCheckSelected()

    # Function to update UI
    def updateSelectedCountLabel(self, count):
        total = self.model.rowCount()
        self.selectedCountLabel.setText("{} of {} selected".format(count, total))

    # Called when item in row changes.
    # Updates the selected count label & Saves selections ids to list.
    def handleItemChanged(self):
        count = 0
        self.routinesSelected = []
        for i in range(self.model.rowCount()):
            if self.model.item(i).checkState():
                self.routinesSelected.append(i)
                count += 1

        self.updateSelectedCountLabel(count)

    def setSourceModel(self, model):
        self.model = model
        self.proxyModel.setSourceModel(self.model)
        self.model.itemChanged.connect(self.handleItemChanged)

        for i in range(self.model.columnCount()):
            self.proxyView.resizeColumnToContents(i)

        # Update label text after model has been set
        self.updateSelectedCountLabel(0)

    # Unused sorting functions
    def filterRegExpChanged(self):
        syntax_nr = self.filterSyntaxComboBox.itemData(self.filterSyntaxComboBox.currentIndex())
        syntax = QRegExp.PatternSyntax(syntax_nr)

        if self.filterCaseSensitivityCheckBox.isChecked():
            caseSensitivity = Qt.CaseSensitive
        else:
            caseSensitivity = Qt.CaseInsensitive

        regExp = QRegExp(self.filterPatternLineEdit.text(), caseSensitivity, syntax)
        self.proxyModel.setFilterRegExp(regExp)

    def filterColumnChanged(self):
        self.proxyModel.setFilterKeyColumn(self.filterColumnComboBox.currentIndex())

    def sortChanged(self):
        if self.sortCaseSensitivityCheckBox.isChecked():
            caseSensitivity = Qt.CaseSensitive
        else:
            caseSensitivity = Qt.CaseInsensitive

        self.proxyModel.setSortCaseSensitivity(caseSensitivity)


def addRoutineRow(model, routine):
    items = [QStandardItem(val) for val in routine.values()]
    items[0].setCheckable(True)  # make first col checkable

    model.appendRow(items)


def createRoutinesModel(parent, routines):
    numColumns = len(routines[0])
    columnNames = [str.capitalize() for str in routines[0].keys()]

    model = QStandardItemModel(0, numColumns, parent)
    model.setHorizontalHeaderLabels(columnNames)

    for i, routine in enumerate(routines):
        addRoutineRow(model, routine)
        # TODO Describe
        if routine['tracked'] is "No":
            parent.untrackedIndexes.append(i)

    return model


def show_selection_menu(routines):
    # To show pyqt exceptions in PyCharm
    import sys
    # http://stackoverflow.com/questions/34363552/python-process-finished-with-exit-code-1-when-using-pycharm-and-pyqt5
    sys._excepthook = sys.excepthook
    def my_exception_hook(exctype, value, traceback):
        # Print the error and traceback
        print(exctype, value, traceback)
        # Call the normal Exception hook after
        sys._excepthook(exctype, value, traceback)
        sys.exit(1)

    # Set the exception hook to our wrapper function
    sys.excepthook = my_exception_hook

    # Create the dialog box
    app = QApplication([])
    dialog = RoutineSelectDialog()
    dialog.setSourceModel(createRoutinesModel(dialog, routines))
    okay = dialog.exec_()
    if okay:
        # Save the last selection to a file
        with open(consts.lastSelectionFilePath, 'w') as lastSelectionFile:
            json.dump(dialog.routinesSelected, lastSelectionFile)
        # Return the selected ids
        return dialog.routinesSelected
    else:  # "Cancel" btn was pressed
        return []


if __name__ == '__main__':
    print 'Does not run standalone...'

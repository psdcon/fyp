# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'demo.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_routineSelectDialog(object):
    def setupUi(self, routineSelectDialog):
        routineSelectDialog.setObjectName("routineSelectDialog")
        routineSelectDialog.resize(800, 600)
        self.gridLayout = QtWidgets.QGridLayout(routineSelectDialog)
        self.gridLayout.setObjectName("gridLayout")
        self.proxyView = QtWidgets.QTreeView(routineSelectDialog)
        self.proxyView.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.proxyView.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.proxyView.setProperty("showDropIndicator", False)
        self.proxyView.setAlternatingRowColors(True)
        self.proxyView.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.proxyView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.proxyView.setRootIsDecorated(False)
        self.proxyView.setItemsExpandable(False)
        self.proxyView.setSortingEnabled(True)
        self.proxyView.setExpandsOnDoubleClick(False)
        self.proxyView.setObjectName("proxyView")
        self.gridLayout.addWidget(self.proxyView, 0, 0, 1, 1)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.selectUntrackedButton = QtWidgets.QPushButton(routineSelectDialog)
        self.selectUntrackedButton.setObjectName("selectUntrackedButton")
        self.horizontalLayout.addWidget(self.selectUntrackedButton)
        self.lastSelectionButton = QtWidgets.QPushButton(routineSelectDialog)
        self.lastSelectionButton.setObjectName("lastSelectionButton")
        self.horizontalLayout.addWidget(self.lastSelectionButton)
        self.filterCompetitionLabel = QtWidgets.QLabel(routineSelectDialog)
        self.filterCompetitionLabel.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.filterCompetitionLabel.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.filterCompetitionLabel.setObjectName("filterCompetitionLabel")
        self.horizontalLayout.addWidget(self.filterCompetitionLabel)
        self.filterCompetitionComboBox = QtWidgets.QComboBox(routineSelectDialog)
        self.filterCompetitionComboBox.setObjectName("filterCompetitionComboBox")
        self.horizontalLayout.addWidget(self.filterCompetitionComboBox)
        self.gridLayout.addLayout(self.horizontalLayout, 1, 0, 1, 1)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.selectedCountLabel = QtWidgets.QLabel(routineSelectDialog)
        self.selectedCountLabel.setObjectName("selectedCountLabel")
        self.horizontalLayout_2.addWidget(self.selectedCountLabel)
        self.buttonBox = QtWidgets.QDialogButtonBox(routineSelectDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(False)
        self.buttonBox.setObjectName("buttonBox")
        self.horizontalLayout_2.addWidget(self.buttonBox)
        self.gridLayout.addLayout(self.horizontalLayout_2, 2, 0, 1, 1)
        self.filterCompetitionLabel.setBuddy(self.filterCompetitionComboBox)

        self.retranslateUi(routineSelectDialog)
        self.buttonBox.accepted.connect(routineSelectDialog.accept)
        self.buttonBox.rejected.connect(routineSelectDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(routineSelectDialog)

    def retranslateUi(self, routineSelectDialog):
        _translate = QtCore.QCoreApplication.translate
        routineSelectDialog.setWindowTitle(_translate("routineSelectDialog", "Dialog"))
        self.selectUntrackedButton.setText(_translate("routineSelectDialog", "Select Untracked"))
        self.lastSelectionButton.setText(_translate("routineSelectDialog", "Last Selection"))
        self.filterCompetitionLabel.setText(_translate("routineSelectDialog", "Filter Competition"))
        self.selectedCountLabel.setText(_translate("routineSelectDialog", "0 of 00 selected"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    routineSelectDialog = QtWidgets.QDialog()
    ui = Ui_routineSelectDialog()
    ui.setupUi(routineSelectDialog)
    routineSelectDialog.show()
    sys.exit(app.exec_())


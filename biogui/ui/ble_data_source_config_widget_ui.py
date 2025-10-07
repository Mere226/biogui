# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ble_data_source_config_widget.ui'
##
## Created by: Qt User Interface Compiler version 6.9.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QComboBox, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QSizePolicy,
    QWidget)

class Ui_BLEDataSourceConfigWidget(object):
    def setupUi(self, BLEDataSourceConfigWidget):
        if not BLEDataSourceConfigWidget.objectName():
            BLEDataSourceConfigWidget.setObjectName(u"BLEDataSourceConfigWidget")
        BLEDataSourceConfigWidget.resize(400, 163)
        self.formLayout = QFormLayout(BLEDataSourceConfigWidget)
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setLabelAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.label1 = QLabel(BLEDataSourceConfigWidget)
        self.label1.setObjectName(u"label1")
        self.label1.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label1)

        self.row1Layout = QHBoxLayout()
        self.row1Layout.setObjectName(u"row1Layout")
        self.lineEditName = QLineEdit(BLEDataSourceConfigWidget)
        self.lineEditName.setObjectName(u"lineEditName")

        self.row1Layout.addWidget(self.lineEditName)

        self.pushButtonSearch = QPushButton(BLEDataSourceConfigWidget)
        self.pushButtonSearch.setObjectName(u"pushButtonSearch")
        icon = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.ViewRefresh))
        self.pushButtonSearch.setIcon(icon)

        self.row1Layout.addWidget(self.pushButtonSearch)

        self.row1Layout.setStretch(0, 4)
        self.row1Layout.setStretch(1, 1)

        self.formLayout.setLayout(0, QFormLayout.ItemRole.FieldRole, self.row1Layout)

        self.comboBoxName = QComboBox(BLEDataSourceConfigWidget)
        self.comboBoxName.setObjectName(u"comboBoxName")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.comboBoxName)

        self.label2 = QLabel(BLEDataSourceConfigWidget)
        self.label2.setObjectName(u"label2")
        self.label2.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.label2)

        self.comboBoxService = QComboBox(BLEDataSourceConfigWidget)
        self.comboBoxService.setObjectName(u"comboBoxService")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.comboBoxService)

        self.label3 = QLabel(BLEDataSourceConfigWidget)
        self.label3.setObjectName(u"label3")
        self.label3.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout.setWidget(3, QFormLayout.ItemRole.LabelRole, self.label3)

        self.comboBoxCharacteristic = QComboBox(BLEDataSourceConfigWidget)
        self.comboBoxCharacteristic.setObjectName(u"comboBoxCharacteristic")

        self.formLayout.setWidget(3, QFormLayout.ItemRole.FieldRole, self.comboBoxCharacteristic)

        self.label = QLabel(BLEDataSourceConfigWidget)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label)


        self.retranslateUi(BLEDataSourceConfigWidget)

        QMetaObject.connectSlotsByName(BLEDataSourceConfigWidget)
    # setupUi

    def retranslateUi(self, BLEDataSourceConfigWidget):
        BLEDataSourceConfigWidget.setWindowTitle(QCoreApplication.translate("BLEDataSourceConfigWidget", u"BLE Data Source Configuration", None))
        self.label1.setText(QCoreApplication.translate("BLEDataSourceConfigWidget", u"Device:", None))
#if QT_CONFIG(tooltip)
        self.pushButtonSearch.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.label2.setText(QCoreApplication.translate("BLEDataSourceConfigWidget", u"Service:", None))
        self.label3.setText(QCoreApplication.translate("BLEDataSourceConfigWidget", u"Characteristic:", None))
        self.label.setText("")
    # retranslateUi


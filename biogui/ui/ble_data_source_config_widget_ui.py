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
        BLEDataSourceConfigWidget.resize(465, 309)
        self.formLayout = QFormLayout(BLEDataSourceConfigWidget)
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setLabelAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.row1Layout = QHBoxLayout()
        self.row1Layout.setObjectName(u"row1Layout")
        self.device = QLabel(BLEDataSourceConfigWidget)
        self.device.setObjectName(u"device")
        self.device.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.row1Layout.addWidget(self.device)

        self.lineEditName = QLineEdit(BLEDataSourceConfigWidget)
        self.lineEditName.setObjectName(u"lineEditName")

        self.row1Layout.addWidget(self.lineEditName)

        self.pushButtonSearch = QPushButton(BLEDataSourceConfigWidget)
        self.pushButtonSearch.setObjectName(u"pushButtonSearch")
        icon = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.ViewRefresh))
        self.pushButtonSearch.setIcon(icon)

        self.row1Layout.addWidget(self.pushButtonSearch)

        self.row1Layout.setStretch(0, 1)
        self.row1Layout.setStretch(1, 10)
        self.row1Layout.setStretch(2, 1)

        self.formLayout.setLayout(0, QFormLayout.ItemRole.FieldRole, self.row1Layout)

        self.row2Layout = QHBoxLayout()
        self.row2Layout.setObjectName(u"row2Layout")
        self.statusLabel = QLabel(BLEDataSourceConfigWidget)
        self.statusLabel.setObjectName(u"statusLabel")

        self.row2Layout.addWidget(self.statusLabel)

        self.comboBoxName = QComboBox(BLEDataSourceConfigWidget)
        self.comboBoxName.setObjectName(u"comboBoxName")

        self.row2Layout.addWidget(self.comboBoxName)

        self.row2Layout.setStretch(0, 1)
        self.row2Layout.setStretch(1, 2)

        self.formLayout.setLayout(1, QFormLayout.ItemRole.FieldRole, self.row2Layout)

        self.row3Layout = QHBoxLayout()
        self.row3Layout.setObjectName(u"row3Layout")
        self.service = QLabel(BLEDataSourceConfigWidget)
        self.service.setObjectName(u"service")
        self.service.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.row3Layout.addWidget(self.service)

        self.comboBoxService = QComboBox(BLEDataSourceConfigWidget)
        self.comboBoxService.setObjectName(u"comboBoxService")

        self.row3Layout.addWidget(self.comboBoxService)

        self.row3Layout.setStretch(0, 1)
        self.row3Layout.setStretch(1, 2)

        self.formLayout.setLayout(2, QFormLayout.ItemRole.FieldRole, self.row3Layout)


        self.retranslateUi(BLEDataSourceConfigWidget)

        QMetaObject.connectSlotsByName(BLEDataSourceConfigWidget)
    # setupUi

    def retranslateUi(self, BLEDataSourceConfigWidget):
        BLEDataSourceConfigWidget.setWindowTitle(QCoreApplication.translate("BLEDataSourceConfigWidget", u"BLE Data Source Configuration", None))
        self.device.setText(QCoreApplication.translate("BLEDataSourceConfigWidget", u"Device:", None))
#if QT_CONFIG(tooltip)
        self.pushButtonSearch.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.statusLabel.setText("")
        self.service.setText(QCoreApplication.translate("BLEDataSourceConfigWidget", u"Service:", None))
    # retranslateUi


"""
Classes for the serial data source.


Copyright 2024 Mattia Orlandi, Pierangelo Maria Rapa

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from __future__ import annotations

import logging
import time

from PySide6.QtCore import QByteArray, QIODevice, QLocale
from PySide6.QtGui import QIcon, QIntValidator
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo
from PySide6.QtWidgets import QWidget

from biogui.utils import detectTheme

from ..ui.serial_data_source_config_widget_ui import Ui_SerialDataSourceConfigWidget
from .base import (
    DataSourceConfigResult,
    DataSourceConfigWidget,
    DataSourceType,
    DataSourceWorker,
)


class SerialConfigWidget(DataSourceConfigWidget, Ui_SerialDataSourceConfigWidget):
    """
    Widget to configure the serial source.

    Parameters
    ----------
    parent : QWidget or None, default=None
        Parent QWidget.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        # Setup UI
        self.setupUi(self)
        theme = detectTheme()
        self.rescanSerialPortsButton.setIcon(
            QIcon.fromTheme("view-refresh", QIcon(f":icons/{theme}/reload"))
        )

        self._rescanSerialPorts()
        self.rescanSerialPortsButton.clicked.connect(self._rescanSerialPorts)

        baudRateValidator = QIntValidator(bottom=1, top=4_000_000)
        self.baudRateTextField.setValidator(baudRateValidator)

        self.destroyed.connect(self.deleteLater)

    def validateConfig(self) -> DataSourceConfigResult:
        """
        Validate the configuration.

        Returns
        -------
        DataSourceConfigResult
            Configuration result.
        """
        if self.serialPortsComboBox.currentText() == "":
            return DataSourceConfigResult(
                dataSourceType=DataSourceType.SERIAL,
                dataSourceConfig={},
                isValid=False,
                errMessage='The "serial port" field is empty.',
            )

        if not self.baudRateTextField.hasAcceptableInput():
            return DataSourceConfigResult(
                dataSourceType=DataSourceType.SERIAL,
                dataSourceConfig={},
                isValid=False,
                errMessage='The "baud rate" field is invalid.',
            )

        serialPortName = self.serialPortsComboBox.currentText()
        return DataSourceConfigResult(
            dataSourceType=DataSourceType.SERIAL,
            dataSourceConfig={
                "serialPortName": serialPortName,
                "baudRate": QLocale().toInt(self.baudRateTextField.text())[0],
            },
            isValid=True,
            errMessage="",
        )

    def prefill(self, config: dict) -> None:
        """Pre-fill the form with the provided configuration.

        Parameters
        ----------
        config : dict
            Dictionary with the configuration.
        """
        if "serialPortName" in config:
            self.serialPortsComboBox.setCurrentText(config["serialPortName"])
        if "baudRate" in config:
            self.baudRateTextField.setText(QLocale().toString(config["baudRate"]))

    def getFieldsInTabOrder(self) -> list[QWidget]:
        """
        Get the list of fields in tab order.

        Returns
        -------
        list of QWidgets
            List of the QWidgets in tab order.
        """
        return [
            self.serialPortsComboBox,
            self.rescanSerialPortsButton,
            self.baudRateTextField,
        ]

    def _rescanSerialPorts(self) -> None:
        """Rescan the serial ports to update the combo box."""
        self.serialPortsComboBox.clear()
        self.serialPortsComboBox.addItems(
            [portInfo.portName() for portInfo in QSerialPortInfo.availablePorts()]
        )


class SerialDataSourceWorker(DataSourceWorker):
    """
    Concrete DataSourceWorker that collects data from a serial port.

    Parameters
    ----------
    packetSize : int
        Size of each packet read from the serial port.
    startSeq : list of bytes
        Sequence of commands to start the source.
    stopSeq : list of bytes
        Sequence of commands to stop the source.
    serialPortName : str
        String representing the serial port.
    baudRate : int
        Baud rate.

    Attributes
    ----------
    _packetSize : int
        Size of each packet read from the serial port.
    _startSeq : list of bytes
        Sequence of commands to start the source.
    _stopSeq : list of bytes
        Sequence of commands to stop the source.
    _serialPortName : str
        String representing the serial port.
    _baudRate : int
        Baud rate.
    _serialPort : QSerialPort
        Serial port object.
    _buffer : QByteArray
        Input buffer.

    Class attributes
    ----------------
    dataPacketReady : Signal
        Qt Signal emitted when new data is collected.
    errorOccurred : Signal
        Qt Signal emitted when a communication error occurs.
    """

    def __init__(
        self,
        packetSize: int,
        startSeq: list[bytes],
        stopSeq: list[bytes],
        serialPortName: str,
        baudRate: int,
    ) -> None:
        super().__init__()

        self._packetSize = packetSize
        self._startSeq = startSeq
        self._stopSeq = stopSeq
        self._serialPortName = serialPortName
        self._baudRate = baudRate

        self._serialPort = QSerialPort(self)
        self._serialPort.setPortName(serialPortName)
        self._serialPort.setBaudRate(baudRate)
        self._serialPort.readyRead.connect(self._collectData)
        self._buffer = QByteArray()

        self.destroyed.connect(self.deleteLater)

    def __str__(self):
        return f"Serial port - {self._serialPortName}"

    def startCollecting(self) -> None:
        """Collect data from the configured source."""
        # Open port
        if not self._serialPort.open(QIODevice.ReadWrite):  # type: ignore
            errMsg = f"Cannot open serial port due to the following error:\n{self._serialPort.errorString()}."
            self.errorOccurred.emit(errMsg)
            logging.error("DataWorker: {errMsg}")
            return

        # Start command
        for c in self._startSeq:
            if type(c) is bytes:
                self._serialPort.write(c)
            elif type(c) is float:
                time.sleep(c)

        logging.info("DataWorker: serial communication started.")

    def stopCollecting(self) -> None:
        """Stop data collection."""

        logging.info("DataWorker: serial communication stopped.")

        # Stop command
        for c in self._stopSeq:
            if type(c) is bytes:
                self._serialPort.write(c)
            elif type(c) is float:
                time.sleep(c)

        # Reset input buffer and close port
        while self._serialPort.waitForReadyRead(100):
            self._serialPort.clear()
        self._serialPort.close()
        self._buffer = QByteArray()

    def _collectData(self) -> None:
        """Fill input buffer when data is ready."""
        self._buffer.append(self._serialPort.readAll())
        if self._buffer.size() >= self._packetSize:
            data = self._buffer.mid(0, self._packetSize).data()
            self.dataPacketReady.emit(data)
            self._buffer.remove(0, self._packetSize)

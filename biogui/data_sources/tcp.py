"""
Classes for the TCP socket data source.


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

from PySide6.QtCore import QByteArray, QLocale
from PySide6.QtGui import QIntValidator
from PySide6.QtNetwork import QHostAddress, QTcpServer, QTcpSocket
from PySide6.QtWidgets import QWidget

from ..ui.tcp_data_source_config_widget_ui import Ui_TCPDataSourceConfigWidget
from .base import (
    DataSourceConfigResult,
    DataSourceConfigWidget,
    DataSourceType,
    DataSourceWorker,
)


class TCPConfigWidget(DataSourceConfigWidget, Ui_TCPDataSourceConfigWidget):
    """
    Widget to configure the socket source.

    Parameters
    ----------
    parent : QWidget or None, default=None
        Parent QWidget.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setupUi(self)

        # Validation rules
        lo = QLocale()
        minPort, maxPort = 1024, 49151
        self.socketPortTextField.setToolTip(
            f"Integer between {lo.toString(minPort)} and {lo.toString(maxPort)}"
        )
        portValidator = QIntValidator(bottom=minPort, top=maxPort)
        self.socketPortTextField.setValidator(portValidator)

    def validateConfig(self) -> DataSourceConfigResult:
        """
        Validate the configuration.

        Returns
        -------
        DataSourceConfigResult
            Configuration result.
        """
        lo = QLocale()
        if not self.socketPortTextField.hasAcceptableInput():
            return DataSourceConfigResult(
                dataSourceType=DataSourceType.TCP,
                dataSourceConfig={},
                isValid=False,
                errMessage='The "port" field is invalid.',
            )
        socketPort = lo.toInt(self.socketPortTextField.text())[0]

        return DataSourceConfigResult(
            dataSourceType=DataSourceType.TCP,
            dataSourceConfig={"socketPort": socketPort},
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
        if "socketPort" in config:
            self.socketPortTextField.setText(QLocale().toString(config["socketPort"]))

    def getFieldsInTabOrder(self) -> list[QWidget]:
        """
        Get the list of fields in tab order.

        Returns
        -------
        list of QWidgets
            List of the QWidgets in tab order.
        """
        return [self.socketPortTextField]


class TCPDataSourceWorker(DataSourceWorker):
    """
    Concrete DataSourceWorker that collects data from a TCP socket.

    Parameters
    ----------
    packetSize : int
        Size of each packet read from the socket.
    startSeq : list of bytes
        Sequence of commands to start the source.
    stopSeq : list of bytes
        Sequence of commands to stop the source.
    socketPort: int
        Socket port.

    Attributes
    ----------
    _packetSize : int
        Size of each packet read from the socket.
    _startSeq : list of bytes
        Sequence of commands to start the source.
    _stopSeq : list of bytes
        Sequence of commands to stop the source.
    _socketPort: int
        Socket port.
    _tcpServer : QTcpServer
        Instance of QTcpServer.
    _clientSock : QTcpSocket or None
        Client socket.
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
        socketPort: int,
    ) -> None:
        super().__init__()

        self._packetSize = packetSize
        self._startSeq = startSeq
        self._stopSeq = stopSeq
        self._socketPort = socketPort

        self._tcpServer = QTcpServer(self)
        self._tcpServer.newConnection.connect(self._handleConnection)
        self._clientSock: QTcpSocket | None = None
        self._buffer = QByteArray()

    def __str__(self):
        return f"TCP socket - port {self._socketPort}"

    def startCollecting(self) -> None:
        """Collect data from the configured source."""
        # Start server
        if not self._tcpServer.listen(QHostAddress.Any, self._socketPort):  # type: ignore
            errMsg = f"Cannot start TCP server due to the following error:\n{self._tcpServer.errorString()}."
            self.errorOccurred.emit(errMsg)
            logging.error(f"DataWorker: {errMsg}")
            return

        logging.info(
            f"DataWorker: waiting for TCP connection on port {self._socketPort}."
        )

    def stopCollecting(self) -> None:
        """Stop data collection."""
        if self._clientSock is not None:
            # Stop command
            for c in self._stopSeq:
                if type(c) is bytes:
                    self._clientSock.write(c)
                elif type(c) is float:
                    time.sleep(c)
            self._clientSock.flush()

            # Close socket
            self._clientSock.close()
            self._clientSock.deleteLater()
            self._clientSock = None

        # Close server
        self._tcpServer.close()
        self._buffer = QByteArray()

        logging.info("DataWorker: TCP communication stopped.")

    def _handleConnection(self) -> None:
        """Handle a new TCP connection."""
        self._clientSock = self._tcpServer.nextPendingConnection()
        self._clientSock.readyRead.connect(self._collectData)

        logging.info("DataWorker: new TCP connection.")

        # Start command
        for c in self._startSeq:
            if type(c) is bytes:
                self._clientSock.write(c)
            elif type(c) is float:
                time.sleep(c)

        logging.info("DataWorker: TCP communication started.")

    def _collectData(self) -> None:
        """Fill input buffer when data is ready."""
        self._buffer.append(self._clientSock.readAll())  # type: ignore
        if self._buffer.size() >= self._packetSize:
            data = self._buffer.mid(0, self._packetSize).data()
            self.dataPacketReady.emit(data)
            self._buffer.remove(0, self._packetSize)

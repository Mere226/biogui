"""
Classes for the ble data source.


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

from PySide6.QtCore import QByteArray, QIODevice, QLocale, QTimer, Slot, QObject, Signal, Slot, Qt, QEventLoop
from PySide6.QtGui import QIcon, QIntValidator
from PySide6.QtBluetooth import (
    QBluetoothDeviceDiscoveryAgent, QBluetoothDeviceInfo,
    QLowEnergyController, QLowEnergyService, QLowEnergyCharacteristic, QBluetoothUuid
)
from PySide6.QtWidgets import QWidget

from biogui.utils import detectTheme

from ..ui.ble_data_source_config_widget_ui import Ui_BLEDataSourceConfigWidget
from .base import (
    DataSourceConfigResult,
    DataSourceConfigWidget,
    DataSourceType,
    DataSourceWorker,
)

import struct


class BLEConfigWidget(DataSourceConfigWidget, Ui_BLEDataSourceConfigWidget):
    """
    Widget to configure the serial source.

    Parameters
    ----------
    parent : QWidget or None, default=None
        Parent QWidget.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setupUi(self)
        theme = detectTheme()

        self._discoveryAgent: QBluetoothDeviceDiscoveryAgent | None = None
        self._controller: QLowEnergyController | None = None
        self._currentDevice: QBluetoothDeviceInfo | None = None
        self._restart = False
        self.filterPrefix = ""

        # Cache: device name → list of services
        self.servicesCache: dict[str, list] = {}

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
    
        self._updateStatus("Disconnected", "red")
        self.pushButtonSearch.clicked.connect(self._onButtonClicked)
        self.comboBoxName.activated.connect(self._onUserSelectedDevice)

    def _updateStatus(self, text: str, color: str):
        if self._timer.isActive():
            self._timer.stop()
        self.statusLabel.setText(text)
        self.statusLabel.setStyleSheet(f"color: {color}; font-weight: bold;")
        if text == "Connecting" or text == "Disconnecting":
            self._dots = 0
            self._animText = text
            self._timer.start(500)

    def _animate(self):
        self.statusLabel.setText(self._animText + "." * self._dots)
        self._dots = (self._dots + 1) % 4

    def _onButtonClicked(self):
        filterText = self.lineEditName.text().strip()
        if not filterText:
            filterText = ""
        self.filterPrefix = filterText.lower()
        self._doScan()

    def _onScanFinished(self):
        if self.comboBoxName.count() == 0:
            self.comboBoxName.addItem("No device found")

    def _onUserSelectedDevice(self, index):

        self.comboBoxName.setEnabled(False)

        if index < 0:
            return

        device: QBluetoothDeviceInfo = self.comboBoxName.itemData(index)
        if not isinstance(device, QBluetoothDeviceInfo):
            return

        # If the selected device is already the connected one → do nothing
        if self._currentDevice and device.address() == self._currentDevice.address():
            if self._controller is not None and self._controller.state() in (
                    QLowEnergyController.ConnectingState,
                    QLowEnergyController.ConnectedState,
                    QLowEnergyController.DiscoveringState,
                    QLowEnergyController.DiscoveredState
                ):
                print(f"Device {device.name()} already connected, no action needed.")
                self.comboBoxName.setEnabled(True)
                return

        if hasattr(self, '_connectionTimeout') and self._connectionTimeout.isActive():
            self._connectionTimeout.timeout.disconnect(self._onTimeout)
            self._connectionTimeout.stop()

        self.comboBoxService.clear()
        self._currentDevice = device
        # Changing target
        # if self._currentDevice and device.address() != self._currentDevice.address():
        if self._controller is not None and self._controller.state() in (
                QLowEnergyController.ConnectingState,
                QLowEnergyController.ConnectedState,
                QLowEnergyController.DiscoveringState,
                QLowEnergyController.DiscoveredState
            ):
            self._updateStatus("Disconnecting", "yellow")
            loop = QEventLoop()
            def on_state_changed_for_loop(new_state):
                if new_state == QLowEnergyController.UnconnectedState:
                    if self._controller is not None:
                        self._controller.deleteLater()
                        self._controller = None
                    loop.quit()
            self._controller.stateChanged.connect(on_state_changed_for_loop)
            self._controller.disconnectFromDevice()
            loop.exec()

        deviceAddress = self._currentDevice.address().toString()
        # Device previously discovered (changing target)
        if deviceAddress in self.servicesCache:
            for serviceUUID in self.servicesCache[deviceAddress]:
                self.comboBoxService.addItem(str(serviceUUID), serviceUUID)
            self._updateStatus("Discovered", "orange")
            self.comboBoxName.setEnabled(True)
            return
        
        # Initial pairing or connection to a new device (changing target)
        self._doConnect()
        self.comboBoxName.setEnabled(True)

    def _doScan(self):
        self.comboBoxName.clear()
        if self._discoveryAgent is None:
            self._discoveryAgent = QBluetoothDeviceDiscoveryAgent()
            self._discoveryAgent.deviceDiscovered.connect(self._onDeviceDiscovered)
            self._discoveryAgent.finished.connect(self._onScanFinished)
            self._discoveryAgent.errorOccurred.connect(self._onScanError)
        if self._discoveryAgent.isActive():
            self._discoveryAgent.stop()
        self._discoveryAgent.start(QBluetoothDeviceDiscoveryAgent.LowEnergyMethod)

    def _onDeviceDiscovered(self, info: QBluetoothDeviceInfo):
        name = info.name() or "Unknown"
        address = info.address().toString()
        if self.filterPrefix and name.lower().startswith(self.filterPrefix) or self.filterPrefix == "":
            self.comboBoxName.blockSignals(True)
            self.comboBoxName.addItem(f"{name} ({address})", info)
            self.comboBoxName.blockSignals(False)

        if self._currentDevice != None:
            index = self.comboBoxName.findText(self._currentDevice.name()+" ("+self._currentDevice.address().toString()+")")
            if index >= 0:
                self.comboBoxName.setCurrentIndex(index)
                device: QBluetoothDeviceInfo = self.comboBoxName.itemData(index)
                if self._restart == True: # Timeout
                    self.comboBoxName.setEnabled(False)
                    self._currentDevice = device
                    self._restart = False
                    self._doConnect()
                    self.comboBoxName.setEnabled(True)

    def _doConnect(self):
        if self._discoveryAgent.isActive():
            self._discoveryAgent.stop()
        self._controller = QLowEnergyController.createCentral(self._currentDevice)
        self._controller.connected.connect(self._onConnected)
        self._controller.serviceDiscovered.connect(self._onServiceDiscovered)
        self._controller.discoveryFinished.connect(self._onDiscoveryFinished)

        self._connectionTimeout = QTimer()
        self._connectionTimeout.setSingleShot(True)
        self._connectionTimeout.timeout.connect(self._onTimeout)
        self._connectionTimeout.start(10000)

        self._updateStatus("Connecting","yellow")
        self._controller.connectToDevice()


    def _onTimeout(self):
        self._controller.connected.disconnect(self._onConnected)
        self._controller.serviceDiscovered.disconnect(self._onServiceDiscovered)
        self._controller.discoveryFinished.disconnect(self._onDiscoveryFinished)
        print("Timeout: Failed to establish BLE connection.")
        self._restart = True

        if self._controller is not None and self._controller.state() == QLowEnergyController.ConnectingState:
                self.comboBoxName.setEnabled(False)
                loop = QEventLoop()
                def on_state_changed_for_loop(new_state):
                    if new_state == QLowEnergyController.UnconnectedState:
                        if self._controller is not None:
                            self._controller.deleteLater()
                            self._controller = None
                        loop.quit()
                self._controller.stateChanged.connect(on_state_changed_for_loop)
                self._controller.disconnectFromDevice()
                loop.exec()
                self.comboBoxName.setEnabled(True)

        self._doScan()

    def _onScanError(self, error):
        logging.error(f"Scan error: {error}")

    def _onConnected(self):
        if hasattr(self, '_connectionTimeout') and self._connectionTimeout.isActive():
            self._connectionTimeout.timeout.disconnect(self._onTimeout)
            self._connectionTimeout.stop()
        self._updateStatus("Connected", "green")
        print(self._controller.state())
        print("Connected to:", self._currentDevice.name())
        self._controller.discoverServices()

    def _onServiceDiscovered(self, uuid):
        self.comboBoxService.addItem(str(uuid), uuid)
        print(self._controller.state())

        # cache services for the current device
        deviceAddress = self._currentDevice.address().toString()
        if deviceAddress not in self.servicesCache:
            self.servicesCache[deviceAddress] = [uuid]
        else:
            if uuid not in self.servicesCache[deviceAddress]:
                self.servicesCache[deviceAddress].append(uuid)

    def _onDiscoveryFinished(self):
        print(self._controller.state())
        self._updateStatus("Discovered", "orange")
        if self.comboBoxService.count() == 0:
            self.comboBoxService.addItem("No service found")
            
    def validateConfig(self) -> DataSourceConfigResult:
        """
        Validate the configuration.

        Returns
        -------
        DataSourceConfigResult
            Configuration result.
        """

        if self.comboBoxName.currentText() == "" or self.comboBoxService.currentText() == "":
            return DataSourceConfigResult(
                dataSourceType=DataSourceType.BLE,
                dataSourceConfig={},
                isValid=False,
                errMessage='The field is empty.',
            )

        device = self.comboBoxName.itemData(self.comboBoxName.currentIndex())
        uuid = self.comboBoxService.itemData(self.comboBoxService.currentIndex())

        if self._controller:
            if self._controller.state() in (
                    QLowEnergyController.ConnectedState,
                    QLowEnergyController.DiscoveringState,
                    QLowEnergyController.DiscoveredState
                ):
                self._updateStatus("Disconnecting", "yellow")
                loop = QEventLoop()
                def on_state_changed_for_loop(new_state):
                    if new_state == QLowEnergyController.UnconnectedState:
                        if self._controller is not None:
                            self._controller.deleteLater()
                            self._controller = None
                        loop.quit()
                self._controller.stateChanged.connect(on_state_changed_for_loop)
                self._controller.disconnectFromDevice()
                loop.exec()


        return DataSourceConfigResult(
            dataSourceType=DataSourceType.BLE,
            dataSourceConfig={
                "device": device,
                "uuid": uuid,
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

        self.comboBoxName.addItem(config["device"].name(), config["device"])
        self.comboBoxName.setEnabled(False)
        self.comboBoxService.addItem(str(config["uuid"]), config["uuid"])
        self.comboBoxService.setEnabled(False)

class BLEDataSourceWorker(DataSourceWorker):
    """
    Concrete DataSourceWorker that collects data from a serial port.

    Parameters
    ----------
    packetSize : int
        Size of each packet read from the serial port.
    startSeq : list of bytes or float
        Sequence of commands to start the source.
    stopSeq : list of bytes or float
        Sequence of commands to stop the source.
    """

    sendCommand = Signal(bytes)
    def __init__(
        self,
        packetSize: int,
        startSeq: list[bytes | float],
        stopSeq: list[bytes | float],
        device: QBluetoothDeviceInfo,
        uuid: str,

    ) -> None:
        super().__init__()

        self._packetSize = packetSize
        self._startSeq = startSeq
        self._stopSeq = stopSeq
        self._discoveryAgent: QBluetoothDeviceDiscoveryAgent | None = None
        self._controller: QLowEnergyController | None = None
        self._currentDevice = device
        self._uuid = uuid
        self._buffer = QByteArray()
        self._service = None
        self._writeChar = None
        self._notifyChar = None
        self._state = "idle"
        self._pendingStart = False

    def __str__(self):
        return f"Device - {self._currentDevice.name()}"

    def startCollecting(self):
        """Collect data from the configured source."""

        if self._controller is not None and self._controller.state() != QLowEnergyController.UnconnectedState:
            if self._state != "idle":
                return

        self._state = "scanning"
        if self._discoveryAgent is None:
            self._discoveryAgent = QBluetoothDeviceDiscoveryAgent()
            self._discoveryAgent.deviceDiscovered.connect(self._onDeviceDiscovered)
            self._discoveryAgent.finished.connect(self._onScanFinished)
            self._discoveryAgent.errorOccurred.connect(self._onScanError)
        if self._discoveryAgent.isActive():
            self._discoveryAgent.stop()
        self._discoveryAgent.start(QBluetoothDeviceDiscoveryAgent.LowEnergyMethod)

    def _onDeviceDiscovered(self, info):
        print(info.name() , info.address().toString())
        if info.address() == self._currentDevice.address():
            self._currentDevice = info
            self._discoveryAgent.stop()
            self._doConnect()

    def _doConnect(self):
        self._state = "connecting"

        self._controller = QLowEnergyController.createCentral(self._currentDevice)
        self._controller.connected.connect(self._connected)
        self._controller.stateChanged.connect(self._onStateChanged)
        self._controller.discoveryFinished.connect(self._onDiscoveryFinished)
        
        self._connectionTimeout = QTimer()
        self._connectionTimeout.setSingleShot(True)
        self._connectionTimeout.timeout.connect(self._onTimeout)
        self._connectionTimeout.start(10000) # 10.000 ms = 10 secondi

        print("Connection to:", self._currentDevice.name())
        self._controller.connectToDevice()

    def _connected(self):
        self._connectionTimeout.stop()
        self._state = "connected"
        print(self._currentDevice.name() + " connected")
        self._controller.discoverServices()
        
    def _onDiscoveryFinished(self):
        self._service = self._controller.createServiceObject(self._uuid)
        if self._service:
            self._service.characteristicChanged.connect(self._collectData)
            self._service.stateChanged.connect(self.onServiceStateChanged)
            self._service.discoverDetails()

    def onServiceStateChanged(self, new_state):
        if new_state == QLowEnergyService.ServiceDiscovered:

            for char in self._service.characteristics():
                props = char.properties()
                if props & QLowEnergyCharacteristic.Write:
                    self._writeChar = char
                if props & QLowEnergyCharacteristic.Notify:
                    self._notifyChar = char

            if self._notifyChar and self._notifyChar.isValid():
                cccd = self._notifyChar.descriptor(QBluetoothUuid.ClientCharacteristicConfiguration)
                if cccd.isValid():
                    self._service.descriptorWritten.connect(self._onDescriptorWritten)
                    QTimer.singleShot(500, lambda: self._service.writeDescriptor(cccd, QByteArray.fromHex(b"0100")))
                    # self._service.writeDescriptor(cccd, QByteArray.fromHex(b"0100"))
                else:
                    self._state = "aborting"
                    logging.error("CCCD Descriptor not found or invalid on the peripheral.")
                    self._disconnect()
            else:
                self._state = "aborting"
                logging.warning("Notify characteristic not found in the selected service.")
                self._disconnect()

    def _onDescriptorWritten(self, descriptor, value):
        if descriptor.uuid() == QBluetoothUuid.ClientCharacteristicConfiguration:
            self._service.descriptorWritten.disconnect(self._onDescriptorWritten)
            self._sendStartSequence()
            
    def _sendStartSequence(self):
        for c in self._startSeq:
            if type(c) is bytes:
                payload = (c.decode("utf-8") + "\r\n").encode("utf-8")
                self._service.writeCharacteristic(
                    self._writeChar,
                    QByteArray(payload),
                    QLowEnergyService.WriteWithResponse
                )
            elif type(c) is float:
                time.sleep(c)

        self._state = "streaming"
        print(self._state, "started")
        logging.info("DataWorker: BLE communication started.")

    def stopCollecting(self):
        """Stop data collection."""

        if self._state != "streaming":
            return

        self._state = "stopped"
        print("streaming", self._state)
        logging.info("DataWorker: BLE communication stopped.")

        # Stop command
        for c in self._stopSeq:
            if type(c) is bytes:
                payload = (c.decode("utf-8") + "\r\n").encode("utf-8")
                try:
                    self._service.writeCharacteristic(
                        self._writeChar,
                        QByteArray(payload),
                        QLowEnergyService.WriteWithResponse
                    )
                except RuntimeError as e:
                    print(e)
            elif type(c) is float:
                time.sleep(c)

        self._buffer = QByteArray()
        self._disconnect()

        logging.info("DataWorker: BLE communication stopped.")

    def _disconnect(self):
        if self._controller:
            if self._controller.state() != QLowEnergyController.UnconnectedState:
                self._controller.disconnectFromDevice()
        print("Disconnecting")

    def _onStateChanged(self, new_state):
        if new_state == QLowEnergyController.UnconnectedState:
            if self._state in ("stopped","timeout","connected","streaming"):
                print(self._state)
                print("Device disconnected")
                if self._controller is not None:
                    self._controller.deleteLater()
                    self._controller = None
                self._service = None
                self._writeChar = None
                self._notifyChar = None
                self.startCollecting()
            if self._state == "aborting":
                if self._controller is not None:
                    self._controller.deleteLater()
                    self._controller = None
                self._service = None
                self._state = "idle"

    def _collectData(self, characteristic, data: QByteArray) -> None:
        self._buffer.append(data)
        if self._buffer.size() >= self._packetSize:
            dati = self._buffer.mid(0, self._packetSize).data()
            self.dataPacketReady.emit(dati)
            self._buffer.remove(0, self._packetSize)

    def _onTimeout(self):
        print("Timeout: Failed to establish BLE connection.")
        print (self._controller.state())
        if self._controller is not None and self._controller.state() == QLowEnergyController.ConnectingState:
            self._controller.disconnectFromDevice()
        if self._controller.state() == QLowEnergyController.UnconnectedState:
            self.startCollecting()
        else:
            self._state = "timeout"

    def _onScanFinished(self):
        if self._state == "scanning":
            logging.warning("Device not found")
            self._state = "idle"

    def _onScanError(self, error):
        logging.error(f"Scan error: {error}")
        self._state = "idle"

    def __del__(self):
        if self._controller is not None:
                self._controller.deleteLater()
                self._controller = None

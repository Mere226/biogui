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

from PySide6.QtCore import QByteArray, QIODevice, QLocale, QTimer, Slot, QObject, Signal, Slot, Qt
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
        
        self.discovery_agent = QBluetoothDeviceDiscoveryAgent()
        self.discovery_agent.deviceDiscovered.connect(self.on_device_discovered)
        self.discovery_agent.finished.connect(self.on_scan_finished)

        self.controller: QLowEnergyController | None = None
        self.current_device: QBluetoothDeviceInfo | None = None
        self.user_selected_device = False
        self.filter_prefix = ""

        # Cache: device name → list of services
        self.services_cache: dict[str, list] = {}

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate_connecting)
    
        self._update_status("Disconnected", "red")
        self.pushButtonSearch.clicked.connect(self.on_button_clicked)
        self.comboBoxName.activated.connect(self.on_user_selected_device)

    def _update_status(self, text: str, color: str):
        self.label.setText(text)
        self.label.setStyleSheet(f"color: {color}; font-weight: bold;")

    def _animate_connecting(self):
        if self._show_text:
            self.label.setText("Connecting")
            self._show_text = False
            self._dots = 0
        else:
            self._dots += 1
            self.label.setText("." * self._dots)
            if self._dots >= 3:
                self._show_text = True
                self._dots = 0

    def on_button_clicked(self):
        if not self.comboBoxName.isEnabled():
            self.comboBoxName.setEnabled(True)

        if self.discovery_agent.isActive():
            self.discovery_agent.stop()

        self.comboBoxName.clear()
        self.comboBoxService.clear()
        self.user_selected_device = False
        self.current_device = None

        filter_text = self.lineEditName.text().strip()
        if not filter_text:
            filter_text = ""
 
        self.filter_prefix = filter_text.lower()
        self.discovery_agent.start()

    def on_device_discovered(self, info: QBluetoothDeviceInfo):
        name = info.name() or "Unknown"
        address = info.address().toString()

        if self.filter_prefix and name.lower().startswith(self.filter_prefix) or self.filter_prefix == "":
            self.comboBoxName.blockSignals(True)
            self.comboBoxName.addItem(f"{name} ({address})", info)
            self.comboBoxName.blockSignals(False)

        # The connected device remains displayed even after the scan
        self.comboBoxService.clear()
        if self.current_device != None:
            index = self.comboBoxName.findText(self.current_device.name()+" ("+self.current_device.address().toString()+")")
            if index >= 0:
                self.comboBoxName.setCurrentIndex(index)
                device_addr = self.current_device.address().toString()
                if device_addr in self.services_cache:
                    for service_uuid in self.services_cache[device_addr]:
                        self.comboBoxService.addItem(str(service_uuid), service_uuid)

    def on_scan_finished(self):
        if self.comboBoxName.count() == 0:
            self.comboBoxName.addItem("No device found")

    def on_user_selected_device(self, index):
        if index < 0:
            return
        self.user_selected_device = True

        device: QBluetoothDeviceInfo = self.comboBoxName.itemData(index)
        if not isinstance(device, QBluetoothDeviceInfo):
            return

        # If the selected device is already the connected one → do nothing
        if self.current_device and device.address() == self.current_device.address():
            print(f"Device {device.name()} already connected, no action needed.")
            return
        
        self.comboBoxService.clear()

        if self.current_device and device.address() != self.current_device.address():
            self.controller.disconnectFromDevice()
            print(f"{self.current_device.name()} disconnected, connection to {device.name()}")

        self.current_device = device
        self.controller = QLowEnergyController.createCentral(self.current_device)
        self.controller.connected.connect(self.on_connected)
        self.controller.serviceDiscovered.connect(self.on_service_discovered)
        self.controller.discoveryFinished.connect(self.on_services_finished)

        print("Connection to:", self.current_device.name())
        self._update_status("Connecting","yellow")
        self._show_text = True
        self._timer.start(500)
        self.controller.connectToDevice()

    def on_connected(self):
        self._timer.stop()
        self._update_status("Connected", "green")

        print("Connected to:", self.current_device.name())

        if self.discovery_agent.isActive():
            self.discovery_agent.stop()

        device_addr = self.current_device.address().toString()

        # Check if services are already cached for this device
        if device_addr in self.services_cache:
            for service_uuid in self.services_cache[device_addr]:
                self.comboBoxService.addItem(str(service_uuid), service_uuid)
        else:
            self.controller.discoverServices()

    def on_service_discovered(self, uuid):
        self.comboBoxService.addItem(str(uuid), uuid)

        # cache services for the current device
        device_addr = self.current_device.address().toString()
        if device_addr not in self.services_cache:
            self.services_cache[device_addr] = []
            self.services_cache[device_addr].append(uuid)
            return
        if uuid not in self.services_cache[device_addr]:
            self.services_cache[device_addr].append(uuid)

    def on_services_finished(self):
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
        
        if self.controller:
            self.controller.disconnectFromDevice()

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
        device: str,
        uuid: str,

    ) -> None:
        super().__init__()

        self._current_device=device
        self._packetSize = packetSize
        self._startSeq = startSeq
        self._stopSeq = stopSeq
        self.discovery_agent = QBluetoothDeviceDiscoveryAgent()
        self._controller: QLowEnergyController | None = None
        self._uuid = uuid
        self._buffer = QByteArray()

    def __str__(self):
        return f"Device - {self._current_device.name()}"

    def startCollecting(self):
        """Collect data from the configured source."""

        if self.discovery_agent.isActive():
            self.discovery_agent.stop()
        self.discovery_agent.start()
        
        self._controller = QLowEnergyController.createCentral(self._current_device)
        disconnected = False
        while not disconnected:
            if self._controller.state() in (
                QLowEnergyController.UnconnectedState,
            ):  
                self._controller.connected.connect(self.conn)
                self._controller.discoveryFinished.connect(self.on_discovery_finished)
                print("Connection started")
                self._controller.connectToDevice()
                disconnected = True

    def conn(self):
        if self.discovery_agent.isActive():
            self.discovery_agent.stop()
        print(self._current_device.name() + " connected")
        self._controller.discoverServices()
        
    def on_discovery_finished(self):
        for u in self._controller.services():
                if(u == self._uuid):
                    self._service = self._controller.createServiceObject(self._uuid) 
                    if self._service:
                        self._service.characteristicChanged.connect(self._collectData)
                        self._service.stateChanged.connect(self.on_service_state_changed)
                        self._service.discoverDetails()
                    break

    def on_service_state_changed(self, new_state):
        if new_state == QLowEnergyService.ServiceDiscovered:

            for char in self._service.characteristics():
                props = char.properties()
                if props & QLowEnergyCharacteristic.Write:
                    self._write_char = char
                if props & QLowEnergyCharacteristic.Notify:
                    self._notify_char = char

            ccc_desc = self._notify_char.descriptor(QBluetoothUuid.ClientCharacteristicConfiguration)
            if ccc_desc.isValid():
                self._service.writeDescriptor(ccc_desc, QByteArray.fromHex(b"0100"))
            
            for c in self._startSeq:
                if type(c) is bytes:
                    payload = (c.decode("utf-8") + "\r\n").encode("utf-8")
                    self._service.writeCharacteristic(
                        self._write_char,
                        QByteArray(payload),
                        QLowEnergyService.WriteWithResponse
                    )
                elif type(c) is float:
                    time.sleep(c)
            
            logging.info("DataWorker: BLE communication started.")

    def stopCollecting(self):
        """Stop data collection."""

        logging.info("DataWorker: BLE communication stopped.")

        if self._service and self._controller.state() not in (
                QLowEnergyController.UnconnectedState, 
                QLowEnergyController.ClosingState,
                QLowEnergyController.ConnectingState,
            ):
            # Stop command
            for c in self._stopSeq:
                if type(c) is bytes:
                    payload = (c.decode("utf-8") + "\r\n").encode("utf-8")
                    try:
                        self._service.writeCharacteristic(
                            self._write_char,
                            QByteArray(payload),
                            QLowEnergyService.WriteWithoutResponse
                        )
                    except RuntimeError as e:
                        print(e)
                elif type(c) is float:
                    time.sleep(c)

            self._buffer = QByteArray()
            self._disconnect()

            logging.info("DataWorker: BLE communication stopped.")

    def _disconnect(self):
        if self._service:
            self._service.characteristicChanged.disconnect()
        if self._controller:
            self._controller.disconnectFromDevice()
        print("Connection stopped")

    def _collectData(self, characteristic, data: QByteArray) -> None:
        self._buffer.append(data)
        if self._buffer.size() >= self._packetSize:
            dati = self._buffer.mid(0, self._packetSize).data()
            self.dataPacketReady.emit(dati)
            self._buffer.remove(0, self._packetSize)

    def __del__(self):
        try:
            self.stopCollecting()
        except Exception as e:
            logging.warning(f"Error: {e}")

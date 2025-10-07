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
#        self.agent.errorOccurred.connect(self.on_scan_error)

        self.controller: QLowEnergyController | None = None
        self.current_device: QBluetoothDeviceInfo | None = None
        self.user_selected_device = False
        self.filter_prefix = ""

        # Cache: Name → list of services
        self.device_services_cache: dict[str, list] = {}
        # Cache: service UUID → list of characteristics
        self.services_cache: dict[str, list] = {}

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate_connecting)
    
        self._update_status("Disconnected", "red")
        self.pushButtonSearch.clicked.connect(self.on_button_clicked)
        self.comboBoxName.activated.connect(self.on_user_selected_device)
        self.comboBoxService.currentIndexChanged.connect(self.discover_characteristics)

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

        if self.discovery_agent.isActive():
            self.discovery_agent.stop()

        # Reset combo box
        self.comboBoxName.clear()
        self.comboBoxService.clear()
        self.comboBoxCharacteristic.clear()
        self.user_selected_device = False
#        self.current_device = None
#        self.services_cache.clear()

        filter_text = self.lineEditName.text().strip()
        if not filter_text:
            self.lineEditName.setPlaceholderText("Enter device prefix")
            return

        self.filter_prefix = filter_text.lower()
        self.discovery_agent.start()
        #print("Scan started...")

    def on_device_discovered(self, info: QBluetoothDeviceInfo):
        name = info.name() or "Unknown"
        address = info.address().toString()

        if self.filter_prefix and name.lower().startswith(self.filter_prefix):
            self.comboBoxName.blockSignals(True)
            self.comboBoxName.addItem(f"{name} ({address})", info)
            self.comboBoxName.blockSignals(False)

        # The connected device remains displayed even after the scan
        if self.current_device != None:
            index = self.comboBoxName.findText(self.current_device.name()+" ("+self.current_device.address().toString()+")")
            if index >= 0:
                self.comboBoxName.setCurrentIndex(index)

    def on_scan_finished(self):
        if self.comboBoxName.count() == 0:
            self.comboBoxName.addItem("No device found")

    def on_user_selected_device(self, index):
        if index < 0:
            return
        self.user_selected_device = True

        #print(self.comboBoxName.itemData(index))
        device: QBluetoothDeviceInfo = self.comboBoxName.itemData(index)
        if not isinstance(device, QBluetoothDeviceInfo):
            return

        # If the selected device is already the connected one → do nothing
        if self.current_device and device.address() == self.current_device.address():
            print(f"Device {device.name()} already connected, no action needed.")
            return
        
        self.comboBoxService.clear()
        self.comboBoxCharacteristic.clear()

        if self.current_device and device.address() != self.current_device.address():
            self.controller.disconnectFromDevice()
            print(f"Device {self.current_device.name()} disconnected, connection to {device.name()}")

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

        self.comboBoxService.clear()
        self.comboBoxCharacteristic.clear()
#        self.services_cache.clear()


        device_addr = self.current_device.address().toString()

        # Check if services are already cached for this device
        if device_addr in self.device_services_cache:
            for service_uuid in self.device_services_cache[device_addr]:
                self.comboBoxService.addItem(str(service_uuid), service_uuid)
        else:
            self.controller.discoverServices()

    def on_service_discovered(self, uuid):
        self.comboBoxService.addItem(str(uuid), uuid)

        # cache services for the current device
        device_addr = self.current_device.address().toString()
        if device_addr not in self.device_services_cache:
            self.device_services_cache[device_addr] = []
            self.device_services_cache[device_addr].append(uuid)
            print(self.device_services_cache)
            return
        if uuid not in self.device_services_cache[device_addr]:
            self.device_services_cache[device_addr].append(uuid)
            print(self.device_services_cache)

    def on_services_finished(self):
        if self.comboBoxService.count() == 0:
            self.comboBoxService.addItem("No service found")
        else:
            print(f"Found {self.comboBoxService.count()} services.")

    def discover_characteristics(self):
        idx = self.comboBoxService.currentIndex()
        if idx < 0:
            self.comboBoxCharacteristic.clear()
            return

        service_uuid = self.comboBoxService.itemData(idx)
        if service_uuid is None:
            self.comboBoxCharacteristic.clear()
            return

        service_uuid_str = str(service_uuid)

        # Check if there are characteristics cached for this service
        if service_uuid_str in self.services_cache:
            self._populate_characteristics(self.services_cache[service_uuid_str])
            return

        self.comboBoxCharacteristic.clear()

        # Creating new service
        service = self.controller.createServiceObject(service_uuid)
        if not service:
            print("Unable to create service for UUID:", service_uuid)
            return
        
        # Connect signal to update characteristics when discovery is complete
        service.stateChanged.connect(lambda state, s=service, uuid=service_uuid_str: self._on_service_state_changed(state, s, uuid))
        service.discoverDetails()

    def _on_service_state_changed(self, state, service, uuid):
        if state != QLowEnergyService.ServiceDiscovered:
            return

        characteristics = service.characteristics()

        self.services_cache[uuid] = characteristics
        self._populate_characteristics(characteristics)

    def _populate_characteristics(self, characteristics):
        self.comboBoxCharacteristic.blockSignals(True)
        self.comboBoxCharacteristic.clear()
        for ch in characteristics:
            self.comboBoxCharacteristic.addItem(str(ch.uuid()), ch)
        self.comboBoxCharacteristic.blockSignals(False)
            
    def validateConfig(self) -> DataSourceConfigResult:
        """
        Validate the configuration.

        Returns
        -------
        DataSourceConfigResult
            Configuration result.
        """

        if self.comboBoxName.currentText() == "" or self.comboBoxService.currentText() == "" or self.comboBoxCharacteristic.currentText() == "":
            return DataSourceConfigResult(
                dataSourceType=DataSourceType.BLE,
                dataSourceConfig={},
                isValid=False,
                errMessage='The field is empty.',
            )

        device = self.comboBoxName.itemData(self.comboBoxName.currentIndex())
        uuid = self.comboBoxService.itemData(self.comboBoxService.currentIndex())
        
        write_char = None
        notify_char = None
        
        for i in range(self.comboBoxCharacteristic.count()):
            char: QLowEnergyCharacteristic = self.comboBoxCharacteristic.itemData(i)
            props = char.properties()
            if props & QLowEnergyCharacteristic.Write:
                write_char = char
            if props & QLowEnergyCharacteristic.Notify:
                notify_char = char

        return DataSourceConfigResult(
            dataSourceType=DataSourceType.BLE,
            dataSourceConfig={
                "device": device,
                "controller": self.controller,
                "uuid": uuid,
                "write_char": write_char,
                "notify_char": notify_char,
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
       

    def getFieldsInTabOrder(self) -> list[QWidget]:
        """
        Get the list of fields in tab order.

        Returns
        -------
        list of QWidgets
            List of the QWidgets in tab order.
        """


    def _rescanBleDevices(self) -> None:
        """Rescan the serial ports to update the combo box."""
        


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
        controller: QLowEnergyController,
        uuid: str,
        write_char: str,
        notify_char: str,

    ) -> None:
        super().__init__()

        
        self._device=device
        self._packetSize = packetSize
        self._startSeq = startSeq
        self._stopSeq = stopSeq
        self._write_char = write_char
        self._notify_char = notify_char

        self._service = controller.createServiceObject(uuid)  
        if self._service:
            self._service.characteristicChanged.connect(self._collectData)

        self._buffer = QByteArray()

        # Enable notifications on the notify char
        ccc_desc = self._notify_char.descriptor(QBluetoothUuid.ClientCharacteristicConfiguration)
        if ccc_desc.isValid():
            #0x0100 = notifications on, 0x0000 = notifications off
            self._service.writeDescriptor(ccc_desc, QByteArray.fromHex(b"0100"))

    def __str__(self):
        return f"Device - {self._device}"

    def startCollecting(self) -> None:
        """Collect data from the configured source."""

         # Stop command
        for c in self._startSeq:
            if type(c) is bytes:
                payload = (c.decode("utf-8") + "\r\n").encode("utf-8")
                self._service.writeCharacteristic(
                    self._write_char,
                    QByteArray(payload),
                    QLowEnergyService.WriteWithoutResponse
                )
            elif type(c) is float:
                time.sleep(c)
        
        logging.info("DataWorker: BLE communication started.")

    def stopCollecting(self) -> None:
        """Stop data collection."""

        logging.info("DataWorker: BLE communication stopped.")

        # Stop command
        for c in self._stopSeq:
            if type(c) is bytes:
                payload = (c.decode("utf-8") + "\r\n").encode("utf-8")
                self._service.writeCharacteristic(
                    self._write_char,
                    QByteArray(payload),
                    QLowEnergyService.WriteWithoutResponse
                )
            elif type(c) is float:
                time.sleep(c)

        self._buffer = QByteArray()
    
    def _collectData(self, characteristic, data: QByteArray) -> None:
        # text = data.data().decode("utf-8", errors="ignore")
        nums = struct.unpack(f"{len(data)//4}I", data)
        self._buffer.append(data)
        if self._buffer.size() >= self._packetSize:
            dati = self._buffer.mid(0, self._packetSize).data()
            self.dataPacketReady.emit(dati)
            self._buffer.remove(0, self._packetSize)
            # self.log(f"[NOTIFY] {text}")
            print(f"[NOTIFY] Unpacked numbers: {nums}")

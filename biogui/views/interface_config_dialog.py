"""
Dialog to add a new data source.


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

from PySide6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel, QComboBox, QFormLayout, QApplication, QStyle

class InterfaceConfigDialog(QDialog):
    def __init__(self, configOptions: dict, startSeqTemplate: str, sigInfoTemplate: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Interface Configuration")
        self.resize(300, 200)

        self.combos = {}
        self._startSeq = None
        self._sigInfo = None

        layout = QFormLayout()

        for label_text, options in configOptions.items():
            label = QLabel(label_text)
            combo = QComboBox()

            for k, v in options.items():
                combo.addItem(str(k), userData=v)

            layout.addRow(label, combo)
            self.combos[label_text] = combo

        self.setLayout(layout)

        ok_btn = QPushButton("OK")
        ok_btn.setIcon(QApplication.style().standardIcon(QStyle.SP_DialogOkButton))
        self.startSeqTemplate = startSeqTemplate
        self.sigInfoTemplate = sigInfoTemplate
        ok_btn.clicked.connect(self.onClicked)
        layout.addWidget(ok_btn)

    def onClicked(self):
        """Generates startSeq and sigInfo based on the values selected."""

        startSeqValues = {name: combo.currentData() for name, combo in self.combos.items()}
        sigInfoValues = {name: int(combo.currentText()) for name, combo in self.combos.items()}
        self._startSeq = eval(self.startSeqTemplate.format(**startSeqValues))
        self._sigInfo = eval(self.sigInfoTemplate.format(**sigInfoValues))
        self.accept()

    def startSeq(self):
        """Returns the generated sequence"""

        return self._startSeq

    def sigInfo(self):
        """Returns the generated sequence"""

        return self._sigInfo

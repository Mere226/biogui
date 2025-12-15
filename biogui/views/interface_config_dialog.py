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

from PySide6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel, QComboBox

class InterfaceConfigDialog(QDialog):
    def __init__(self, configOptions: dict, startSeqTemplate: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurazione Interfaccia")
        self.resize(300, 200)

        self.combos = {}
        self._startSeq = None

        layout = QVBoxLayout(self)

        for label_text, options in configOptions.items():
            label = QLabel(label_text)
            combo = QComboBox()
            for k, v in options.items():
                combo.addItem(str(k), userData=v)
            layout.addWidget(label)
            layout.addWidget(combo)
            self.combos[label_text] = combo

        ok_btn = QPushButton("OK")
        self.startSeqTemplate = startSeqTemplate
        ok_btn.clicked.connect(self.onClicked)
        layout.addWidget(ok_btn)

    def onClicked(self):
        """Generates startSeq based on the values selected."""

        values = {name: combo.currentData() for name, combo in self.combos.items()}
        templateFilled = self.startSeqTemplate.format(**values)
        self._startSeq = eval(templateFilled)
        self.accept()

    def startSeq(self):
        """Returns the generated sequence after pressing OK."""

        return self._startSeq



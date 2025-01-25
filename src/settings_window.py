#!/usr/bin/env python3
"""
Settings Window for uPNP Volume Control
Trisha's Note: "Making settings sexy since 2025! 💅"
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QComboBox, QTableWidget, QTableWidgetItem,
                           QHeaderView, QApplication, QTabWidget, QDialog,
                           QLineEdit, QSpinBox, QDoubleSpinBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QColor, QKeySequence
import darkdetect
from profile_manager import ProfileManager, DeviceProfile, KeyBinding, AVAILABLE_ACTIONS

class KeyBindingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Key Binding")
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Description
        desc_layout = QHBoxLayout()
        desc_layout.addWidget(QLabel("Description:"))
        self.description = QLineEdit()
        desc_layout.addWidget(self.description)
        layout.addLayout(desc_layout)
        
        # Key Sequence
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("Shortcut:"))
        self.key_edit = QKeySequence()
        key_layout.addWidget(self.key_edit)
        layout.addLayout(key_layout)
        
        # Action
        action_layout = QHBoxLayout()
        action_layout.addWidget(QLabel("Action:"))
        self.action_combo = QComboBox()
        self.action_combo.addItems(AVAILABLE_ACTIONS.values())
        action_layout.addWidget(self.action_combo)
        layout.addLayout(action_layout)
        
        # Parameters (dynamic based on action)
        self.params_layout = QVBoxLayout()
        layout.addLayout(self.params_layout)
        
        # Buttons
        buttons = QHBoxLayout()
        save_btn = QPushButton("💾 Save")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)
        
        self.setLayout(layout)
        
    def get_binding(self) -> KeyBinding:
        return KeyBinding(
            key=self.key_edit.toString(),
            action=list(AVAILABLE_ACTIONS.keys())[self.action_combo.currentIndex()],
            params={},  # TODO: Get params from dynamic fields
            description=self.description.text()
        )

class ProfileTab(QWidget):
    def __init__(self, profile_manager: ProfileManager):
        super().__init__()
        self.profile_manager = profile_manager
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Profile selection
        profile_layout = QHBoxLayout()
        self.profile_combo = QComboBox()
        self.profile_combo.addItems(self.profile_manager.profiles.keys())
        profile_layout.addWidget(QLabel("Profile:"))
        profile_layout.addWidget(self.profile_combo)
        layout.addLayout(profile_layout)
        
        # Key bindings table
        self.bindings_table = QTableWidget(0, 3)
        self.bindings_table.setHorizontalHeaderLabels(["Description", "Key", "Action"])
        self.bindings_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.bindings_table)
        
        # Volume settings
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("Volume Step:"))
        self.volume_step = QDoubleSpinBox()
        self.volume_step.setRange(0.5, 10)
        self.volume_step.setSingleStep(0.5)
        volume_layout.addWidget(self.volume_step)
        
        volume_layout.addWidget(QLabel("Max Volume:"))
        self.max_volume = QSpinBox()
        self.max_volume.setRange(1, 100)
        volume_layout.addWidget(self.max_volume)
        layout.addLayout(volume_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        add_binding_btn = QPushButton("➕ Add Binding")
        add_binding_btn.clicked.connect(self.add_binding)
        remove_binding_btn = QPushButton("➖ Remove Binding")
        remove_binding_btn.clicked.connect(self.remove_binding)
        button_layout.addWidget(add_binding_btn)
        button_layout.addWidget(remove_binding_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        self.load_current_profile()
        
    def load_current_profile(self):
        profile_name = self.profile_combo.currentText()
        if profile_name in self.profile_manager.profiles:
            profile = self.profile_manager.profiles[profile_name]
            self.bindings_table.setRowCount(len(profile.key_bindings))
            
            for i, binding in enumerate(profile.key_bindings):
                self.bindings_table.setItem(i, 0, QTableWidgetItem(binding.description))
                self.bindings_table.setItem(i, 1, QTableWidgetItem(binding.key))
                self.bindings_table.setItem(i, 2, QTableWidgetItem(
                    AVAILABLE_ACTIONS[binding.action]
                ))
            
            self.volume_step.setValue(profile.volume_step)
            self.max_volume.setValue(profile.max_volume)
    
    def add_binding(self):
        dialog = KeyBindingDialog(self)
        if dialog.exec():
            binding = dialog.get_binding()
            row = self.bindings_table.rowCount()
            self.bindings_table.insertRow(row)
            self.bindings_table.setItem(row, 0, QTableWidgetItem(binding.description))
            self.bindings_table.setItem(row, 1, QTableWidgetItem(binding.key))
            self.bindings_table.setItem(row, 2, QTableWidgetItem(
                AVAILABLE_ACTIONS[binding.action]
            ))
    
    def remove_binding(self):
        current_row = self.bindings_table.currentRow()
        if current_row >= 0:
            self.bindings_table.removeRow(current_row)

class SettingsWindow(QWidget):
    settings_updated = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎵 uPNP Control Settings")
        self.setMinimumWidth(600)
        self.profile_manager = ProfileManager()
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI with a beautiful, modern look"""
        layout = QVBoxLayout()
        
        # Create tab widget
        tabs = QTabWidget()
        
        # Profiles tab
        self.profile_tab = ProfileTab(self.profile_manager)
        tabs.addTab(self.profile_tab, "🎮 Profiles")
        
        # Device selection tab
        device_tab = QWidget()
        device_layout = QVBoxLayout()
        device_label = QLabel("Default Device:")
        self.device_combo = QComboBox()
        device_layout.addWidget(device_label)
        device_layout.addWidget(self.device_combo)
        device_tab.setLayout(device_layout)
        tabs.addTab(device_tab, "🔌 Devices")
        
        layout.addWidget(tabs)
        
        # Save Button
        save_btn = QPushButton("💾 Save Settings")
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)
        
        self.setLayout(layout)
        self.apply_theme()
    
    def apply_theme(self):
        """Apply light/dark theme based on system settings"""
        is_dark = darkdetect.isDark()
        if is_dark:
            self.setStyleSheet("""
                QWidget {
                    background-color: #2D2D2D;
                    color: #FFFFFF;
                }
                QPushButton {
                    background-color: #4A90E2;
                    border: none;
                    padding: 8px;
                    border-radius: 4px;
                }
                QComboBox {
                    background-color: #3D3D3D;
                    border: 1px solid #555;
                    border-radius: 4px;
                    padding: 4px;
                }
                QTableWidget {
                    gridline-color: #555;
                    border: 1px solid #555;
                }
                QTabWidget::pane {
                    border: 1px solid #555;
                }
                QTabBar::tab {
                    background-color: #3D3D3D;
                    padding: 8px;
                    margin-right: 2px;
                }
                QTabBar::tab:selected {
                    background-color: #4A90E2;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #4A90E2;
                    color: white;
                    border: none;
                    padding: 8px;
                    border-radius: 4px;
                }
                QComboBox {
                    border: 1px solid #DDD;
                    border-radius: 4px;
                    padding: 4px;
                }
                QTableWidget {
                    gridline-color: #DDD;
                    border: 1px solid #DDD;
                }
                QTabWidget::pane {
                    border: 1px solid #DDD;
                }
                QTabBar::tab {
                    background-color: #F5F5F5;
                    padding: 8px;
                    margin-right: 2px;
                }
                QTabBar::tab:selected {
                    background-color: #4A90E2;
                    color: white;
                }
            """)
    
    def update_devices(self, devices):
        """Update the devices dropdown with discovered devices"""
        self.device_combo.clear()
        for device in devices:
            self.device_combo.addItem(device.friendly_name)
    
    def save_settings(self):
        """Save current settings"""
        # Save profile changes
        current_profile = self.profile_tab.profile_combo.currentText()
        if current_profile:
            bindings = []
            for row in range(self.profile_tab.bindings_table.rowCount()):
                bindings.append(KeyBinding(
                    key=self.profile_tab.bindings_table.item(row, 1).text(),
                    action=next(k for k, v in AVAILABLE_ACTIONS.items() 
                              if v == self.profile_tab.bindings_table.item(row, 2).text()),
                    params={},  # TODO: Save params
                    description=self.profile_tab.bindings_table.item(row, 0).text()
                ))
            
            profile = DeviceProfile(
                name=current_profile,
                device_pattern=current_profile.lower(),  # TODO: Make this configurable
                manufacturer_pattern="",  # TODO: Make this configurable
                key_bindings=bindings,
                volume_step=self.profile_tab.volume_step.value(),
                max_volume=self.profile_tab.max_volume.value()
            )
            
            self.profile_manager.add_profile(profile)
        
        settings = {
            'default_device': self.device_combo.currentText(),
            'current_profile': current_profile
        }
        
        self.settings_updated.emit(settings)
        self.hide()

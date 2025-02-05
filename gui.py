import sys
import subprocess
import os
import logging
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout, 
                             QTextEdit, QCheckBox, QLabel, QMessageBox, QFrame, QHBoxLayout)
from PyQt5.QtCore import QThread, pyqtSignal, QCoreApplication, Qt
from PyQt5.QtGui import QFont, QColor, QPalette


class Logger:
    def __init__(self):
        self.log_dir = os.path.expanduser("~/.zorin-unlocker/logs")
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_file = os.path.join(self.log_dir, 
            f"zorin_unlocker_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        
        logging.basicConfig(
            filename=self.log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def log(self, message, level=logging.INFO):
        logging.log(level, message)

class UnlockThread(QThread):
    output_received = pyqtSignal(str)
    finished = pyqtSignal(bool)

    def __init__(self, version, more_content, unattended):
        super().__init__()
        self.logger = Logger()
        self.version = version
        self.more_content = more_content
        self.unattended = unattended

    def run(self):
        if os.geteuid() != 0:
            self.output_received.emit("Error: Script must be run with sudo privileges")
            self.finished.emit(False)
            return

        try:
            script_path = "./zorin.sh"
            if not os.access(script_path, os.X_OK):
                self.output_received.emit("Setting execution permissions for zorin.sh")
                os.chmod(script_path, 0o755)

            version_check = subprocess.run(
                "cat /etc/os-release | grep VERSION_ID",
                shell=True, capture_output=True, text=True
            )
            current_version = version_check.stdout.split('=')[1].strip('"').split('.')[0]
            if str(self.version) != current_version:
                self.output_received.emit("Activating Zorin OS Pro version...")

            command = f"./zorin.sh -{self.version}"
            if self.more_content:
                command += " -M"
            if self.unattended:
                command += " -U"

            process = subprocess.Popen(
                command, 
                shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True
            )

            while True:
                line = process.stdout.readline()  # Read the line from stdout
                if not line and process.poll() is not None:  # End of output
                    break
                if line:
                    self.output_received.emit(line.strip())  # Emit line immediately to the GUI
                    self.logger.log(line.strip())  # Log the line
                    QCoreApplication.processEvents()  # Ensure the GUI updates immediately

            success = process.returncode == 0
            self.finished.emit(success)
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.output_received.emit(error_msg)
            self.logger.log(error_msg, logging.ERROR)
            self.finished.emit(False)

class KeyFixThread(QThread):
    output_received = pyqtSignal(str)
    finished = pyqtSignal(bool)

    def run(self):
        try:
            keyservers = [
                "hkps://keyserver.ubuntu.com:443",
                "hkps://keyring.debian.org:443",
                "hkps://keys.openpgp.org:443"
            ]
            
            for server in keyservers:
                self.output_received.emit(f"Trying keyserver: {server}")
                
                command = f"sudo apt-get update 2>&1 | sed -En 's/.*NO_PUBKEY ([[:xdigit:]]+).*/\\1/p' | sort -u"
                process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                keys, _ = process.communicate()
                
                if keys.strip():
                    for key in keys.strip().split('\n'):
                        fix_command = f"sudo gpg --keyserver {server} --recv-keys {key}"
                        self.output_received.emit(f"Importing key {key}")
                        subprocess.run(fix_command, shell=True)
                        
                        export_command = f'sudo gpg --yes --output "/etc/apt/trusted.gpg.d/{key}.gpg" --export "{key}"'
                        subprocess.run(export_command, shell=True)

            self.output_received.emit("Key fix process completed")
            self.finished.emit(True)
            
        except Exception as e:
            self.output_received.emit(f"Error fixing keys: {str(e)}")
            self.finished.emit(False)

class ZorinUnlocker(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.thread = None
        self.key_thread = None
        self.logger = Logger()
        self.set_dark_mode()

    def set_dark_mode(self):
        # Dark Mode Style
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))  # Window background color
        dark_palette.setColor(QPalette.WindowText, Qt.white)  # Text color
        dark_palette.setColor(QPalette.Base, QColor(42, 42, 42))  # QTextEdit background color
        dark_palette.setColor(QPalette.AlternateBase, QColor(66, 66, 66))  # Alt background
        dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(0, 128, 0))  # Button background color (green)
        dark_palette.setColor(QPalette.ButtonText, Qt.white)  # Button text color
        dark_palette.setColor(QPalette.Highlight, QColor(44, 120, 255))  # Highlight color
        dark_palette.setColor(QPalette.HighlightedText, Qt.black)
        
        self.setPalette(dark_palette)
        self.setStyleSheet("""
            QCheckBox { 
                color: white;
                padding-left: 10px;
                padding-right: 10px;
            }
            QCheckBox::indicator {
                border: 2px solid #444444;  /* Border color of checkbox */
                border-radius: 4px;
                background-color: #333333;  /* Background color of checkbox */
            }
            QCheckBox::indicator:checked {
                background-color: green;  /* Checked background color */
                border-color: green;
            }
            QCheckBox::indicator:unchecked {
                background-color: #333333;
            }
            QCheckBox::indicator:checked:hover {
                background-color: #006400;
            }
            QPushButton { 
                color: white; 
                background-color: green; 
                border: none; 
                padding: 10px 20px; 
                border-radius: 10px;  /* Rounded corners */
            }
            QPushButton:hover {  /* Hover effect */
                background-color: #006400;  /* Dark green when hovered */
            }
            QTextEdit { background-color: #2A2A2A; color: white; border: 1px solid #444444; }
            QLabel { color: white; }
        """)

    def initUI(self):
        self.setWindowTitle("Zorin OS Premium Unlocker[by r3df3d]")
        self.setGeometry(500, 400, 800, 500)
        

        main_layout = QVBoxLayout()

        # Header
        header = QLabel("Zorin OS Premium Unlocker")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header)

        # Output console
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setFont(QFont("Consolas", 10))
        main_layout.addWidget(self.output)

        # Options
        options_frame = QFrame()
        options_layout = QHBoxLayout()
        
        self.more_content = QCheckBox("Include More Content (-M)")
        self.unattended = QCheckBox("Unattended Installation (-U)")
        options_layout.addWidget(self.more_content)
        options_layout.addWidget(self.unattended)
        
        options_frame.setLayout(options_layout)
        main_layout.addWidget(options_frame)

        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.btn_zorin16 = QPushButton("Unlock Zorin OS 16")
        self.btn_zorin16.clicked.connect(lambda: self.unlock_premium(16))
        
        self.btn_zorin17 = QPushButton("Unlock Zorin OS 17")
        self.btn_zorin17.clicked.connect(lambda: self.unlock_premium(17))
        
        self.btn_fix_keys = QPushButton("Fix Public Keys")
        self.btn_fix_keys.clicked.connect(self.fix_pubkeys)
        
        buttons_layout.addWidget(self.btn_zorin16)
        buttons_layout.addWidget(self.btn_zorin17)
        buttons_layout.addWidget(self.btn_fix_keys)
        
        main_layout.addLayout(buttons_layout)

        # Add status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #666666;")
        main_layout.addWidget(self.status_label)

        self.setLayout(main_layout)

    def unlock_premium(self, version):
        self.thread = UnlockThread(version, self.more_content.isChecked(), self.unattended.isChecked())
        self.thread.output_received.connect(self.update_output)  # Ensure this is connected
        self.thread.finished.connect(self.unlock_finished)
        self.thread.start()

    def fix_pubkeys(self):
        self.key_thread = KeyFixThread()
        self.key_thread.output_received.connect(self.update_output)
        self.key_thread.finished.connect(self.key_fix_finished)
        self.key_thread.start()

    def update_output(self, text):
        self.output.append(text)  # Append new text to the QTextEdit

    def unlock_finished(self, success):
        if success:
            self.show_info_dialog("Zorin OS Premium Unlocker completed successfully!")
        else:
            self.show_error_dialog("Zorin OS Premium Unlocker failed.")

    def key_fix_finished(self, success):
        if success:
            self.show_info_dialog("Public keys fixed successfully!")
        else:
            self.show_error_dialog("Failed to fix public keys.")

    def show_info_dialog(self, message):
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setWindowTitle("Success")
        msg_box.setText(message)
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #333333;
                color: white;
            }
            QMessageBox QPushButton {
                background-color: #444444;
                color: white;
                border-radius: 5px;
                padding: 5px 10px;
            }
            QMessageBox QPushButton:hover {
                background-color: #006400;
            }
        """)
        msg_box.exec_()

    def show_error_dialog(self, message):
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle("Error")
        msg_box.setText(message)
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #333333;
                color: white;
            }
            QMessageBox QPushButton {
                background-color: #444444;
                color: white;
                border-radius: 5px;
                padding: 5px 10px;
            }
            QMessageBox QPushButton:hover {
                background-color: #800000;
            }
        """)
        msg_box.exec_()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ZorinUnlocker()
    window.show()
    sys.exit(app.exec_())

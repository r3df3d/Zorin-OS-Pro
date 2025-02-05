import sys
import subprocess
import os
import logging
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout, 
                           QTextEdit, QProgressBar, QCheckBox, QLabel, 
                           QMessageBox, QHBoxLayout, QFrame, QAction, QMenuBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor

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
    progress_update = pyqtSignal(int)
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
            # Ensure zorin.sh has execution permissions
            script_path = "./zorin.sh"
            if not os.access(script_path, os.X_OK):
                self.output_received.emit("Setting execution permissions for zorin.sh")
                os.chmod(script_path, 0o755)
                self.logger.log("Added execution permission to zorin.sh")

            # Check Zorin version compatibility
            version_check = subprocess.run(
                "cat /etc/os-release | grep VERSION_ID",
                shell=True, capture_output=True, text=True
            )
            current_version = version_check.stdout.split('=')[1].strip('"').split('.')[0]
            if str(self.version) != current_version:
                self.output_received.emit(f"Warning: Script version {self.version} "
                                       f"may not be compatible with Zorin OS {current_version}")

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

            # Improved progress tracking
            total_steps = subprocess.run(
                f"./zorin.sh -{self.version} --count-steps",
                shell=True, capture_output=True, text=True
            ).stdout.strip()
            steps_completed = 0
            
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    if "Step:" in line:
                        steps_completed += 1
                        progress = int((steps_completed / int(total_steps)) * 100)
                        self.progress_update.emit(progress)
                    self.output_received.emit(line.strip())
                    self.logger.log(line.strip())

            success = process.returncode == 0
            self.finished.emit(success)
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.output_received.emit(error_msg)
            self.logger.log(error_msg, logging.ERROR)
            self.finished.emit(False)

class KeyFixThread(QThread):
    output_received = pyqtSignal(str)
    progress_update = pyqtSignal(int)
    finished = pyqtSignal(bool)

    def run(self):
        try:
            keyservers = [
                "hkps://keyserver.ubuntu.com:443",
                "hkps://keyring.debian.org:443",
                "hkps://keys.openpgp.org:443"
            ]
            
            for i, server in enumerate(keyservers):
                self.output_received.emit(f"Trying keyserver: {server}")
                self.progress_update.emit((i * 30) + 10)
                
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
            self.progress_update.emit(100)
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
        self.error_count = 0
        self.setup_error_timer()
        self.logger = Logger()
        self.init_themes()
        self.current_theme = "dark"

    def init_themes(self):
        self.themes = {
            "dark": {
                "background": "#2e2e2e",
                "text": "#ffffff",
                "button": "#00b828",
                "button_hover": "rgb(0, 155, 52)",
                "console": "#1e1e1e"
            },
            "light": {
                "background": "#f0f0f0",
                "text": "#000000",
                "button": "#2196F3",
                "button_hover": "#1976D2",
                "console": "#ffffff"
            }
        }

    def initUI(self):
        self.setWindowTitle("Zorin OS Premium Unlocker[by r3df3d]")
        self.setGeometry(500, 300, 700, 500)
        self.setStyleSheet("""
            QWidget {
                background-color: #2e2e2e;
                color: #ffffff;
            }
            QPushButton {
                background-color:#00b828;
                border: none;
                padding: 8px;
                border-radius: 4px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color:rgb(0, 155, 52);
            }
            QPushButton:disabled {
                background-color: #666666;
            }
            QTextEdit {
                background-color: #1e1e1e;
                border: 1px solid #3e3e3e;
                border-radius: 4px;
                padding: 4px;
            }
            QCheckBox {
                spacing: 8px;
            }
            QProgressBar {
                border: 1px solid #3e3e3e;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color:rgb(57, 124, 224);
            }
        """)

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

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setMaximum(100)
        self.progress.setValue(0)
        main_layout.addWidget(self.progress)

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

        # Add menu bar with theme toggle
        menubar = QMenuBar(self)
        view_menu = menubar.addMenu('Theme Options')
        
        theme_action = QAction('Dark/White', self)
        theme_action.triggered.connect(self.toggle_theme)
        view_menu.addAction(theme_action)
        
        main_layout.setMenuBar(menubar)

        self.setLayout(main_layout)

    def toggle_theme(self):
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        theme = self.themes[self.current_theme]
        
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {theme['background']};
                color: {theme['text']};
            }}
            QPushButton {{
                background-color: {theme['button']};
                border: none;
                padding: 8px;
                border-radius: 4px;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {theme['button_hover']};
            }}
            QTextEdit {{
                background-color: {theme['console']};
                border: 1px solid #3e3e3e;
                border-radius: 4px;
                padding: 4px;
            }}
            /* ...existing styles... */
        """)

    def setup_error_timer(self):
        self.error_timer = QTimer()
        self.error_timer.timeout.connect(self.reset_error_count)
        self.error_timer.setInterval(60000)  # Reset error count after 1 minute

    def reset_error_count(self):
        self.error_count = 0
        
    def unlock_premium(self, version):
        try:
            if os.geteuid() != 0:
                QMessageBox.critical(self, "Error", 
                    "Please run this application with sudo privileges")
                return

            self.output.clear()
            self.progress.setValue(0)
            self.disable_buttons()

            # Create and run thread in try block
            self.thread = UnlockThread(
                version,
                self.more_content.isChecked(),
                self.unattended.isChecked()
            )
            self.thread.output_received.connect(self.update_output)
            self.thread.progress_update.connect(self.progress.setValue)
            self.thread.finished.connect(self.process_finished)
            self.thread.start()

        except Exception as e:
            self.enable_buttons()
            self.output.append(f"Error: {str(e)}")
            self.logger.log(f"Error in unlock_premium: {str(e)}", logging.ERROR)
            QMessageBox.critical(self, "Error", 
                "An error occurred while starting the unlock process.")

    def fix_pubkeys(self):
        self.output.clear()
        self.progress.setValue(0)
        self.disable_buttons()
        
        self.key_thread = KeyFixThread()
        self.key_thread.output_received.connect(self.update_output)
        self.key_thread.progress_update.connect(self.progress.setValue)
        self.key_thread.finished.connect(self.key_fix_finished)
        self.key_thread.start()

    def disable_buttons(self):
        self.btn_zorin16.setEnabled(False)
        self.btn_zorin17.setEnabled(False)
        self.btn_fix_keys.setEnabled(False)

    def enable_buttons(self):
        self.btn_zorin16.setEnabled(True)
        self.btn_zorin17.setEnabled(True)
        self.btn_fix_keys.setEnabled(True)

    def update_output(self, text):
        self.output.append(text)
        self.output.verticalScrollBar().setValue(
            self.output.verticalScrollBar().maximum()
        )
        self.status_label.setText(f"Status: {text}")

    def process_finished(self, success):
        self.enable_buttons()
        self.progress.setValue(100)

        if success:
            QMessageBox.information(
                self,
                "Success",
                "Zorin OS Premium has been successfully unlocked!\nPlease restart your system."
            )
        else:
            QMessageBox.critical(
                self,
                "Error",
                "An error occurred during the unlock process.\nCheck the output for details."
            )

    def key_fix_finished(self, success):
        self.enable_buttons()
        self.progress.setValue(100)
        
        if success:
            QMessageBox.information(self, "Success", "Public keys have been fixed successfully!")
        else:
            self.error_count += 1
            if self.error_count >= 3:
                self.show_advanced_error_help()
            else:
                QMessageBox.critical(self, "Error", "Failed to fix public keys. Please try again.")

    def show_advanced_error_help(self):
        help_text = """
        Advanced Troubleshooting Steps:
        1. Try running 'sudo apt-get clean'
        2. Try 'sudo rm -rf /var/lib/apt/lists/*'
        3. Try 'sudo apt-get update --fix-missing'
        4. Check your internet connection
        5. Verify system time is correct
        
        Would you like to try automatic advanced fixes?
        """
        reply = QMessageBox.question(self, "Advanced Help", help_text, 
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.run_advanced_fixes()

    def run_advanced_fixes(self):
        commands = [
            "sudo apt-get clean",
            "sudo rm -rf /var/lib/apt/lists/*",
            "sudo apt-get update --fix-missing"
        ]
        
        self.output.append("Running advanced fixes...")
        for cmd in commands:
            try:
                subprocess.run(cmd, shell=True, check=True)
                self.output.append(f"✓ Successfully ran: {cmd}")
            except subprocess.CalledProcessError:
                self.output.append(f"✗ Failed to run: {cmd}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ZorinUnlocker()
    window.show()
    sys.exit(app.exec_())

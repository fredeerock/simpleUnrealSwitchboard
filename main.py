import sys
import subprocess
import socket
from PyQt6 import QtWidgets, QtGui, QtCore
import os
import threading
import time  # Import the time module

class UnrealSyncApp(QtWidgets.QWidget):
    def __init__(self):
        try:
            super().__init__()
            self.unrealEditorPath = 'C:\\Program Files\\Epic Games\\UE_5.4\\Engine\\Binaries\\Win64\\UnrealEditor.exe'
            self.uprojectPath = 'C:\\Users\\dostr\\Documents\\Unreal Projects\\gitSwitchboard\\gitSwitchboard.uproject'
            self.serverProcess = None
            self.session_name = 'Session_1'
            self.initUI()
        except Exception as e:
            self.logMessage(f'Error during initialization: {e}')

    def initUI(self):
        try:
            self.setWindowTitle('Unreal Multi-User Sync & Launch')
            self.setGeometry(100, 100, 400, 600)

            layout = QtWidgets.QVBoxLayout()

            # Start server button
            self.startServerButton = QtWidgets.QPushButton('Start Multiuser Server', self)
            self.startServerButton.clicked.connect(self.startServer)

            # Textbox for Concert session name
            self.concertSessionNameTextbox = QtWidgets.QLineEdit(self)
            self.concertSessionNameTextbox.setPlaceholderText('Concert Session Name')
            self.concertSessionNameTextbox.setText('Session_1')
            self.concertSessionNameTextbox.textChanged.connect(self.updateConcertSessionName)

            # Launch Unreal Editor button
            launchEditorButton = QtWidgets.QPushButton('Launch Unreal Editor', self)
            launchEditorButton.clicked.connect(self.launchLocalServer)

            # Launch Unreal Client button
            launchClientButton = QtWidgets.QPushButton('Launch Unreal Client', self)
            launchClientButton.clicked.connect(self.launchClient)

            # Browse Unreal Editor button
            browseEditorButton = QtWidgets.QPushButton('Browse Unreal Editor', self)
            browseEditorButton.clicked.connect(self.browseUnrealEditor)

            # Browse .uproject file button
            browseUprojectButton = QtWidgets.QPushButton('Browse .uproject File', self)
            browseUprojectButton.clicked.connect(self.browseUproject)

            # Textbox for Unreal Editor path
            self.unrealEditorPathTextbox = QtWidgets.QLineEdit(self)
            self.unrealEditorPathTextbox.setPlaceholderText('Path to Unreal Editor')
            self.unrealEditorPathTextbox.setText(self.unrealEditorPath)
            self.unrealEditorPathTextbox.textChanged.connect(self.updateUnrealEditorPath)

            # Textbox for .uproject file path
            self.uprojectPathTextbox = QtWidgets.QLineEdit(self)
            self.uprojectPathTextbox.setPlaceholderText('Path to .uproject file')
            self.uprojectPathTextbox.setText(self.uprojectPath)

            # Adding widgets to layout
            layout.addWidget(launchEditorButton)
            layout.addWidget(launchClientButton)
            layout.addWidget(self.startServerButton)
            layout.addWidget(self.concertSessionNameTextbox)
            layout.addWidget(browseEditorButton)
            layout.addWidget(self.unrealEditorPathTextbox)
            layout.addWidget(browseUprojectButton)
            layout.addWidget(self.uprojectPathTextbox)
            self.setLayout(layout)
        except Exception as e:
            self.logMessage(f'Error during UI setup: {e}')

    def logMessage(self, message):
        print(message)  # Print to command prompt

    def startServer(self):
        try:
            # Verify paths before starting the server
            if not os.path.isfile(self.unrealEditorPath):
                self.logMessage('Error: Unreal Editor path is invalid.')
                return
            if not os.path.isfile(self.uprojectPath):
                self.logMessage('Error: .uproject file path is invalid.')
                return

            # Start the server in a separate thread
            threading.Thread(target=self._startServerProcess, daemon=True).start()
        except Exception as e:
            self.logMessage(f'Error starting server: {e}')

    def closeEvent(self, event):
        try:
            if self.serverProcess:
                self.logMessage('Terminating server process...')
                self.serverProcess.terminate()
                self.serverProcess.wait()
                self.logMessage('Server process terminated.')
        except Exception as e:
            self.logMessage(f'Error during close event: {e}')
        event.accept()

    def handleAppQuit(self):
        self.closeEvent(QtCore.QEvent(QtCore.QEvent.Type.Close))

    def _startServerProcess(self):
        try:
            server_path = os.path.join(os.path.dirname(self.unrealEditorPath), 'UnrealMultiUserSlateServer.exe')
            if not os.path.isfile(server_path):
                self.logMessage('Error: Unreal Multi-User Slate Server executable not found.')
                return

            command = [
                server_path,
                '-CONCERTSERVER=unrealMUS',
                '-UDPMESSAGING_SHARE_KNOWN_NODES=1',
                '-UDPMESSAGING_TRANSPORT_UNICAST=127.0.0.1:9030',
                '-UDPMESSAGING_TRANSPORT_MULTICAST=230.0.0.1:6666',
                '-messaging'
            ]

            self.logMessage(f"Executing command: {' '.join(command)}")
            self.serverProcess = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.logMessage('Multi-User Server Started Successfully')

            # Monitor the server output
            threading.Thread(target=self.readServerOutput, daemon=True).start()
            threading.Thread(target=self.readServerError, daemon=True).start()

        except FileNotFoundError as fnf_error:
            self.logMessage(f'FileNotFoundError: {fnf_error}')
        except Exception as e:
            self.logMessage(f'Unexpected error: {e}')

    def readServerOutput(self):
        try:
            while True:
                output = self.serverProcess.stdout.readline()
                if output == '' and self.serverProcess.poll() is not None:
                    break
                if output:
                    self.logMessage(output.strip())
            rc = self.serverProcess.poll()
            self.logMessage(f'Server process exited with return code: {rc}')
            return rc
        except Exception as e:
            self.logMessage(f'Error reading server output: {e}')

    def readServerError(self):
        try:
            while True:
                error_output = self.serverProcess.stderr.readline()
                if error_output == '' and self.serverProcess.poll() is not None:
                    break
                if error_output:
                    self.logMessage(f"ERROR: {error_output.strip()}")
            rc = self.serverProcess.poll()
            self.logMessage(f'Server process exited with return code: {rc}')
            return rc
        except Exception as e:
            self.logMessage(f'Error reading server error output: {e}')

    def launchClient(self):
        try:
            if not os.path.isfile(self.unrealEditorPath):
                self.logMessage('Error: Unreal Editor path not set.')
                return
            if not os.path.isfile(self.uprojectPath):
                self.logMessage('Error: .uproject file path not set.')
                return
            if not self.session_name:
                self.logMessage('Error: Multi-User session not started.')
                return

            command = [
                self.unrealEditorPath, self.uprojectPath,
                '-game', '/Game/Main', '-messaging', '-nosplash', '-fixedseed',
                '-UDPMESSAGING_TRANSPORT_MULTICAST=230.0.0.1:6666',
                '-UDPMESSAGING_TRANSPORT_UNICAST=127.0.0.1:0',
                '-UDPMESSAGING_TRANSPORT_STATIC=127.0.0.1:9030',
                f'-CONCERTSESSION={self.session_name}',
                '-CONCERTDISPLAYNAME=Node_0'
            ]
            self.logMessage(f"Executing command: {' '.join(command)}")
            subprocess.Popen(command)
            self.logMessage('Client launched in viewer mode')
        except Exception as e:
            self.logMessage(f'Error launching client: {e}')

    def launchLocalServer(self):
        try:
            if not os.path.isfile(self.unrealEditorPath):
                self.logMessage('Error: Unreal Editor path not set.')
                return
            if not os.path.isfile(self.uprojectPath):
                self.logMessage('Error: .uproject file path not set.')
                return
            if not self.session_name:
                self.logMessage('Error: Multi-User session not started.')
                return

            command = [
                self.unrealEditorPath, self.uprojectPath,
                '/Game/Main', 'Log=Editor_1.log',
                '-CONCERTAUTOCONNECT', f'-CONCERTSESSION={self.session_name}',
                '-CONCERTDISPLAYNAME=Editor_1',
                '-UDPMESSAGING_TRANSPORT_MULTICAST=230.0.0.1:6666',
                '-UDPMESSAGING_TRANSPORT_UNICAST=127.0.0.1:0',
                '-UDPMESSAGING_TRANSPORT_STATIC=127.0.0.1:9030'
            ]
            self.logMessage(f"Executing command: {' '.join(command)}")
            subprocess.Popen(command)
            self.logMessage('Local Unreal Project launched and joined the session')
        except Exception as e:
            self.logMessage(f'Error launching local server: {e}')

    def browseUnrealEditor(self):
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select Unreal Editor", "", "Executables (*.exe);;All Files (*)")
        if fileName:
            self.unrealEditorPath = fileName
            self.unrealEditorPathTextbox.setText(fileName)

    def browseUproject(self):
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select .uproject File", "", "Unreal Project Files (*.uproject);;All Files (*)")
        if fileName:
            self.uprojectPath = fileName
            self.uprojectPathTextbox.setText(fileName)

    def updateUnrealEditorPath(self, text):
        self.unrealEditorPath = text

    def updateConcertSessionName(self, text):
        self.session_name = text

def main():
    try:
        app = QtWidgets.QApplication(sys.argv)
        ex = UnrealSyncApp()
        ex.show()
        app.aboutToQuit.connect(ex.handleAppQuit)
        sys.exit(app.exec())
    except Exception as e:
        print(f'Unhandled exception: {e}')

if __name__ == '__main__':
    main()

import sys
import subprocess
import socket
from PyQt6 import QtWidgets, QtGui, QtCore
import os
import threading
import time
import signal
import shutil
import hashlib
import ast
from PyQt6.QtCore import QThread, pyqtSignal

class SyncThread(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal()
    
    def __init__(self, app, editor_folder, listener_folder):
        super().__init__()
        self.app = app
        self.editor_folder = editor_folder
        self.listener_folder = listener_folder

    def run(self):
        try:
            if not os.path.isdir(self.editor_folder):
                self.progress.emit('Error: Editor folder path is invalid.')
                return

            self.progress.emit(f'Syncing from {self.editor_folder} to {self.app.listener_ip}:{self.listener_folder}')

            # Get checksums of files on the listener side
            listener_checksums = self.app.getListenerChecksums(self.listener_folder)
            self.progress.emit('Received listener checksums')

            # Send the contents of the editor folder to the listener
            for root, dirs, files in os.walk(self.editor_folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, self.editor_folder)

                    # Calculate checksum of the local file
                    local_checksum = self.app.calculate_checksum(file_path)

                    # Compare checksums and send file if different
                    if listener_checksums.get(relative_path) != local_checksum:
                        self.progress.emit(f'Syncing {relative_path}...')
                        self.app.sendFileToListener(file_path, os.path.join(self.listener_folder, relative_path))
                    else:
                        self.progress.emit(f'Skipping {relative_path} (unchanged)')

            self.progress.emit('Folders synced successfully.')
            self.finished.emit()
        except Exception as e:
            self.progress.emit(f'Error syncing folders: {e}')
            self.finished.emit()

class UnrealSyncApp(QtWidgets.QWidget):
    def __init__(self):
        try:
            super().__init__()
            # Initialize default paths and variables
            self.unrealEditorPath = 'C:\\Program Files\\Epic Games\\UE_5.4\\Engine\\Binaries\\Win64\\UnrealEditor.exe'
            self.uprojectPath = 'C:\\Users\\dostr\\Documents\\Unreal Projects\\gitSwitchboard\\gitSwitchboard.uproject'
            self.serverProcess = None
            self.session_name = 'Session_1'
            self.listener_ip = '127.0.0.1'
            self.concert_server_name = 'unrealMUS'
            self.listenerUprojectPath = 'C:\\Users\\dostr\\OneDrive - Louisiana State University\\Desktop\\synctest\\gitSwitchboard.uproject'
            self.listenerUnrealEditorPath = ''
            self.initUI()
        except Exception as e:
            self.logMessage(f'Error during initialization: {e}')

    def initUI(self):
        try:
            self.setWindowTitle('Unreal Multi-User Sync & Launch')
            self.setGeometry(100, 100, 400, 600)

            layout = QtWidgets.QVBoxLayout()
            formLayout = QtWidgets.QFormLayout()

            # Start server button
            self.startServerButton = QtWidgets.QPushButton('Start Multiuser Server', self)
            self.startServerButton.clicked.connect(self.startServer)

            # Label and textbox for Concert server name
            concertServerNameLabel = QtWidgets.QLabel('Concert Server Name:', self)
            self.concertServerNameTextbox = QtWidgets.QLineEdit(self)
            self.concertServerNameTextbox.setPlaceholderText('Concert Server Name')
            self.concertServerNameTextbox.setText(self.concert_server_name)
            self.concertServerNameTextbox.setToolTip('Specify the name of the Concert server (Multi-User server). Default is "unrealMUS".')
            self.concertServerNameTextbox.textChanged.connect(self.updateConcertServerName)

            # Label and textbox for Concert session name
            concertSessionNameLabel = QtWidgets.QLabel('Concert Session Name:', self)
            self.concertSessionNameTextbox = QtWidgets.QLineEdit(self)
            self.concertSessionNameTextbox.setPlaceholderText('Concert Session Name')
            self.concertSessionNameTextbox.setText('Session_1')
            self.concertSessionNameTextbox.setToolTip('Specify the name of the Concert session. Default is "Session_1".')
            self.concertSessionNameTextbox.textChanged.connect(self.updateConcertSessionName)

            # Label and textbox for Listener IP address
            listenerIpLabel = QtWidgets.QLabel('Listener IP Address:', self)
            self.listenerIpTextbox = QtWidgets.QLineEdit(self)
            self.listenerIpTextbox.setPlaceholderText('Listener IP Address')
            self.listenerIpTextbox.setText(self.listener_ip)
            self.listenerIpTextbox.setToolTip('Specify the IP address of the listener application. Default is "127.0.0.1".')
            self.listenerIpTextbox.textChanged.connect(self.updateListenerIp)

            # Label and textbox for Unreal Editor path
            unrealEditorPathLabel = QtWidgets.QLabel('Path to Unreal Editor:', self)
            self.unrealEditorPathTextbox = QtWidgets.QLineEdit(self)
            self.unrealEditorPathTextbox.setPlaceholderText('Path to Unreal Editor')
            self.unrealEditorPathTextbox.setText(self.unrealEditorPath)
            self.unrealEditorPathTextbox.setToolTip('Specify the path to the Unreal Editor executable.')
            self.unrealEditorPathTextbox.textChanged.connect(self.updateUnrealEditorPath)

            # Label and textbox for .uproject file path
            uprojectPathLabel = QtWidgets.QLabel('Editor .uproject file:', self)
            self.uprojectPathTextbox = QtWidgets.QLineEdit(self)
            self.uprojectPathTextbox.setPlaceholderText('Editor .uproject file')
            self.uprojectPathTextbox.setText(self.uprojectPath)
            self.uprojectPathTextbox.setToolTip('Specify the path to the .uproject file for the editor.')

            # Label and textbox for listener .uproject file path
            listenerUprojectPathLabel = QtWidgets.QLabel('Listener .uproject Path:', self)
            self.listenerUprojectPathTextbox = QtWidgets.QLineEdit(self)
            self.listenerUprojectPathTextbox.setPlaceholderText('Listener .uproject Path')
            self.listenerUprojectPathTextbox.setText(self.listenerUprojectPath)  # Set initial text
            self.listenerUprojectPathTextbox.setToolTip('Specify the path to the .uproject file for the listener.')
            self.listenerUprojectPathTextbox.textChanged.connect(self.updateListenerUprojectPath)

            # Label and textbox for listener Unreal Editor path
            listenerUnrealEditorPathLabel = QtWidgets.QLabel('Listener Unreal Editor Path:', self)
            self.listenerUnrealEditorPathTextbox = QtWidgets.QLineEdit(self)
            self.listenerUnrealEditorPathTextbox.setPlaceholderText('Listener Unreal Editor Path')
            self.listenerUnrealEditorPathTextbox.setToolTip('Specify the path to the Unreal Editor executable for the listener.')
            self.listenerUnrealEditorPathTextbox.textChanged.connect(self.updateListenerUnrealEditorPath)

            # Launch Unreal Editor button
            launchEditorButton = QtWidgets.QPushButton('Launch Unreal Editor', self)
            launchEditorButton.clicked.connect(self.launchLocalServer)

            # Launch Unreal Client button
            launchClientButton = QtWidgets.QPushButton('Launch Unreal Client', self)
            launchClientButton.clicked.connect(self.launchClient)

            # Sync folders button
            syncFoldersButton = QtWidgets.QPushButton('Sync Folders', self)
            syncFoldersButton.clicked.connect(self.syncFolders)

            # Browse Unreal Editor button
            browseEditorButton = QtWidgets.QPushButton('Browse Unreal Editor', self)
            browseEditorButton.clicked.connect(self.browseUnrealEditor)

            # Browse .uproject file button
            browseUprojectButton = QtWidgets.QPushButton('Browse .uproject File', self)
            browseUprojectButton.clicked.connect(self.browseUproject)

            # Status box for sync operation
            self.statusBox = QtWidgets.QTextEdit(self)
            self.statusBox.setReadOnly(True)
            self.statusBox.setPlaceholderText('Status messages will appear here...')

            # Adding widgets to form layout
            formLayout.addRow(concertServerNameLabel, self.concertServerNameTextbox)
            formLayout.addRow(concertSessionNameLabel, self.concertSessionNameTextbox)
            formLayout.addRow(listenerIpLabel, self.listenerIpTextbox)
            formLayout.addRow(unrealEditorPathLabel, self.unrealEditorPathTextbox)
            formLayout.addRow(uprojectPathLabel, self.uprojectPathTextbox)
            formLayout.addRow(listenerUprojectPathLabel, self.listenerUprojectPathTextbox)
            formLayout.addRow(listenerUnrealEditorPathLabel, self.listenerUnrealEditorPathTextbox)

            # Adding buttons to layout
            layout.addWidget(self.startServerButton)
            layout.addWidget(launchEditorButton)
            layout.addWidget(launchClientButton)
            layout.addWidget(syncFoldersButton)
            layout.addWidget(browseEditorButton)
            layout.addWidget(browseUprojectButton)
            layout.addLayout(formLayout)
            layout.addWidget(self.statusBox)

            self.setLayout(layout)
        except Exception as e:
            self.logMessage(f'Error during UI setup: {e}')

    def logMessage(self, message):
        print(message)  # Print to command prompt
        self.statusBox.append(message)  # Append message to status box

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
                f'-CONCERTSERVER={self.concert_server_name}',
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

            data = {
                'unrealEditorPath': self.unrealEditorPath,
                'uprojectPath': self.uprojectPath,
                'session_name': self.session_name,
                'concert_server_name': self.concert_server_name,
                'listenerUprojectPath': self.listenerUprojectPath,
                'listenerUnrealEditorPath': self.listenerUnrealEditorPath
            }
            self.logMessage(f"Sending data to listener: {data}")
            self.sendDataToListener(data)
        except Exception as e:
            self.logMessage(f'Error launching client: {e}')

    def sendDataToListener(self, data):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.listener_ip, 65432))
                s.sendall(str(data).encode())
                self.logMessage('Data sent to listener')
        except Exception as e:
            self.logMessage(f'Error sending data to listener: {e}')

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
                'Log=Editor_1.log',
                '-CONCERTRETRYAUTOCONNECTONERROR', '-CONCERTAUTOCONNECT',
                f'-CONCERTSERVER="{self.concert_server_name}"', f'-CONCERTSESSION="{self.session_name}"',
                '-CONCERTDISPLAYNAME="Editor_1"', '-StageFriendlyName="Editor_1"',
                '-DPCVars="Slate.bAllowThrottling=0"', '-ConcertReflectVisibility=1',
                '-UDPMESSAGING_TRANSPORT_MULTICAST="230.0.0.1:6666"',
                '-UDPMESSAGING_TRANSPORT_UNICAST="127.0.0.1:0"',
                '-UDPMESSAGING_TRANSPORT_STATIC="127.0.0.1:9030"'
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

    def updateListenerIp(self, text):
        self.listener_ip = text

    def updateConcertServerName(self, text):
        self.concert_server_name = text

    def updateListenerUprojectPath(self, text):
        self.listenerUprojectPath = text

    def updateListenerUnrealEditorPath(self, text):
        self.listenerUnrealEditorPath = text

    def syncFolders(self):
        try:
            editor_folder = os.path.dirname(self.uprojectPath)
            listener_folder = os.path.dirname(self.listenerUprojectPath)

            # Create and start sync thread
            self.sync_thread = SyncThread(self, editor_folder, listener_folder)
            self.sync_thread.progress.connect(self.logMessage)
            self.sync_thread.start()

            # Create progress dialog
            self.progress_dialog = QtWidgets.QProgressDialog("Syncing folders...", "Cancel", 0, 0, self)
            self.progress_dialog.setWindowTitle("Sync Progress")
            self.progress_dialog.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
            self.progress_dialog.setAutoClose(False)
            self.progress_dialog.canceled.connect(self.sync_thread.terminate)
            self.sync_thread.finished.connect(self.progress_dialog.close)
            self.progress_dialog.show()

        except Exception as e:
            self.logMessage(f'Error starting sync: {e}')

    def calculate_checksum(self, file_path):
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.md5()
                while chunk := f.read(8192):
                    file_hash.update(chunk)
            return file_hash.hexdigest()
        except Exception as e:
            self.logMessage(f'Error calculating checksum for {file_path}: {e}')
            return None

    def getListenerChecksums(self, listener_folder):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.listener_ip, 65432))
                message = {'command': 'get_checksums', 'folder': listener_folder}
                
                # Send the request
                message_str = str(message).encode('utf-8')
                message_length = len(message_str)
                s.sendall(message_length.to_bytes(4, 'big'))
                s.sendall(message_str)

                # Receive the response
                data_length = int.from_bytes(s.recv(4), 'big')
                data = b''
                while len(data) < data_length:
                    chunk = s.recv(min(4096, data_length - len(data)))
                    if not chunk:
                        break
                    data += chunk

                if len(data) == data_length:
                    response = data.decode('utf-8')
                    return ast.literal_eval(response)
                else:
                    self.logMessage('Error: Incomplete data received')
                    return {}

        except Exception as e:
            self.logMessage(f'Error getting checksums from listener: {str(e)}')
            return {}

    def sendFileToListener(self, file_path, dest_path):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.listener_ip, 65432))
                with open(file_path, 'rb') as f:
                    data = f.read()
                message = {
                    'command': 'sync_file',
                    'dest_path': dest_path,
                    'file_data': data.hex()
                }
                message_str = str(message).encode()
                message_length = len(message_str)
                s.sendall(message_length.to_bytes(4, 'big') + message_str)
                self.logMessage(f'Sent file {file_path} to listener')
        except Exception as e:
            self.logMessage(f'Error sending file to listener: {e}')

def main():
    try:
        app = QtWidgets.QApplication(sys.argv)
        ex = UnrealSyncApp()
        ex.show()
        app.aboutToQuit.connect(ex.handleAppQuit)

        # Handle SIGINT (Ctrl-C)
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        sys.exit(app.exec())
    except KeyboardInterrupt:
        print('Application interrupted by user')
        sys.exit(0)
    except Exception as e:
        print(f'Unhandled exception: {e}')

if __name__ == '__main__':
    main()

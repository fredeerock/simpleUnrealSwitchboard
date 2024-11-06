# Unreal Multi-User Sync & Launch

This project provides a tool to sync and launch Unreal Engine projects in a multi-user environment. It includes a main application to manage the Unreal Editor and a listener application to handle file synchronization.

## Features

- Start and stop a multi-user server for Unreal Engine
- Launch Unreal Editor and clients
- Sync project files between the main application and a listener
- Compare files using checksums to ensure data integrity
- Progress dialog for sync operations

## Download

Download the latest binares from the [releases page](https://github.com/fredeerock/simpleUnrealSwitchboard/releases).

## Usage

### Main Application

1. Open SimpleUnrealSwitchboard.exe on the computer you use to control Unreal. 

2. Configure the paths for the Unreal Editor and .uproject files in the UI.

3. Use the buttons to start the server, launch the editor, launch clients, and sync folders.

### Listener Application

1. Open SimpleUnrealSwitchboardListener.exe on the computer you want Unreal to be viewable on. 

2. Ensure the listener is running and accessible from the main application.

## Configuration

- **Concert Server Name**: Name of the multi-user server.
- **Concert Session Name**: Name of the session to join.
- **Listener IP Address**: IP address of the listener application.
- **Path to Unreal Editor**: Path to the Unreal Editor executable.
- **Editor .uproject file**: Path to the .uproject file for the editor.
- **Listener .uproject Path**: Path to the .uproject file for the listener.
- **Listener Unreal Editor Path**: Path to the Unreal Editor executable for the listener.

## Syncing Folders

1. Click the "Sync Folders" button to start the sync process.
2. Files will be compared using checksums and only changed files will be transferred.

## Running From Source

1. Clone the repository:
    ```sh
    git clone https://github.com/fredeerock/simpleUnrealSwitchboard.git
    cd simpleUnrealSwitchboard
    ```

2. Install the required Python packages:
    ```sh
    pip install PyQt6
    ```

1. Run the main application:
    ```sh
    python main.py
    ```

1. Run the listener application:
    ```sh
    python listener.py
    ```

## Building Executables

To create standalone executables:

1. Install PyInstaller:
    ```sh
    pip install pyinstaller
    ```

2. Build the executables:
    ```sh
    # Build main application
    pyinstaller --name SimpleUnrealSwitchboard --onefile --noconsole main.py

    # Build listener application
    pyinstaller --name SimpleUnrealSwitchboardListener --onefile listener.py
    ```

The executables will be created in the `dist` folder:
- `UnrealSwitchboard.exe` - Main application
- `UnrealSwitchboardListener.exe` - Listener application

These executables can be distributed to users who don't have Python installed.
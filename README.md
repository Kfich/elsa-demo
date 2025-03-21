# Canvas-based Applications Suite

This project is a suite of interactive applications built on top of a common socket-based canvas API. The applications range from productivity tools like a text editor and collaborative whiteboard to games and development tools.

## Project Structure

The project is organized as follows:

```
project_root/
│
├── socket_canvas.py         # Core canvas API (required for all applications)
│
├── app.py  # Main entry screen for all applications
│
├── Text Editor/
│   ├── main.py              # Text editor entry point
│   ├── TextEditor.py        # Main editor controller
│   ├── TextBuffer.py        # Text content management
│   ├── Renderer.py          # UI rendering
│   └── TextEditorClient.py  # Canvas client interface
│
├── Chess/
│   ├── chess.py             # Chess game entry point
│   ├── chess_server.py      # Game server for multiplayer
│   └── chess_client.py      # Chess game client
│
├── Whiteboard/
│   ├── whiteboard_main.py         # Whiteboard launcher
│   ├── whiteboard_server.py       # Collaboration server
│   ├── whiteboard_client.py       # Standalone client
│   └── whiteboard_client_collab.py # Collaborative client
│
└── Code Editor/
    ├── code_editor.py       # Code editor launcher
    └── code_editor_client.py # Code editor implementation
```

### Core Components

- **socket_canvas.py**: The foundation of all applications. This creates a Tkinter canvas that is accessible via a TCP socket, allowing applications to draw on it and receive user input events.

### Applications

1. **Text Editor**: A feature-rich text editor with syntax highlighting, line numbers, and standard editing features.

2. **Chess Game**: A multiplayer chess application with a lobby system, allowing users to create and join games.

3. **Whiteboard**: A drawing application with real-time collaboration features, allowing multiple users to draw together.

4. **Code Editor**: A Python code editor with execution visualization, helping users understand how their code runs step by step.

## Running the Applications

### Prerequisites

- Python 3.x
- Tkinter (included with most Python installations)

### Socket Canvas (Required for all applications)

The socket canvas must be running before launching any application. It provides the drawing surface and input handling for all applications.

```bash
python socket_canvas.py [--port PORT]
```

Options:
- `--port PORT`: Specify the port to listen on (default: 5005)

Example:
```bash
python socket_canvas.py --port 5005
```

### Text Editor

A feature-rich text editor with line numbers, syntax highlighting, and standard editing capabilities.

```bash
python main.py [--host HOST] [--port PORT]
```

Options:
- `--host HOST`: Canvas API host (default: localhost)
- `--port PORT`: Canvas API port (default: 5005)

Example:
```bash
python main.py --host localhost --port 5005
```

Keyboard shortcuts:
- Ctrl+C: Copy
- Ctrl+X: Cut
- Ctrl+V: Paste
- Ctrl+A: Select All
- Ctrl+N: New File
- Ctrl+L: Toggle Line Numbers
- Ctrl+H: Toggle Help

### Chess Game

A multiplayer chess game with a lobby system for creating and joining games.

```bash
python chess.py [--canvas-port PORT] [--server-port PORT] [--name NAME] [--players NUM]
```

Options:
- `--canvas-port PORT`: Port for canvas server (default: 5005)
- `--server-port PORT`: Port for game server (default: 5006)
- `--name NAME`: Player name
- `--players NUM`: Number of clients to start (default: 1)

Example:
```bash
# Start with a single client
python chess.py --name Player1

# Start with two clients (for testing on one computer)
python chess.py --players 2
```

You can also start each component individually:

```bash
# Start the chess server
python chess_server.py [--host HOST] [--port PORT]

# Start a chess client
python chess_client.py [--port PORT] [--server-port PORT] [--name NAME]
```

### Whiteboard

A collaborative drawing application with real-time updates across clients.

```bash
python whiteboard_main.py [--canvas-port PORT] [--server-port PORT] [--username NAME] [--clients NUM] [--standalone]
```

Options:
- `--canvas-port PORT`: Port for canvas server (default: 5005)
- `--server-port PORT`: Port for collaboration server (default: 5006)
- `--username NAME`: Username for client
- `--clients NUM`: Number of clients to start (default: 1)
- `--standalone`: Run standalone (non-collaborative) client

Example:
```bash
# Start collaborative whiteboard with one client
python whiteboard_main.py --username User1

# Start with multiple clients
python whiteboard_main.py --clients 2

# Start standalone whiteboard (no collaboration)
python whiteboard_main.py --standalone
```

You can also start each component individually:

```bash
# Start the collaboration server
python whiteboard_server.py [--host HOST] [--port PORT]

# Start a collaborative client
python whiteboard_client_collab.py [--canvas-host HOST] [--canvas-port PORT] [--server-host HOST] [--server-port PORT] [--username NAME]

# Start a standalone client
python whiteboard_client.py [--host HOST] [--port PORT] [--username NAME]
```

Controls:
- Mouse: Draw with selected tool
- +/-: Increase/decrease tool size
- c: Clear whiteboard

### Code Editor

A Python code editor with execution visualization and debugging.

```bash
python code_editor.py [--port PORT]
```

Options:
- `--port PORT`: Port for canvas server (default: 5005)

Example:
```bash
python code_editor.py --port 5005
```

You can also start the client directly:

```bash
python code_editor_client.py [--host HOST] [--port PORT]
```

Features:
- Code syntax highlighting
- Real-time execution visualization
- Variable tracking
- Breakpoints
- Step-by-step debugging

## Using the Main Entry Screen (Optional)

For a more integrated experience, you can use the main entry screen that provides a unified interface to launch all applications.

```bash
python app.py [--width WIDTH] [--height HEIGHT]
```

Options:
- `--width WIDTH`: Window width (default: 800)
- `--height HEIGHT`: Window height (default: 600)

Example:
```bash
python app.py --width 1024 --height 768
```

The launcher provides these features:
1. Start/stop socket_canvas.py automatically
2. Launch any application with a single click
3. Monitor running processes
4. Stop applications when done

To use:
1. Start the launcher
2. Browse applications by category
3. Click "Launch" on the application you want to run
4. Monitor running applications in the "Active Processes" section
5. Stop or remove processes as needed

This provides a convenient way to manage all the components of the project without dealing with multiple terminal windows.
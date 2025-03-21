# Collaborative Whiteboard

A real-time collaborative drawing application built using the socket canvas API.

## Features

- Real-time collaborative drawing with multiple users
- See other users' cursors and activities in real-time
- Multiple drawing tools: pen, line, rectangle, eraser
- Color selection palette
- Tool size adjustment
- Shared whiteboard state across all clients
- User identification with unique colors

## Project Structure

```
whiteboard/
│
├── socket_canvas.py           # Provided canvas API for drawing
│
├── whiteboard_client.py       # Standalone whiteboard client (non-collaborative)
│
├── whiteboard_server.py       # Collaboration server to sync client state
│
└── whiteboard_client_collab.py  # Client that connects to both canvas and server
```

## Architecture

This project uses a client-server architecture with two types of connections:

1. **Canvas Connection**: Each client connects to a Tkinter canvas via socket to display the whiteboard
2. **Server Connection**: All clients connect to a central server that synchronizes drawing actions and cursor positions

The architecture allows multiple users to collaborate on the same whiteboard in real-time, with each user seeing what others are drawing.

## Setup and Running

### Prerequisites
- Python 3.x
- Tkinter (included with most Python installations)

### Step 1: Start the Socket Canvas
First, run the socket canvas API:
```bash
python socket_canvas.py
```
This will start the Tkinter canvas server on port 5005.

### Step 2: Start the Collaboration Server
Next, in a separate terminal, run the collaboration server:
```bash
python whiteboard_server.py
```
This will start the server on port 5006 that manages communication between clients.

### Step 3: Start Clients
Finally, in one or more additional terminals, run the collaborative whiteboard client:
```bash
python whiteboard_client_collab.py --username YourName
```

For a standalone experience (no collaboration), you can use:
```bash
python whiteboard_main.py
```

## Usage

### Drawing Tools
- **Pen**: Free-form drawing
- **Line**: Draw straight lines
- **Rectangle**: Draw rectangles by clicking and dragging
- **Eraser**: Erase parts of the drawing
- **Clear**: Clear the entire whiteboard

### Controls
- Click on a tool in the toolbar to select it
- Click on a color to select it
- Use the '+' and '-' keys to adjust tool size
- Press 'c' to clear the whiteboard
- Click and drag to draw with the selected tool

### Collaboration
- Your cursor position is visible to other users
- Other users' cursors are displayed with their username
- All drawing actions are synchronized in real-time
- The whiteboard state is shared among all connected clients

## Technical Implementation

The collaborative whiteboard implementation consists of:

1. **Drawing Primitives**: Lines, points, and rectangles drawn using the socket canvas API
2. **State Management**: Tracking all drawing objects and synchronizing them across clients
3. **Event Handling**: Processing mouse and keyboard events to create drawings
4. **Networking**: Socket-based communication for canvas display and client synchronization
5. **UI Components**: Toolbar, color palette, and status bar for user interaction

The drawing objects are stored as serializable data structures that can be transmitted between clients via the server.

## Future Enhancements

- Text tool implementation
- Circle/ellipse drawing
- Undo/redo functionality
- Saving/loading whiteboards
- User authentication
- Private collaboration rooms
- More drawing tools (spray, brush, shapes)
- Layer support

## Troubleshooting

If you encounter connection issues:
1. Ensure the socket_canvas.py is running first
2. Then start the whiteboard_server.py
3. Finally, run the collaborative_whiteboard_client.py
4. Check if ports 5005 and 5006 are available on your system
5. Verify all components are run with Python 3.x
# Canvas Text Editor

A feature-rich text editor built with Python using the provided socket canvas API.

## Features

- Basic text editing functionality (insert, delete, navigate)
- Selection with mouse and keyboard (with Shift key)
- Copy, cut, and paste operations
- Line numbers with toggling capability
- Status bar with cursor position and line count
- Color highlighting for selections and cursor line
- Keyboard shortcuts for common operations

## Prerequisites

- Python 3.x
- socket_canvas.py (provided separately)

## Running the Text Editor

1. First, start the socket canvas API:
   ```
   python socket_canvas.py
   ```

2. Then, in a separate terminal, run the text editor:
   ```
   python main.py
   ```

## Keyboard Shortcuts

- **Ctrl+C**: Copy selected text
- **Ctrl+X**: Cut selected text
- **Ctrl+V**: Paste from clipboard
- **Ctrl+A**: Select all text
- **Ctrl+N**: New file (clears the editor)
- **Ctrl+L**: Toggle line numbers
- **Ctrl+H**: Toggle command legend/help
- **Tab**: Insert 4 spaces
- **Home**: Move to beginning of line
- **End**: Move to end of line
- **Arrow keys**: Navigate through text
- **Shift + Arrow keys**: Select text while navigating
- **Escape**: Clear selection

## Mouse Operations

- **Click**: Position cursor
- **Click and drag**: Select text
- **Click in line number area**: Select entire line

## Project Structure

- `main.py`: Main entry point and editor implementation
  - `TextEditorClient`: Handles socket communication
  - `TextEditor`: Handles text editing
  - `TextBuffer`: Manages text content and cursor
  - `Renderer`: Renders text and UI to the canvas
  - `TextEditor`: Main controller coordinating all components

## Implementation Details

The editor is built on a client-server architecture where:

1. The socket_canvas.py provides a Tkinter canvas accessible via TCP
2. The main.py connects to this canvas and uses it as a display

All drawing is done via the three available commands:
- Drawing rectangles for UI elements and cursor
- Drawing text for content display
- Clearing the screen for refreshes

The editor leverages event-driven programming to handle user input from both keyboard and mouse.

## Future Enhancements

- Syntax highlighting for common programming languages
- Undo/redo functionality
- Find and replace
- File open/save operations
- Multiple tabs or windows
- Code folding

## Troubleshooting

If you encounter issues connecting to the canvas:
1. Ensure the socket_canvas.py is running first
2. Check that port 5005 is not blocked or in use
3. Verify that both scripts are run with Python 3.x
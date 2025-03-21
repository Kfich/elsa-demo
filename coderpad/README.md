# Live Code Editor with Execution Visualization

A Python code editor that visualizes code execution in real-time, allowing you to see variables, the call stack, and execution flow as your code runs.

## Features

- **Code Editor with Syntax Highlighting**: Write Python code with proper syntax coloring
- **Real-Time Execution Visualization**: See your code execute line by line
- **Variable Inspector**: Watch variables change as your code runs
- **Call Stack Display**: View the function call stack during execution
- **Breakpoints**: Set breakpoints by clicking on line numbers
- **Execution Control**: Run, step, reset, and adjust execution speed
- **Console Output**: See your program's output in a dedicated console area

## Project Structure

```
code-editor/
│
├── socket_canvas.py          # Provided canvas API for rendering
│
├── code_editor_client.py     # The main code editor implementation
│
└── run_code_editor.py        # Helper script to run all components
```

## Architecture

This project uses a client-server architecture:

1. **Canvas Server (socket_canvas.py)**: Provides the drawing surface and handles user input
2. **Code Editor Client (code_editor_client.py)**: Implements the editor, execution visualization, and UI

The editor uses a simplified AST (Abstract Syntax Tree) parser to understand and visualize Python code execution.

## Setup and Running

### Prerequisites
- Python 3.x
- Tkinter (included with most Python installations)

### Running with the Helper Script

The easiest way to start the Live Code Editor is with the provided helper script:

```bash
python run_code_editor.py
```

### Starting Components Manually

You can also start each component individually:

1. First, start the socket canvas:
```bash
python socket_canvas.py
```

2. Then, start the code editor client:
```bash
python code_editor_client.py
```

## How to Use

### Writing Code
- Type Python code in the editor area
- The editor supports standard text editing operations:
  - Arrow keys to navigate
  - Home/End to move to start/end of line
  - Enter for new lines (with auto-indentation)
  - Tab to insert spaces
  - Backspace/Delete to remove characters

### Running Code
- Click the "Run" button to execute the code with visualization
- The current line being executed is highlighted
- Variables and their values are displayed in real-time
- Function calls are shown in the call stack
- Output appears in the console area

### Execution Control
- "Step" button: Execute one step at a time
- "Reset" button: Reset execution to start
- "Faster"/"Slower" buttons: Adjust execution speed
- Click on line numbers to toggle breakpoints (execution will pause at breakpoints)

### Visual Feedback
- Line numbers show where you are in the code
- Syntax highlighting makes the code more readable
- Current line is highlighted during execution
- Variables panel shows the current state
- Call stack shows active function calls
- Console shows program output

## Technical Details

### Code Execution Visualization
The editor visualizes code execution by:
1. Parsing the code into an Abstract Syntax Tree (AST)
2. Flattening the AST into a sequence of instructions
3. Executing each instruction while tracking variables and the call stack
4. Updating the visualization after each step

### Limitations
- The execution visualization is simplified and doesn't support all Python features
- Complex expressions and some language features may not visualize correctly
- The editor doesn't handle imports or external libraries
- Error handling is basic

## Example Code

The editor comes with a simple example program to demonstrate its features:

```python
def hello_world():
    print('Hello, world!')
    x = 5
    y = 10
    result = x + y
    print(f'The sum is {result}')

hello_world()
```

Try modifying this code or writing your own Python programs to explore the visualization features!

## Future Enhancements

- Support for more Python language features
- Better error handling and debugging tools
- Memory visualization with object diagrams
- Loop and recursion visualization
- Support for importing external libraries
- Save/load functionality for code files
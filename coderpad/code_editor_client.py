#!/usr/bin/env python3
import socket
import threading
import time
import argparse
import re

class CodeEditorClient:
    def __init__(self, host='localhost', port=5005):
        # Canvas connection
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        
        # Event handlers
        self.event_handlers = {
            'resize': [],
            'mousedown': [],
            'mouseup': [],
            'mousemove': [],
            'keydown': [],
            'keyup': []
        }
        
        # Canvas dimensions
        self.canvas_width = 1200
        self.canvas_height = 800
        
        # Editor dimensions and position
        self.editor_x = 20
        self.editor_y = 60
        self.editor_width = 600
        self.editor_height = 500
        self.line_height = 18
        self.char_width = 8
        self.line_number_width = 40
        
        # Execution visualization area
        self.visualization_x = 640
        self.visualization_y = 60
        self.visualization_width = 540
        self.visualization_height = 500
        
        # Console output area
        self.console_x = 20
        self.console_y = 580
        self.console_width = 1160
        self.console_height = 200
        self.console_output = []
        self.max_console_lines = 50
        
        # Text state
        self.lines = ["def hello_world():", "    print('Hello, world!')", "    x = 5", "    y = 10", "    result = x + y", "    print(f'The sum is {result}')", "", "hello_world()"]
        self.cursor_row = 0
        self.cursor_col = 0
        self.scroll_offset = 0
        self.selection_start = None
        self.selection_end = None
        
        # Execution state
        self.execution_state = {
            'running': False,
            'current_line': None,
            'variables': {},
            'call_stack': [],
            'output': [],
            'step': 0,
            'breakpoints': set(),
            'execution_speed': 0.5,  # seconds between steps
        }
        
        # UI state
        self.hover_line = None
        self.hover_button = None
        
        # Syntax highlighting - defined by token type
        self.colors = {
            'background': '#1E1E1E',
            'text': '#D4D4D4',
            'line_numbers': '#858585',
            'current_line': '#264F78',
            'selection': '#264F7880',
            'comment': '#6A9955',
            'string': '#CE9178',
            'number': '#B5CEA8',
            'keyword': '#569CD6',
            'function': '#DCDCAA',
            'class': '#4EC9B0',
            'operator': '#D4D4D4',
            'variable': '#9CDCFE',
            'parameter': '#9CDCFE',
            'punctuation': '#D4D4D4',
            'highlight': '#FFFF0050',
            'button': '#0E639C',
            'button_hover': '#1177BB',
            'button_text': '#FFFFFF',
            'console_bg': '#1E1E1E',
            'console_text': '#CCCCCC',
            'console_error': '#F14C4C',
            'breakpoint': '#E51400',
            'header_bg': '#007ACC',
            'header_text': '#FFFFFF',
            'cursor': '#AEAFAD',
            'visualization_bg': '#252526',
            'border': '#454545',
            'active_line': '#2A3450',
        }
        
        # Python keywords for syntax highlighting
        self.python_keywords = [
            'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await', 'break', 
            'class', 'continue', 'def', 'del', 'elif', 'else', 'except', 'finally', 
            'for', 'from', 'global', 'if', 'import', 'in', 'is', 'lambda', 'nonlocal', 
            'not', 'or', 'pass', 'raise', 'return', 'try', 'while', 'with', 'yield'
        ]
        
        # Button definitions
        self.buttons = {
            'run': {'x': 20, 'y': 20, 'width': 80, 'height': 30, 'text': 'Run', 'action': self.run_code},
            'step': {'x': 110, 'y': 20, 'width': 80, 'height': 30, 'text': 'Step', 'action': self.step_code},
            'reset': {'x': 200, 'y': 20, 'width': 80, 'height': 30, 'text': 'Reset', 'action': self.reset_execution},
            'faster': {'x': 290, 'y': 20, 'width': 80, 'height': 30, 'text': 'Faster', 'action': self.increase_speed},
            'slower': {'x': 380, 'y': 20, 'width': 80, 'height': 30, 'text': 'Slower', 'action': self.decrease_speed},
        }
        
        # Regex patterns for syntax highlighting
        self.patterns = {
            'keywords': r'\b(' + '|'.join(self.python_keywords) + r')\b',
            'functions': r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
            'classes': r'\bclass\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            'strings': r'("[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\')',
            'comments': r'(#.*$)',
            'numbers': r'\b(\d+\.?\d*)\b',
        }
        
        # Execution thread
        self.execution_thread = None
    
    def connect(self):
        """Connect to the canvas"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            
            # Start listening for events
            self.listen_thread = threading.Thread(target=self.listen_for_events)
            self.listen_thread.daemon = True
            self.listen_thread.start()
            
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the canvas"""
        if self.connected:
            self.connected = False
            try:
                self.socket.close()
            except:
                pass
    
    def send_command(self, command):
        """Send a command to the canvas"""
        if not self.connected:
            return False
        
        if not command.endswith('\n'):
            command += '\n'
        
        try:
            self.socket.sendall(command.encode('utf-8'))
            return True
        except Exception as e:
            print(f"Send error: {e}")
            self.connected = False
            return False
    
    def listen_for_events(self):
        """Listen for events from the canvas"""
        buffer = ""
        
        while self.connected:
            try:
                data = self.socket.recv(1024).decode('utf-8')
                if not data:
                    self.connected = False
                    break
                
                buffer += data
                
                # Process complete events (ones that end with newline)
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    self.process_event(line)
                    
            except Exception as e:
                print(f"Receive error: {e}")
                self.connected = False
                break
    
    def process_event(self, event_str):
        """Process events from the canvas"""
        parts = event_str.split(',')
        if len(parts) >= 1:
            event_type = parts[0]
            
            if event_type in self.event_handlers:
                for handler in self.event_handlers[event_type]:
                    handler(parts)
    
    def on(self, event_type, handler):
        """Register an event handler"""
        if event_type in self.event_handlers:
            self.event_handlers[event_type].append(handler)
    
    # Canvas API commands
    def draw_rect(self, x, y, width, height, color):
        """Draw a rectangle on the canvas"""
        return self.send_command(f"rect,{x},{y},{width},{height},{color}")
    
    def draw_text(self, x, y, color, text):
        """Draw text on the canvas"""
        return self.send_command(f"text,{x},{y},{color},{text}")
    
    def clear_screen(self):
        """Clear the canvas"""
        return self.send_command("clear")
    
    def handle_resize(self, event_parts):
        """Handle resize event"""
        if len(event_parts) >= 3:
            width = int(event_parts[1])
            height = int(event_parts[2])
            
            # Adjust UI dimensions based on new size
            self.canvas_width = width
            self.canvas_height = height
            
            # Adjust editor size
            self.editor_width = min(600, int(width * 0.5) - 40)
            self.visualization_x = self.editor_x + self.editor_width + 20
            self.visualization_width = width - self.visualization_x - 20
            
            # Adjust console position
            self.console_y = height - self.console_height - 20
            self.console_width = width - 40
            
            # Adjust editor and visualization height
            self.editor_height = self.console_y - self.editor_y - 20
            self.visualization_height = self.editor_height
            
            self.render()
    
    def handle_mousedown(self, event_parts):
        """Handle mouse down event"""
        if len(event_parts) >= 3:
            x = int(event_parts[1])
            y = int(event_parts[2])
            
            # Check for button clicks
            for button_id, button in self.buttons.items():
                if (button['x'] <= x <= button['x'] + button['width'] and
                    button['y'] <= y <= button['y'] + button['height']):
                    button['action']()
                    return
            
            # Check if click is in the editor area
            if (self.editor_x <= x <= self.editor_x + self.editor_width and
                self.editor_y <= y <= self.editor_y + self.editor_height):
                
                # Check if click is in the line numbers area (for breakpoints)
                if x < self.editor_x + self.line_number_width:
                    line_idx = (y - self.editor_y) // self.line_height + self.scroll_offset
                    if 0 <= line_idx < len(self.lines):
                        if line_idx in self.execution_state['breakpoints']:
                            self.execution_state['breakpoints'].remove(line_idx)
                        else:
                            self.execution_state['breakpoints'].add(line_idx)
                        self.render()
                    return
                
                # Handle click in the text area
                text_x = x - (self.editor_x + self.line_number_width)
                text_y = y - self.editor_y
                
                # Calculate row and column
                row = text_y // self.line_height + self.scroll_offset
                if row >= len(self.lines):
                    row = len(self.lines) - 1
                
                col = text_x // self.char_width
                line_length = len(self.lines[row]) if row < len(self.lines) else 0
                if col > line_length:
                    col = line_length
                
                # Update cursor position
                self.cursor_row = max(0, min(row, len(self.lines) - 1))
                self.cursor_col = max(0, min(col, line_length))
                
                # Clear selection
                self.selection_start = None
                self.selection_end = None
                
                self.render()
    
    def handle_mousemove(self, event_parts):
        """Handle mouse move event"""
        if len(event_parts) >= 3:
            x = int(event_parts[1])
            y = int(event_parts[2])
            
            # Check for hover over buttons
            old_hover_button = self.hover_button
            self.hover_button = None
            
            for button_id, button in self.buttons.items():
                if (button['x'] <= x <= button['x'] + button['width'] and
                    button['y'] <= y <= button['y'] + button['height']):
                    self.hover_button = button_id
                    break
            
            # Check for hover over line numbers (for breakpoints)
            old_hover_line = self.hover_line
            self.hover_line = None
            
            if (self.editor_x <= x <= self.editor_x + self.line_number_width and
                self.editor_y <= y <= self.editor_y + self.editor_height):
                line_idx = (y - self.editor_y) // self.line_height + self.scroll_offset
                if 0 <= line_idx < len(self.lines):
                    self.hover_line = line_idx
            
            # Render only if hover state changed
            if old_hover_button != self.hover_button or old_hover_line != self.hover_line:
                self.render()
    
    def handle_keydown(self, event_parts):
        """Handle key down event"""
        if len(event_parts) >= 2:
            key = event_parts[1]
            
            if key == "BackSpace":
                self.delete_char_before_cursor()
            elif key == "Delete":
                self.delete_char_at_cursor()
            elif key == "Left":
                self.move_cursor_left()
            elif key == "Right":
                self.move_cursor_right()
            elif key == "Up":
                self.move_cursor_up()
            elif key == "Down":
                self.move_cursor_down()
            elif key == "Home":
                self.move_cursor_to_line_start()
            elif key == "End":
                self.move_cursor_to_line_end()
            elif key == "Return":
                self.insert_newline()
            elif key == "Tab":
                self.insert_tab()
            elif len(key) == 1:  # Regular character
                self.insert_char(key)
            
            self.render()
    
    def insert_char(self, char):
        """Insert character at cursor position"""
        if self.cursor_row < len(self.lines):
            line = self.lines[self.cursor_row]
            new_line = line[:self.cursor_col] + char + line[self.cursor_col:]
            self.lines[self.cursor_row] = new_line
            self.cursor_col += 1
    
    def delete_char_before_cursor(self):
        """Delete character before cursor"""
        if self.cursor_col > 0:
            # Delete character in current line
            line = self.lines[self.cursor_row]
            new_line = line[:self.cursor_col - 1] + line[self.cursor_col:]
            self.lines[self.cursor_row] = new_line
            self.cursor_col -= 1
        elif self.cursor_row > 0:
            # Join with previous line
            prev_line = self.lines[self.cursor_row - 1]
            curr_line = self.lines[self.cursor_row]
            self.cursor_col = len(prev_line)
            self.lines[self.cursor_row - 1] = prev_line + curr_line
            self.lines.pop(self.cursor_row)
            self.cursor_row -= 1
    
    def delete_char_at_cursor(self):
        """Delete character at cursor position"""
        if self.cursor_col < len(self.lines[self.cursor_row]):
            # Delete character in current line
            line = self.lines[self.cursor_row]
            new_line = line[:self.cursor_col] + line[self.cursor_col + 1:]
            self.lines[self.cursor_row] = new_line
        elif self.cursor_row < len(self.lines) - 1:
            # Join with next line
            curr_line = self.lines[self.cursor_row]
            next_line = self.lines[self.cursor_row + 1]
            self.lines[self.cursor_row] = curr_line + next_line
            self.lines.pop(self.cursor_row + 1)
    
    def insert_newline(self):
        """Insert a new line at cursor position"""
        curr_line = self.lines[self.cursor_row]
        line_before = curr_line[:self.cursor_col]
        line_after = curr_line[self.cursor_col:]
        
        # Calculate indentation for the new line
        indentation = ""
        for char in line_before:
            if char == ' ' or char == '\t':
                indentation += char
            else:
                break
        
        # If the previous line ends with a colon, add additional indentation
        if line_before.rstrip().endswith(':'):
            indentation += '    '
        
        # Update lines
        self.lines[self.cursor_row] = line_before
        self.lines.insert(self.cursor_row + 1, indentation + line_after)
        
        # Move cursor to new line
        self.cursor_row += 1
        self.cursor_col = len(indentation)
    
    def insert_tab(self):
        """Insert a tab (4 spaces) at cursor position"""
        for _ in range(4):
            self.insert_char(' ')
    
    def move_cursor_left(self):
        """Move cursor left"""
        if self.cursor_col > 0:
            self.cursor_col -= 1
        elif self.cursor_row > 0:
            self.cursor_row -= 1
            self.cursor_col = len(self.lines[self.cursor_row])
    
    def move_cursor_right(self):
        """Move cursor right"""
        if self.cursor_col < len(self.lines[self.cursor_row]):
            self.cursor_col += 1
        elif self.cursor_row < len(self.lines) - 1:
            self.cursor_row += 1
            self.cursor_col = 0
    
    def move_cursor_up(self):
        """Move cursor up"""
        if self.cursor_row > 0:
            self.cursor_row -= 1
            # Ensure cursor column is valid for the new line
            self.cursor_col = min(self.cursor_col, len(self.lines[self.cursor_row]))
            
            # Scroll if needed
            if self.cursor_row < self.scroll_offset:
                self.scroll_offset = self.cursor_row
    
    def move_cursor_down(self):
        """Move cursor down"""
        if self.cursor_row < len(self.lines) - 1:
            self.cursor_row += 1
            # Ensure cursor column is valid for the new line
            self.cursor_col = min(self.cursor_col, len(self.lines[self.cursor_row]))
            
            # Scroll if needed
            visible_lines = self.editor_height // self.line_height
            if self.cursor_row >= self.scroll_offset + visible_lines:
                self.scroll_offset = self.cursor_row - visible_lines + 1
    
    def move_cursor_to_line_start(self):
        """Move cursor to start of line"""
        # Find first non-whitespace character
        line = self.lines[self.cursor_row]
        pos = 0
        for char in line:
            if char != ' ' and char != '\t':
                break
            pos += 1
        
        # If already at first non-whitespace char, go to beginning of line
        if self.cursor_col == pos and pos > 0:
            self.cursor_col = 0
        else:
            self.cursor_col = pos
    
    def move_cursor_to_line_end(self):
        """Move cursor to end of line"""
        self.cursor_col = len(self.lines[self.cursor_row])
    
    def run_code(self):
        """Run the code with visualization"""
        if self.execution_state['running']:
            return
        
        # Reset execution state
        self.reset_execution()
        
        # Start execution thread
        self.execution_state['running'] = True
        if self.execution_thread is not None and self.execution_thread.is_alive():
            return
        
        self.execution_thread = threading.Thread(target=self.execute_code)
        self.execution_thread.daemon = True
        self.execution_thread.start()
    
    def step_code(self):
        """Step through code execution"""
        if not self.execution_state['running']:
            self.reset_execution()
            self.execution_state['running'] = True
        
        self.run_next_step()
    
    def reset_execution(self):
        """Reset execution state"""
        self.execution_state = {
            'running': False,
            'current_line': None,
            'variables': {},
            'call_stack': [],
            'output': [],
            'step': 0,
            'breakpoints': self.execution_state['breakpoints'].copy(),
            'execution_speed': self.execution_state['execution_speed'],
        }
        self.console_output = []
        self.render()
    
    def increase_speed(self):
        """Increase execution speed"""
        self.execution_state['execution_speed'] = max(0.1, self.execution_state['execution_speed'] / 1.5)
        self.render()
    
    def decrease_speed(self):
        """Decrease execution speed"""
        self.execution_state['execution_speed'] = min(2.0, self.execution_state['execution_speed'] * 1.5)
        self.render()
    
    def execute_code(self):
        """Execute the code with visualization"""
        try:
            # Join all lines to get the full code
            code = '\n'.join(self.lines)
            
            # Parse the code into an AST for execution visualization
            # Note: This is a simplified execution model for visualization
            import ast
            tree = ast.parse(code)
            
            # Convert to a flat list of instructions
            instructions = self.flatten_ast(tree)
            
            # Execute each instruction
            for i, inst in enumerate(instructions):
                if not self.execution_state['running']:
                    break
                
                # Update execution state
                self.execution_state['step'] = i + 1
                self.execution_state['current_line'] = inst['lineno'] - 1  # Convert to 0-based index
                
                # Render the current state
                self.render()
                
                # Check for breakpoints
                if self.execution_state['current_line'] in self.execution_state['breakpoints']:
                    self.execution_state['running'] = False
                    self.render()
                    break
                
                # Run the instruction
                self.run_instruction(inst)
                
                # Wait for the next step
                time.sleep(self.execution_state['execution_speed'])
            
            # End of execution
            self.execution_state['running'] = False
            self.execution_state['current_line'] = None
            self.render()
            
        except Exception as e:
            # Handle execution error
            self.console_output.append(f"Error: {str(e)}")
            self.execution_state['running'] = False
            self.render()
    
    def flatten_ast(self, tree):
        """Convert AST to a flat list of instructions for visualization"""
        instructions = []
        
        for node in ast.walk(tree):
            if hasattr(node, 'lineno'):
                instruction = {
                    'type': type(node).__name__,
                    'lineno': node.lineno,
                    'node': node
                }
                instructions.append(instruction)
        
        # Sort by line number
        instructions.sort(key=lambda x: x['lineno'])
        return instructions
    
    def run_instruction(self, instruction):
        """Run a single instruction"""
        node = instruction['node']
        node_type = instruction['type']
        
        # Simplified execution model for visualization
        try:
            if node_type == 'Call':
                if isinstance(node.func, ast.Name) and node.func.id == 'print':
                    # Handle print function
                    args = []
                    for arg in node.args:
                        if isinstance(arg, ast.Constant):
                            args.append(str(arg.value))
                        elif isinstance(arg, ast.Name):
                            var_name = arg.id
                            if var_name in self.execution_state['variables']:
                                args.append(str(self.execution_state['variables'][var_name]))
                            else:
                                args.append(f"{var_name} (undefined)")
                        elif isinstance(arg, ast.JoinedStr):  # Handle f-strings
                            result = ""
                            for value in arg.values:
                                if isinstance(value, ast.Constant):
                                    result += str(value.value)
                                elif isinstance(value, ast.FormattedValue):
                                    if isinstance(value.value, ast.Name):
                                        var_name = value.value.id
                                        if var_name in self.execution_state['variables']:
                                            result += str(self.execution_state['variables'][var_name])
                                        else:
                                            result += f"{var_name} (undefined)"
                            args.append(result)
                        else:
                            args.append(str(arg))
                    
                    # Add output to console
                    output = " ".join(args)
                    self.console_output.append(output)
                    if len(self.console_output) > self.max_console_lines:
                        self.console_output.pop(0)
                
                # Add function to call stack for visualization
                func_name = ""
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr
                
                self.execution_state['call_stack'].append(func_name)
                
            elif node_type == 'Assign':
                # Handle variable assignment
                if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                    var_name = node.targets[0].id
                    
                    # Evaluate the value (simplified)
                    value = None
                    if isinstance(node.value, ast.Constant):
                        value = node.value.value
                    elif isinstance(node.value, ast.Name):
                        other_var = node.value.id
                        if other_var in self.execution_state['variables']:
                            value = self.execution_state['variables'][other_var]
                    elif isinstance(node.value, ast.BinOp):
                        # Handle simple binary operations like x + y
                        left = right = None
                        
                        # Get left operand
                        if isinstance(node.value.left, ast.Constant):
                            left = node.value.left.value
                        elif isinstance(node.value.left, ast.Name):
                            var_name = node.value.left.id
                            if var_name in self.execution_state['variables']:
                                left = self.execution_state['variables'][var_name]
                        
                        # Get right operand
                        if isinstance(node.value.right, ast.Constant):
                            right = node.value.right.value
                        elif isinstance(node.value.right, ast.Name):
                            var_name = node.value.right.id
                            if var_name in self.execution_state['variables']:
                                right = self.execution_state['variables'][var_name]
                        
                        # Perform operation
                        if left is not None and right is not None:
                            if isinstance(node.value.op, ast.Add):
                                value = left + right
                            elif isinstance(node.value.op, ast.Sub):
                                value = left - right
                            elif isinstance(node.value.op, ast.Mult):
                                value = left * right
                            elif isinstance(node.value.op, ast.Div):
                                value = left / right
                    
                    # Store the variable
                    if value is not None:
                        self.execution_state['variables'][var_name] = value
        
        except Exception as e:
            self.console_output.append(f"Error executing line {instruction['lineno']}: {str(e)}")
    
    def run_next_step(self):
        """Run the next step of code execution"""
        # TODO: Implement step-by-step execution
        pass
    
    def apply_syntax_highlighting(self, line):
        """Apply syntax highlighting to a line of code"""
        # This is a simplified syntax highlighting implementation
        # Start with the default text color
        line_parts = [(line, self.colors['text'])]
        
        # Apply highlighting for each pattern
        for token_type, pattern in self.patterns.items():
            new_parts = []
            for text, color in line_parts:
                if color != self.colors['text']:
                    # Skip already highlighted text
                    new_parts.append((text, color))
                    continue
                
                # Find matches for this pattern
                matches = list(re.finditer(pattern, text))
                if not matches:
                    new_parts.append((text, color))
                    continue
                
                # Split text by matches
                last_end = 0
                for match in matches:
                    # Add text before match
                    if match.start() > last_end:
                        new_parts.append((text[last_end:match.start()], self.colors['text']))
                    
                    # Add the match with appropriate color
                    match_text = match.group(0)
                    if token_type == 'keywords':
                        new_parts.append((match_text, self.colors['keyword']))
                    elif token_type == 'functions':
                        function_name = match.group(1)
                        prefix = match_text[:match_text.index(function_name)]
                        suffix = match_text[match_text.index(function_name) + len(function_name):]
                        new_parts.append((prefix, self.colors['text']))
                        new_parts.append((function_name, self.colors['function']))
                        new_parts.append((suffix, self.colors['text']))
                    elif token_type == 'classes':
                        class_name = match.group(1)
                        prefix = match_text[:match_text.index(class_name)]
                        suffix = match_text[match_text.index(class_name) + len(class_name):]
                        new_parts.append((prefix, self.colors['text']))
                        new_parts.append((class_name, self.colors['class']))
                        new_parts.append((suffix, self.colors['text']))
                    elif token_type == 'strings':
                        new_parts.append((match_text, self.colors['string']))
                    elif token_type == 'comments':
                        new_parts.append((match_text, self.colors['comment']))
                    elif token_type == 'numbers':
                        new_parts.append((match_text, self.colors['number']))
                    
                    last_end = match.end()
                
                # Add text after the last match
                if last_end < len(text):
                    new_parts.append((text[last_end:], self.colors['text']))
            
            line_parts = new_parts
        
        return line_parts
    
    def render(self):
        """Render the code editor interface"""
        self.clear_screen()
        
        # Draw background
        self.draw_rect(0, 0, self.canvas_width, self.canvas_height, self.colors['background'])
        
        # Draw header
        self.draw_rect(0, 0, self.canvas_width, 50, self.colors['header_bg'])
        self.draw_text(20, 15, self.colors['header_text'], "Live Code Editor with Execution Visualization")
        
        # Draw buttons
        for button_id, button in self.buttons.items():
            button_color = self.colors['button_hover'] if self.hover_button == button_id else self.colors['button']
            self.draw_rect(button['x'], button['y'], button['width'], button['height'], button_color)
            
            # Center text in button
            text_width = len(button['text']) * self.char_width
            text_x = button['x'] + (button['width'] - text_width) // 2
            text_y = button['y'] + (button['height'] - self.line_height) // 2 + 12
            self.draw_text(text_x, text_y, self.colors['button_text'], button['text'])
        
        # Draw execution speed indicator
        speed_text = f"Speed: {1.0 / self.execution_state['execution_speed']:.1f}x"
        self.draw_text(480, 35, self.colors['text'], speed_text)
        
        # Draw editor area
        self.draw_rect(self.editor_x, self.editor_y, self.editor_width, self.editor_height, self.colors['background'])
        self.draw_rect(self.editor_x, self.editor_y, self.editor_width, self.editor_height, self.colors['border'])
        
        # Draw line numbers and code
        visible_lines = min(self.editor_height // self.line_height, len(self.lines) - self.scroll_offset)
        for i in range(visible_lines):
            line_idx = i + self.scroll_offset
            y = self.editor_y + i * self.line_height
            
            # Draw current line highlight
            if line_idx == self.execution_state['current_line']:
                self.draw_rect(self.editor_x, y, self.editor_width, self.line_height, self.colors['active_line'])
            elif line_idx == self.cursor_row:
                self.draw_rect(self.editor_x, y, self.editor_width, self.line_height, self.colors['current_line'])
            
            # Draw line number
            line_number_color = self.colors['breakpoint'] if line_idx in self.execution_state['breakpoints'] else self.colors['line_numbers']
            if self.hover_line == line_idx:
                self.draw_rect(self.editor_x, y, self.line_number_width, self.line_height, "#44444480")
            self.draw_text(self.editor_x + 5, y + 12, line_number_color, str(line_idx + 1).rjust(3))
            
            # Draw line text with syntax highlighting
            line = self.lines[line_idx]
            line_parts = self.apply_syntax_highlighting(line)
            
            # Draw each part with its color
            x_offset = 0
            for text_part, color in line_parts:
                self.draw_text(self.editor_x + self.line_number_width + x_offset, y + 12, color, text_part)
                x_offset += len(text_part) * self.char_width
        
        # Draw cursor
        if self.cursor_row >= self.scroll_offset and self.cursor_row < self.scroll_offset + visible_lines:
            cursor_y = self.editor_y + (self.cursor_row - self.scroll_offset) * self.line_height
            cursor_x = self.editor_x + self.line_number_width + self.cursor_col * self.char_width
            self.draw_rect(cursor_x, cursor_y, 2, self.line_height, self.colors['cursor'])
        
        # Draw visualization area
        self.draw_rect(self.visualization_x, self.visualization_y, self.visualization_width, self.visualization_height, self.colors['visualization_bg'])
        self.draw_rect(self.visualization_x, self.visualization_y, self.visualization_width, self.visualization_height, self.colors['border'])
        
        # Draw variables section
        var_title_y = self.visualization_y + 12
        self.draw_text(self.visualization_x + 10, var_title_y, self.colors['keyword'], "Variables:")
        
        var_y = var_title_y + 25
        for i, (var_name, value) in enumerate(self.execution_state['variables'].items()):
            if i >= 15:  # Limit the number of variables shown
                self.draw_text(self.visualization_x + 10, var_y, self.colors['text'], "... more variables ...")
                break
                
            self.draw_text(self.visualization_x + 20, var_y, self.colors['variable'], var_name)
            self.draw_text(self.visualization_x + 150, var_y, self.colors['text'], "=")
            
            # Format value based on type
            if isinstance(value, str):
                value_text = f'"{value}"'
                color = self.colors['string']
            elif isinstance(value, (int, float)):
                value_text = str(value)
                color = self.colors['number']
            else:
                value_text = str(value)
                color = self.colors['text']
                
            self.draw_text(self.visualization_x + 170, var_y, color, value_text)
            var_y += 20
        
        # Draw call stack section
        call_stack_y = var_y + 30
        self.draw_text(self.visualization_x + 10, call_stack_y, self.colors['keyword'], "Call Stack:")
        
        stack_y = call_stack_y + 25
        for i, func_name in enumerate(reversed(self.execution_state['call_stack'])):
            if i >= 8:  # Limit the number of stack frames shown
                break
                
            self.draw_rect(self.visualization_x + 20, stack_y - 15, self.visualization_width - 40, 20, "#444444")
            self.draw_text(self.visualization_x + 25, stack_y, self.colors['function'], func_name + "()")
            stack_y += 25
        
        # Draw execution status
        status_y = stack_y + 30
        status_text = "Status: "
        if self.execution_state['running']:
            status_text += "Running"
            status_color = self.colors['status_good']
        else:
            if self.execution_state['current_line'] is not None:
                status_text += "Paused at breakpoint"
                status_color = self.colors['status_warning']
            else:
                status_text += "Ready"
                status_color = self.colors['text']
                
        self.draw_text(self.visualization_x + 10, status_y, status_color, status_text)
        
        # Draw execution step
        if self.execution_state['step'] > 0:
            step_text = f"Step: {self.execution_state['step']}"
            self.draw_text(self.visualization_x + 200, status_y, self.colors['text'], step_text)
        
        # Draw console area
        self.draw_rect(self.console_x, self.console_y, self.console_width, self.console_height, self.colors['console_bg'])
        self.draw_rect(self.console_x, self.console_y, self.console_width, self.console_height, self.colors['border'])
        
        # Draw console title
        self.draw_text(self.console_x + 10, self.console_y + 12, self.colors['keyword'], "Console Output:")
        
        # Draw console content
        console_content_y = self.console_y + 32
        for i, line in enumerate(self.console_output):
            if i >= 8:  # Limit the number of console lines shown
                break
                
            line_color = self.colors['console_error'] if line.startswith("Error") else self.colors['console_text']
            self.draw_text(self.console_x + 15, console_content_y + i * 20, line_color, line)
            

def main():
    parser = argparse.ArgumentParser(description='Live Code Editor with Execution Visualization')
    parser.add_argument('--host', default='localhost', help='Canvas server host')
    parser.add_argument('--port', type=int, default=5005, help='Canvas server port')
    
    args = parser.parse_args()
    
    editor = CodeEditorClient(args.host, args.port)
    
    if editor.connect():
        # Register event handlers
        editor.on('resize', editor.handle_resize)
        editor.on('mousedown', editor.handle_mousedown)
        editor.on('mousemove', editor.handle_mousemove)
        editor.on('keydown', editor.handle_keydown)
        
        # Initial render
        editor.render()
        
        try:
            while True:
                time.sleep(0.1)
                
                if not editor.connected:
                    print("Connection lost. Exiting...")
                    break
        except KeyboardInterrupt:
            print("\nExiting...")
        finally:
            editor.disconnect()
    else:
        print("Failed to connect. Make sure the socket_canvas.py is running.")


if __name__ == "__main__":
    main()
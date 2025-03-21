#!/usr/bin/env python3
import socket
import threading
import time
import argparse

class WhiteboardClient:
    def __init__(self, host='localhost', port=5005, username='Anonymous'):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.username = username
        self.event_handlers = {
            'resize': [],
            'mousedown': [],
            'mouseup': [],
            'mousemove': [],
            'keydown': [],
            'keyup': []
        }
        
        # Whiteboard state
        self.canvas_width = 800
        self.canvas_height = 600
        self.drawing_objects = []  # List of shapes/lines drawn
        self.current_tool = 'pen'  # pen, line, rectangle, circle, text
        self.current_color = '#000000'  # Black
        self.tool_size = 2  # Pen/line thickness
        self.is_drawing = False
        self.start_x = 0
        self.start_y = 0
        self.current_x = 0
        self.current_y = 0
        self.toolbar_height = 50
        self.status_bar_height = 20
        
        # For collaborative features
        self.peers = {}  # {username: {x, y, color, last_updated}}
        self.peer_cursor_visible = True

    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            
            # Start listening for events
            self.listen_thread = threading.Thread(target=self.listen_for_events)
            self.listen_thread.daemon = True
            self.listen_thread.start()
            
            # Start cursor blinking
            self.cursor_blink_thread = threading.Thread(target=self.blink_peer_cursors)
            self.cursor_blink_thread.daemon = True
            self.cursor_blink_thread.start()
            
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    def disconnect(self):
        if self.connected:
            self.connected = False
            self.socket.close()

    def send_command(self, command):
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
        parts = event_str.split(',')
        if len(parts) >= 1:
            event_type = parts[0]
            
            if event_type in self.event_handlers:
                for handler in self.event_handlers[event_type]:
                    handler(parts)

    def on(self, event_type, handler):
        if event_type in self.event_handlers:
            self.event_handlers[event_type].append(handler)

    # Canvas API commands
    def draw_rect(self, x, y, width, height, color):
        return self.send_command(f"rect,{x},{y},{width},{height},{color}")

    def draw_text(self, x, y, color, text):
        return self.send_command(f"text,{x},{y},{color},{text}")

    def clear_screen(self):
        return self.send_command("clear")
        
    # Drawing methods
    def draw_point(self, x, y, color=None, size=None):
        if color is None:
            color = self.current_color
        if size is None:
            size = self.tool_size
            
        # Draw a square for the point
        half_size = max(1, size // 2)
        self.draw_rect(x - half_size, y - half_size, size, size, color)
        
    def draw_line(self, x1, y1, x2, y2, color=None, size=None):
        if color is None:
            color = self.current_color
        if size is None:
            size = self.tool_size
            
        # Bresenham's line algorithm
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        
        while True:
            self.draw_point(x1, y1, color, size)
            if x1 == x2 and y1 == y2:
                break
            e2 = 2 * err
            if e2 > -dy:
                if x1 == x2:
                    break
                err -= dy
                x1 += sx
            if e2 < dx:
                if y1 == y2:
                    break
                err += dx
                y1 += sy
                
    def add_drawing_object(self, obj_type, properties):
        obj = {
            'type': obj_type,
            'properties': properties,
            'username': self.username
        }
        self.drawing_objects.append(obj)
        
        # Here we would broadcast to other clients
        # For now, just redraw
        self.render()
        
    def clear_whiteboard(self):
        self.drawing_objects = []
        self.render()
        
    def blink_peer_cursors(self):
        """Thread to handle blinking peer cursors"""
        while self.connected:
            self.peer_cursor_visible = not self.peer_cursor_visible
            self.render()
            time.sleep(0.5)  # Blink every 500ms
            
    def render(self):
        """Render the whiteboard with all its contents"""
        # Clear the screen
        self.clear_screen()
        
        # Draw toolbar
        self.draw_rect(0, 0, self.canvas_width, self.toolbar_height, "#EEEEEE")
        self.draw_rect(0, self.toolbar_height-1, self.canvas_width, 1, "#AAAAAA")
        
        # Draw tool buttons
        tools = [
            ("Pen", "pen"), 
            ("Line", "line"), 
            ("Rectangle", "rectangle"),
            ("Circle", "circle"),
            ("Text", "text"),
            ("Eraser", "eraser"),
            ("Clear", "clear")
        ]
        
        button_width = 80
        for i, (label, tool) in enumerate(tools):
            button_x = 10 + i * (button_width + 5)
            button_y = 10
            button_color = "#DDDDDD" if self.current_tool != tool else "#AADDFF"
            
            # Button background
            self.draw_rect(button_x, button_y, button_width, 30, button_color)
            # Button text
            self.draw_text(button_x + 10, button_y + 8, "#000000", label)
        
        # Draw color palette
        colors = ["#000000", "#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF", "#00FFFF"]
        color_box_size = 20
        for i, color in enumerate(colors):
            color_x = 650 + i * (color_box_size + 5)
            color_y = 15
            # Color box
            self.draw_rect(color_x, color_y, color_box_size, color_box_size, color)
            # Selection indicator
            if color == self.current_color:
                self.draw_rect(color_x - 2, color_y - 2, color_box_size + 4, color_box_size + 4, "#AAAAAA")
        
        # Draw all saved objects
        for obj in self.drawing_objects:
            if obj['type'] == 'point':
                props = obj['properties']
                self.draw_point(props['x'], props['y'], props['color'], props['size'])
            elif obj['type'] == 'line':
                props = obj['properties']
                self.draw_line(props['x1'], props['y1'], props['x2'], props['y2'], props['color'], props['size'])
            # Other object types will be implemented later
        
        # Draw current object if drawing
        if self.is_drawing:
            if self.current_tool == 'pen':
                # Nothing to do here as pen drawing adds points directly to drawing_objects
                pass
            elif self.current_tool == 'line':
                self.draw_line(self.start_x, self.start_y, self.current_x, self.current_y)
            elif self.current_tool == 'rectangle':
                x = min(self.start_x, self.current_x)
                y = min(self.start_y, self.current_y)
                width = abs(self.current_x - self.start_x)
                height = abs(self.current_y - self.start_y)
                self.draw_rect(x, y, width, height, self.current_color)
                
        # Draw peer cursors
        if self.peer_cursor_visible:
            for username, info in self.peers.items():
                # Draw a colored triangle for each peer
                self.draw_rect(info['x'], info['y'], 10, 10, info['color'])
                self.draw_text(info['x'] + 15, info['y'], info['color'], username)
                
        # Draw status bar
        status_y = self.canvas_height - self.status_bar_height
        self.draw_rect(0, status_y, self.canvas_width, self.status_bar_height, "#2C3E50")
        status_text = f"Tool: {self.current_tool.capitalize()} | Color: {self.current_color} | Size: {self.tool_size}"
        self.draw_text(10, status_y + 3, "#FFFFFF", status_text)
        
        # Draw user info at right of status bar
        user_text = f"User: {self.username} | Connected"
        user_x = self.canvas_width - (len(user_text) * 8) - 10  # Approximate width of text
        self.draw_text(user_x, status_y + 3, "#FFFFFF", user_text)
        
    def handle_resize(self, event_parts):
        if len(event_parts) >= 3:
            self.canvas_width = int(event_parts[1])
            self.canvas_height = int(event_parts[2])
            self.render()
            
    def handle_mousedown(self, event_parts):
        if len(event_parts) >= 3:
            x = int(event_parts[1])
            y = int(event_parts[2])
            
            # Check if clicking in toolbar
            if y < self.toolbar_height:
                self.handle_toolbar_click(x, y)
                return
                
            # Start drawing
            self.is_drawing = True
            self.start_x = x
            self.start_y = y
            self.current_x = x
            self.current_y = y
            
            # For pen tool, add first point
            if self.current_tool == 'pen':
                self.add_drawing_object('point', {
                    'x': x,
                    'y': y,
                    'color': self.current_color,
                    'size': self.tool_size
                })
            elif self.current_tool == 'eraser':
                # Implementation of eraser - check if point is near any drawn object
                # For simplicity, we'll just add white points for now
                self.add_drawing_object('point', {
                    'x': x,
                    'y': y,
                    'color': '#FFFFFF',
                    'size': self.tool_size * 3  # Bigger eraser
                })
            
    def handle_mouseup(self, event_parts):
        if len(event_parts) >= 3 and self.is_drawing:
            x = int(event_parts[1])
            y = int(event_parts[2])
            self.current_x = x
            self.current_y = y
            
            # Finish drawing
            if self.current_tool == 'line':
                self.add_drawing_object('line', {
                    'x1': self.start_x,
                    'y1': self.start_y,
                    'x2': x,
                    'y2': y,
                    'color': self.current_color,
                    'size': self.tool_size
                })
            elif self.current_tool == 'rectangle':
                draw_x = min(self.start_x, x)
                draw_y = min(self.start_y, y)
                width = abs(x - self.start_x)
                height = abs(y - self.start_y)
                
                # Draw rectangle as 4 lines for now
                # Top line
                self.add_drawing_object('line', {
                    'x1': draw_x, 'y1': draw_y,
                    'x2': draw_x + width, 'y2': draw_y,
                    'color': self.current_color, 'size': self.tool_size
                })
                # Right line
                self.add_drawing_object('line', {
                    'x1': draw_x + width, 'y1': draw_y,
                    'x2': draw_x + width, 'y2': draw_y + height,
                    'color': self.current_color, 'size': self.tool_size
                })
                # Bottom line
                self.add_drawing_object('line', {
                    'x1': draw_x + width, 'y1': draw_y + height,
                    'x2': draw_x, 'y2': draw_y + height,
                    'color': self.current_color, 'size': self.tool_size
                })
                # Left line
                self.add_drawing_object('line', {
                    'x1': draw_x, 'y1': draw_y + height,
                    'x2': draw_x, 'y2': draw_y,
                    'color': self.current_color, 'size': self.tool_size
                })
            
            self.is_drawing = False
            self.render()
            
    def handle_mousemove(self, event_parts):
        if len(event_parts) >= 3:
            x = int(event_parts[1])
            y = int(event_parts[2])
            
            # Update current cursor position
            self.current_x = x
            self.current_y = y
            
            # If drawing with pen tool, add points
            if self.is_drawing:
                if self.current_tool == 'pen':
                    self.add_drawing_object('point', {
                        'x': x,
                        'y': y,
                        'color': self.current_color,
                        'size': self.tool_size
                    })
                elif self.current_tool == 'eraser':
                    self.add_drawing_object('point', {
                        'x': x,
                        'y': y,
                        'color': '#FFFFFF',
                        'size': self.tool_size * 3
                    })
                else:
                    # For other tools, just update display during mouse move
                    self.render()
                    
    def handle_keydown(self, event_parts):
        if len(event_parts) >= 2:
            key = event_parts[1]
            
            # Keyboard shortcuts
            if key == "+":
                self.tool_size = min(20, self.tool_size + 1)
                self.render()
            elif key == "-":
                self.tool_size = max(1, self.tool_size - 1)
                self.render()
            elif key == "c":
                self.current_tool = "clear"
                self.handle_toolbar_click(0, 0)  # Trigger clear action
                
    def handle_toolbar_click(self, x, y):
        # Check tool buttons
        tools = ["pen", "line", "rectangle", "circle", "text", "eraser", "clear"]
        button_width = 80
        
        for i, tool in enumerate(tools):
            button_x = 10 + i * (button_width + 5)
            button_y = 10
            
            if button_x <= x <= button_x + button_width and button_y <= y <= button_y + 30:
                if tool == "clear":
                    self.clear_whiteboard()
                else:
                    self.current_tool = tool
                    self.render()
                return
                
        # Check color palette
        colors = ["#000000", "#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF", "#00FFFF"]
        color_box_size = 20
        
        for i, color in enumerate(colors):
            color_x = 650 + i * (color_box_size + 5)
            color_y = 15
            
            if color_x <= x <= color_x + color_box_size and color_y <= y <= color_y + color_box_size:
                self.current_color = color
                self.render()
                return


def main():
    parser = argparse.ArgumentParser(description='Collaborative Whiteboard')
    parser.add_argument('--host', default='localhost', help='Canvas API host')
    parser.add_argument('--port', type=int, default=5005, help='Canvas API port')
    parser.add_argument('--username', default='Anonymous', help='Your username')
    
    args = parser.parse_args()
    
    print(f"Starting Whiteboard - connecting to {args.host}:{args.port}")
    print("Controls:")
    print("  Mouse: Draw with selected tool")
    print("  + / -: Increase/decrease tool size")
    print("  c: Clear whiteboard")
    
    whiteboard = WhiteboardClient(args.host, args.port, args.username)
    if whiteboard.connect():
        # Register event handlers
        whiteboard.on('resize', whiteboard.handle_resize)
        whiteboard.on('mousedown', whiteboard.handle_mousedown)
        whiteboard.on('mouseup', whiteboard.handle_mouseup)
        whiteboard.on('mousemove', whiteboard.handle_mousemove)
        whiteboard.on('keydown', whiteboard.handle_keydown)
        
        # Initial render
        whiteboard.render()
        
        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nExiting...")
            whiteboard.disconnect()
    else:
        print("Failed to connect. Is the socket_canvas.py running?")


if __name__ == "__main__":
    main()
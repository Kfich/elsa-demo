#!/usr/bin/env python3
import socket
import threading
import time
import json
import argparse
import random

class CollaborativeWhiteboardClient:
    def __init__(self, canvas_host='localhost', canvas_port=5005, 
                 server_host='localhost', server_port=5006, username=None):
        # Canvas connection (for drawing)
        self.canvas_host = canvas_host
        self.canvas_port = canvas_port
        self.canvas_socket = None
        self.canvas_connected = False
        
        # Server connection (for collaboration)
        self.server_host = server_host
        self.server_port = server_port
        self.server_socket = None
        self.server_connected = False
        
        # User information
        self.client_id = None
        self.username = username or f"User-{random.randint(1000, 9999)}"
        self.user_color = "#000000"  # Will be set by server
        
        # Event handlers for canvas
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
        self.last_cursor_update = 0

    def connect(self):
        # Connect to canvas first
        if not self.connect_to_canvas():
            return False
            
        # Then connect to collaboration server
        if not self.connect_to_server():
            self.disconnect_from_canvas()
            return False
            
        # Start cursor position update thread
        cursor_thread = threading.Thread(target=self.update_cursor_position)
        cursor_thread.daemon = True
        cursor_thread.start()
        
        # Start cursor blinking thread
        blink_thread = threading.Thread(target=self.blink_peer_cursors)
        blink_thread.daemon = True
        blink_thread.start()
        
        return True
        
    def connect_to_canvas(self):
        try:
            self.canvas_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.canvas_socket.connect((self.canvas_host, self.canvas_port))
            self.canvas_connected = True
            
            # Start listening for canvas events
            self.canvas_listen_thread = threading.Thread(target=self.listen_for_canvas_events)
            self.canvas_listen_thread.daemon = True
            self.canvas_listen_thread.start()
            
            return True
        except Exception as e:
            print(f"Canvas connection error: {e}")
            return False
            
    def connect_to_server(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.connect((self.server_host, self.server_port))
            self.server_connected = True
            
            # Start listening for server messages
            self.server_listen_thread = threading.Thread(target=self.listen_for_server_messages)
            self.server_listen_thread.daemon = True
            self.server_listen_thread.start()
            
            # Send username to server
            self.send_to_server({
                'type': 'username',
                'username': self.username
            })
            
            return True
        except Exception as e:
            print(f"Server connection error: {e}")
            return False

    def disconnect(self):
        self.disconnect_from_server()
        self.disconnect_from_canvas()
        
    def disconnect_from_canvas(self):
        if self.canvas_connected:
            self.canvas_connected = False
            try:
                self.canvas_socket.close()
            except:
                pass
                
    def disconnect_from_server(self):
        if self.server_connected:
            self.server_connected = False
            try:
                self.server_socket.close()
            except:
                pass

    def send_command(self, command):
        if not self.canvas_connected:
            return False
        
        if not command.endswith('\n'):
            command += '\n'
        
        try:
            self.canvas_socket.sendall(command.encode('utf-8'))
            return True
        except Exception as e:
            print(f"Canvas send error: {e}")
            self.canvas_connected = False
            return False
            
    def send_to_server(self, data):
        if not self.server_connected:
            return False
            
        try:
            # Convert to JSON and add newline
            message = json.dumps(data) + '\n'
            
            # Send to server
            self.server_socket.sendall(message.encode('utf-8'))
            return True
        except Exception as e:
            print(f"Server send error: {e}")
            self.server_connected = False
            return False

    def listen_for_canvas_events(self):
        buffer = ""
        
        while self.canvas_connected:
            try:
                data = self.canvas_socket.recv(1024).decode('utf-8')
                if not data:
                    self.canvas_connected = False
                    break
                
                buffer += data
                
                # Process complete events (ones that end with newline)
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    self.process_canvas_event(line)
                    
            except Exception as e:
                print(f"Canvas receive error: {e}")
                self.canvas_connected = False
                break
                
    def listen_for_server_messages(self):
        buffer = ""
        
        while self.server_connected:
            try:
                data = self.server_socket.recv(4096).decode('utf-8')
                if not data:
                    self.server_connected = False
                    break
                    
                buffer += data
                
                # Process complete messages (ones that end with newline)
                while '\n' in buffer:
                    message, buffer = buffer.split('\n', 1)
                    self.process_server_message(message)
                    
            except Exception as e:
                print(f"Server receive error: {e}")
                self.server_connected = False
                break
                
        print("Disconnected from collaboration server")

    def process_canvas_event(self, event_str):
        parts = event_str.split(',')
        if len(parts) >= 1:
            event_type = parts[0]
            
            if event_type in self.event_handlers:
                for handler in self.event_handlers[event_type]:
                    handler(parts)
                    
    def process_server_message(self, message_str):
        try:
            data = json.loads(message_str)
            message_type = data.get('type')
            
            if message_type == 'welcome':
                # Server is telling us our client ID and color
                self.client_id = data.get('client_id')
                self.user_color = data.get('color')
                if data.get('username'):
                    self.username = data.get('username')
                print(f"Connected to server as {self.username} with color {self.user_color}")
                
            elif message_type == 'draw':
                # Someone drew something
                draw_object = data.get('object')
                if draw_object:
                    self.drawing_objects.append(draw_object)
                    self.render()
                    
            elif message_type == 'clear':
                # Someone cleared the whiteboard
                self.drawing_objects = []
                self.render()
                
            elif message_type == 'cursor':
                # Someone moved their cursor
                username = data.get('username')
                x = data.get('x')
                y = data.get('y')
                color = data.get('color')
                
                if username and username != self.username and x is not None and y is not None:
                    self.peers[username] = {
                        'x': x,
                        'y': y,
                        'color': color,
                        'last_updated': time.time()
                    }
                    self.render()
                    
            elif message_type == 'username':
                # Someone changed their username
                old_username = data.get('old_username')
                new_username = data.get('new_username')
                color = data.get('color')
                
                if old_username in self.peers:
                    # Update the username in peers dictionary
                    self.peers[new_username] = self.peers[old_username]
                    self.peers[new_username]['color'] = color
                    del self.peers[old_username]
                    self.render()
                    
            elif message_type == 'disconnect':
                # Someone disconnected
                username = data.get('username')
                
                if username in self.peers:
                    del self.peers[username]
                    self.render()
                    
        except json.JSONDecodeError:
            print(f"Invalid JSON from server: {message_str}")
        except Exception as e:
            print(f"Error processing server message: {e}")

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
            'properties': properties
        }
        
        # Add locally
        self.drawing_objects.append(obj)
        
        # Send to server
        self.send_to_server({
            'type': 'draw',
            'object': obj
        })
        
        # Redraw
        self.render()
        
    def clear_whiteboard(self):
        # Clear locally
        self.drawing_objects = []
        
        # Tell server
        self.send_to_server({
            'type': 'clear'
        })
        
        # Redraw
        self.render()
        
    def update_cursor_position(self):
        """Periodically send cursor position to server"""
        while self.canvas_connected and self.server_connected:
            # Only send updates if mouse has moved since last update
            now = time.time()
            if now - self.last_cursor_update > 0.1:  # Limit to 10 updates per second max
                self.send_to_server({
                    'type': 'cursor',
                    'x': self.current_x,
                    'y': self.current_y
                })
                self.last_cursor_update = now
                
            time.sleep(0.1)
            
    def blink_peer_cursors(self):
        """Thread to handle blinking peer cursors"""
        while self.canvas_connected:
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
            obj_type = obj.get('type')
            props = obj.get('properties', {})
            
            if obj_type == 'point':
                self.draw_point(props.get('x'), props.get('y'), props.get('color'), props.get('size'))
            elif obj_type == 'line':
                self.draw_line(props.get('x1'), props.get('y1'), props.get('x2'), props.get('y2'),
                              props.get('color'), props.get('size'))
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
                cursor_x = info['x']
                cursor_y = info['y']
                color = info['color']
                
                # Draw cursor
                self.draw_rect(cursor_x-5, cursor_y-5, 10, 10, color)
                
                # Draw username above cursor
                self.draw_text(cursor_x + 15, cursor_y - 15, color, username)
                
        # Draw status bar
        status_y = self.canvas_height - self.status_bar_height
        self.draw_rect(0, status_y, self.canvas_width, self.status_bar_height, "#2C3E50")
        
        # Show tool and color info
        status_text = f"Tool: {self.current_tool.capitalize()} | Color: {self.current_color} | Size: {self.tool_size}"
        self.draw_text(10, status_y + 3, "#FFFFFF", status_text)
        
        # Show connected peers count
        peers_text = f"Connected: {len(self.peers) + 1} users"
        peers_x = self.canvas_width - (len(peers_text) * 8) - 10
        self.draw_text(peers_x, status_y + 3, "#FFFFFF", peers_text)
        
        # Show username in center
        user_text = f"You: {self.username}"
        user_x = (self.canvas_width - (len(user_text) * 8)) // 2
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
            
            # Update cursor position
            self.current_x = x
            self.current_y = y
            self.last_cursor_update = time.time()
            
            # Check if clicking in toolbar
            if y < self.toolbar_height:
                self.handle_toolbar_click(x, y)
                return
                
            # Start drawing
            self.is_drawing = True
            self.start_x = x
            self.start_y = y
            
            # For pen tool, add first point
            if self.current_tool == 'pen':
                self.add_drawing_object('point', {
                    'x': x,
                    'y': y,
                    'color': self.current_color,
                    'size': self.tool_size
                })
            elif self.current_tool == 'eraser':
                # Implementation of eraser - just draw white points for now
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
            
            # Update cursor position
            self.current_x = x
            self.current_y = y
            self.last_cursor_update = time.time()
            
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
            
    def handle_mousemove(self, event_parts):
        if len(event_parts) >= 3:
            x = int(event_parts[1])
            y = int(event_parts[2])
            
            # Update cursor position
            self.current_x = x
            self.current_y = y
            self.last_cursor_update = time.time()
            
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
    parser = argparse.ArgumentParser(description='Collaborative Whiteboard Client')
    parser.add_argument('--canvas-host', default='localhost', help='Canvas API host')
    parser.add_argument('--canvas-port', type=int, default=5005, help='Canvas API port')
    parser.add_argument('--server-host', default='localhost', help='Collaboration server host')
    parser.add_argument('--server-port', type=int, default=5006, help='Collaboration server port')
    parser.add_argument('--username', help='Your username')
    
    args = parser.parse_args()
    
    print(f"Starting Collaborative Whiteboard")
    print(f"Connecting to canvas at {args.canvas_host}:{args.canvas_port}")
    print(f"Connecting to server at {args.server_host}:{args.server_port}")
    print("Controls:")
    print("  Mouse: Draw with selected tool")
    print("  + / -: Increase/decrease tool size")
    print("  c: Clear whiteboard")
    
    whiteboard = CollaborativeWhiteboardClient(
        canvas_host=args.canvas_host,
        canvas_port=args.canvas_port,
        server_host=args.server_host,
        server_port=args.server_port,
        username=args.username
    )
    
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
                if not whiteboard.canvas_connected or not whiteboard.server_connected:
                    print("Connection lost. Exiting...")
                    break
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nExiting...")
        finally:
            whiteboard.disconnect()
    else:
        print("Failed to connect. Make sure socket_canvas.py and whiteboard_server.py are running.")


if __name__ == "__main__":
    main()
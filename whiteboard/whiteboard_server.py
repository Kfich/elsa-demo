#!/usr/bin/env python3
import socket
import threading
import json
import time
import argparse
import random

class WhiteboardServer:
    def __init__(self, host='localhost', port=5006):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        self.clients = {}  # {client_id: {'socket': socket, 'username': username, 'color': color}}
        self.drawing_objects = []  # Shared whiteboard state
        self.client_positions = {}  # {username: {'x': x, 'y': y, 'last_update': timestamp}}
        
    def start(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True
            
            print(f"Whiteboard Server started on {self.host}:{self.port}")
            
            # Start cleanup thread
            cleanup_thread = threading.Thread(target=self.cleanup_inactive_clients)
            cleanup_thread.daemon = True
            cleanup_thread.start()
            
            # Accept client connections
            while self.running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    client_id = str(id(client_socket))
                    
                    # Generate a random color for this client
                    r = random.randint(0, 200)
                    g = random.randint(0, 200)
                    b = random.randint(0, 200)
                    color = f"#{r:02x}{g:02x}{b:02x}"
                    
                    # Set up new client
                    self.clients[client_id] = {
                        'socket': client_socket,
                        'username': f"User-{client_id[-4:]}",
                        'color': color,
                        'address': client_address
                    }
                    
                    print(f"New client connected: {client_address} (ID: {client_id})")
                    
                    # Send initial state to client
                    self.send_initial_state(client_id)
                    
                    # Create thread to handle this client
                    client_thread = threading.Thread(target=self.handle_client, args=(client_id,))
                    client_thread.daemon = True
                    client_thread.start()
                    
                except Exception as e:
                    print(f"Error accepting connection: {e}")
                    if not self.running:
                        break
            
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            self.stop()
            
    def stop(self):
        self.running = False
        
        # Close all client connections
        for client_id in list(self.clients.keys()):
            try:
                self.clients[client_id]['socket'].close()
            except:
                pass
            del self.clients[client_id]
            
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
                
        print("Whiteboard Server stopped")
        
    def send_initial_state(self, client_id):
        """Send current whiteboard state to a new client"""
        if client_id not in self.clients:
            return
            
        try:
            client = self.clients[client_id]
            
            # Send welcome message
            welcome_msg = {
                'type': 'welcome',
                'client_id': client_id,
                'username': client['username'],
                'color': client['color']
            }
            self.send_to_client(client_id, welcome_msg)
            
            # Send all existing drawing objects
            for obj in self.drawing_objects:
                obj_msg = {
                    'type': 'draw',
                    'object': obj
                }
                self.send_to_client(client_id, obj_msg)
                
            # Send info about other connected clients
            for cid, c in self.clients.items():
                if cid != client_id and c['username'] in self.client_positions:
                    pos = self.client_positions[c['username']]
                    cursor_msg = {
                        'type': 'cursor',
                        'username': c['username'],
                        'x': pos['x'],
                        'y': pos['y'],
                        'color': c['color']
                    }
                    self.send_to_client(client_id, cursor_msg)
                    
        except Exception as e:
            print(f"Error sending initial state to client {client_id}: {e}")
            
    def handle_client(self, client_id):
        """Handle messages from a client"""
        if client_id not in self.clients:
            return
            
        client = self.clients[client_id]
        client_socket = client['socket']
        buffer = ""
        
        while self.running and client_id in self.clients:
            try:
                data = client_socket.recv(4096).decode('utf-8')
                if not data:
                    break
                    
                buffer += data
                
                # Process complete messages (ones that end with newline)
                while '\n' in buffer:
                    message, buffer = buffer.split('\n', 1)
                    self.process_client_message(client_id, message)
                    
            except Exception as e:
                print(f"Error receiving from client {client_id}: {e}")
                break
                
        # Client disconnected or error
        self.disconnect_client(client_id)
        
    def process_client_message(self, client_id, message):
        """Process a message received from a client"""
        if client_id not in self.clients:
            return
            
        try:
            # Parse the message (should be JSON)
            data = json.loads(message)
            
            message_type = data.get('type')
            
            if message_type == 'draw':
                # Client is drawing something
                draw_object = data.get('object')
                if draw_object:
                    # Add username to the object
                    draw_object['username'] = self.clients[client_id]['username']
                    
                    # Add to our record
                    self.drawing_objects.append(draw_object)
                    
                    # Broadcast to all other clients
                    self.broadcast({
                        'type': 'draw',
                        'object': draw_object
                    }, exclude=client_id)
                    
            elif message_type == 'clear':
                # Client wants to clear the whiteboard
                self.drawing_objects = []
                
                # Broadcast to all clients
                self.broadcast({
                    'type': 'clear'
                })
                
            elif message_type == 'cursor':
                # Client is moving their cursor
                x = data.get('x')
                y = data.get('y')
                
                if x is not None and y is not None:
                    username = self.clients[client_id]['username']
                    self.client_positions[username] = {
                        'x': x,
                        'y': y,
                        'last_update': time.time()
                    }
                    
                    # Broadcast cursor position to other clients
                    self.broadcast({
                        'type': 'cursor',
                        'username': username,
                        'x': x,
                        'y': y,
                        'color': self.clients[client_id]['color']
                    }, exclude=client_id)
                    
            elif message_type == 'username':
                # Client is setting their username
                new_username = data.get('username')
                
                if new_username and isinstance(new_username, str):
                    # Update username
                    old_username = self.clients[client_id]['username']
                    self.clients[client_id]['username'] = new_username
                    
                    # Update position record if exists
                    if old_username in self.client_positions:
                        self.client_positions[new_username] = self.client_positions[old_username]
                        del self.client_positions[old_username]
                    
                    # Broadcast username change to all clients
                    self.broadcast({
                        'type': 'username',
                        'old_username': old_username,
                        'new_username': new_username,
                        'color': self.clients[client_id]['color']
                    })
                    
        except json.JSONDecodeError:
            print(f"Invalid JSON from client {client_id}: {message}")
        except Exception as e:
            print(f"Error processing message from client {client_id}: {e}")
            
    def send_to_client(self, client_id, data):
        """Send a message to a specific client"""
        if client_id not in self.clients:
            return False
            
        try:
            # Convert to JSON and add newline
            message = json.dumps(data) + '\n'
            
            # Send to client
            self.clients[client_id]['socket'].sendall(message.encode('utf-8'))
            return True
        except Exception as e:
            print(f"Error sending to client {client_id}: {e}")
            self.disconnect_client(client_id)
            return False
            
    def broadcast(self, data, exclude=None):
        """Send a message to all connected clients"""
        # Make a copy of client IDs to avoid modification during iteration
        client_ids = list(self.clients.keys())
        
        for client_id in client_ids:
            if exclude and client_id == exclude:
                continue
                
            self.send_to_client(client_id, data)
            
    def disconnect_client(self, client_id):
        """Handle client disconnection"""
        if client_id not in self.clients:
            return
            
        try:
            # Get username before removing client
            username = self.clients[client_id]['username']
            
            # Close socket
            try:
                self.clients[client_id]['socket'].close()
            except:
                pass
                
            # Remove from clients dictionary
            del self.clients[client_id]
            
            # Remove from positions if exists
            if username in self.client_positions:
                del self.client_positions[username]
                
            print(f"Client disconnected: {client_id} ({username})")
            
            # Notify other clients
            self.broadcast({
                'type': 'disconnect',
                'username': username
            })
            
        except Exception as e:
            print(f"Error disconnecting client {client_id}: {e}")
            
    def cleanup_inactive_clients(self):
        """Periodically clean up inactive clients based on cursor activity"""
        while self.running:
            try:
                # Sleep first
                time.sleep(30)  # Check every 30 seconds
                
                # Current time
                now = time.time()
                
                # Find usernames of clients with no activity for over 2 minutes
                inactive_usernames = []
                for username, position in self.client_positions.items():
                    if now - position['last_update'] > 120:  # 2 minutes
                        inactive_usernames.append(username)
                
                # Find client IDs associated with inactive usernames
                inactive_clients = []
                for client_id, client in self.clients.items():
                    if client['username'] in inactive_usernames:
                        inactive_clients.append(client_id)
                
                # Disconnect inactive clients
                for client_id in inactive_clients:
                    print(f"Disconnecting inactive client: {client_id}")
                    self.disconnect_client(client_id)
                    
            except Exception as e:
                print(f"Error in cleanup thread: {e}")
                

def main():
    parser = argparse.ArgumentParser(description='Collaborative Whiteboard Server')
    parser.add_argument('--host', default='localhost', help='Server host')
    parser.add_argument('--port', type=int, default=5006, help='Server port')
    
    args = parser.parse_args()
    
    server = WhiteboardServer(args.host, args.port)
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        server.stop()


if __name__ == "__main__":
    main()
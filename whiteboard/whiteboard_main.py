#!/usr/bin/env python3
import subprocess
import time
import sys
import os
import signal
import argparse

def print_colored(text, color):
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'purple': '\033[95m',
        'cyan': '\033[96m',
        'end': '\033[0m'
    }
    print(f"{colors.get(color, '')}{text}{colors['end']}")

def run_component(name, command, color):
    print_colored(f"Starting {name}...", color)
    return subprocess.Popen(command, shell=True)

def main():
    parser = argparse.ArgumentParser(description='Run Collaborative Whiteboard')
    parser.add_argument('--canvas-port', type=int, default=5005, help='Port for canvas server')
    parser.add_argument('--server-port', type=int, default=5006, help='Port for collaboration server')
    parser.add_argument('--username', default=None, help='Username for client')
    parser.add_argument('--clients', type=int, default=1, help='Number of clients to start')
    parser.add_argument('--standalone', action='store_true', help='Run standalone (non-collaborative) client')
    
    args = parser.parse_args()
    
    processes = []
    
    try:
        # Start canvas server
        canvas_cmd = f"python socket_canvas.py --port {args.canvas_port}"
        canvas_process = run_component("Canvas Server", canvas_cmd, "green")
        processes.append(canvas_process)
        
        # Wait for canvas to start
        time.sleep(1)
        
        if not args.standalone:
            # Start collaboration server
            server_cmd = f"python whiteboard_server.py --port {args.server_port}"
            server_process = run_component("Collaboration Server", server_cmd, "blue")
            processes.append(server_process)
            
            # Wait for server to start
            time.sleep(1)
            
            # Start clients
            for i in range(args.clients):
                username = args.username or f"User{i+1}"
                if args.clients > 1:
                    username = f"{username}{i+1}"
                    
                client_cmd = (f"python collaborative_whiteboard_client.py --canvas-port {args.canvas_port} "
                             f"--server-port {args.server_port} --username {username}")
                client_process = run_component(f"Client {i+1}", client_cmd, "purple")
                processes.append(client_process)
                
                # Brief delay between starting clients
                time.sleep(0.5)
        else:
            # Start standalone client
            client_cmd = f"python whiteboard_client.py --port {args.canvas_port}"
            client_process = run_component("Standalone Client", client_cmd, "yellow")
            processes.append(client_process)
        
        print_colored("\nAll components started! Press Ctrl+C to shut down.\n", "cyan")
        
        # Wait for processes to finish or until interrupted
        for p in processes:
            p.wait()
            
    except KeyboardInterrupt:
        print_colored("\nShutting down all components...", "yellow")
    finally:
        # Clean up all processes
        for p in processes:
            try:
                p.terminate()
                p.wait(timeout=1)
            except:
                # Force kill if it doesn't terminate cleanly
                if p.poll() is None:
                    if sys.platform == 'win32':
                        os.kill(p.pid, signal.CTRL_C_EVENT)
                    else:
                        os.kill(p.pid, signal.SIGKILL)
        
        print_colored("All components stopped.", "red")

if __name__ == "__main__":
    main()
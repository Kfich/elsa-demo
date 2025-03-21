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
    parser = argparse.ArgumentParser(description='Run Integrated Chess Platform')
    parser.add_argument('--canvas-port', type=int, default=5005, help='Port for canvas server')
    parser.add_argument('--server-port', type=int, default=5006, help='Port for game server')
    parser.add_argument('--name', default=None, help='Player name')
    parser.add_argument('--players', type=int, default=1, help='Number of clients to start')
    
    args = parser.parse_args()
    
    processes = []
    
    try:
        # Start canvas server
        canvas_cmd = "python socket_canvas.py"
        canvas_process = run_component("Canvas Server", canvas_cmd, "green")
        processes.append(canvas_process)
        
        # Wait for canvas to start
        time.sleep(1)
        
        # Start game server
        server_cmd = f"python chess_server.py --port {args.server_port}"
        server_process = run_component("Chess Server", server_cmd, "blue")
        processes.append(server_process)
        
        # Wait for server to start
        time.sleep(1)
        
        # Start clients
        for i in range(args.players):
            player_name = args.name or f"Player{i+1}"
            if args.players > 1:
                player_name = f"{player_name}{i+1}"
                
            client_cmd = (f"python chess_client.py --port {args.canvas_port} "
                         f"--server-port {args.server_port} --name {player_name}")
            client_process = run_component(f"Chess Client {i+1}", client_cmd, "purple")
            processes.append(client_process)
            
            # Brief delay between starting clients
            time.sleep(0.5)
        
        print_colored("\nAll components started! Press Ctrl+C to shut down.\n", "cyan")
        print_colored("Modern Chess Game Instructions:", "yellow")
        print_colored("1. Create a new game in the lobby", "yellow")
        print_colored("2. Start another client to join the game", "yellow")
        print_colored("3. Hover and click on your pieces to select them", "yellow")
        print_colored("4. Valid moves will be highlighted with green dots", "yellow")
        print_colored("5. Click on a valid move location to move your piece", "yellow")
        print_colored("6. Watch for the turn indicator to know when it's your turn", "yellow")
        
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
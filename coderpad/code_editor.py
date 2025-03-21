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
    parser = argparse.ArgumentParser(description='Run Modern Live Code Editor with Execution Visualization')
    parser.add_argument('--port', type=int, default=5005, help='Port for canvas server')
    
    args = parser.parse_args()
    
    processes = []
    
    try:
        # Print welcome message
        print_colored("\n╔════════════════════════════════════════════════════════════╗", "cyan")
        print_colored("║                Modern Live Code Editor                     ║", "cyan")
        print_colored("║          with Real-time Execution Visualization           ║", "cyan")
        print_colored("╚════════════════════════════════════════════════════════════╝\n", "cyan")
        
        # Start canvas server
        canvas_cmd = f"python socket_canvas.py"
        canvas_process = run_component("Canvas Server", canvas_cmd, "green")
        processes.append(canvas_process)
        
        # Wait for canvas to start
        time.sleep(1)
        
        # Start modern code editor client
        client_cmd = f"python code_editor_client.py --port {args.port}"
        client_process = run_component("Modern Code Editor Client", client_cmd, "blue")
        processes.append(client_process)
        
        print_colored("\nAll components started! Press Ctrl+C to shut down.\n", "green")
        print_colored("Modern Code Editor Features:", "yellow")
        print_colored("  • VS Code-inspired dark theme with syntax highlighting", "yellow")
        print_colored("  • Real-time execution visualization with variable tracking", "yellow")
        print_colored("  • Animated UI elements and cursor blinking", "yellow") 
        print_colored("  • Step-by-step debugging with breakpoints", "yellow")
        print_colored("  • Live console output display", "yellow")
        
        print_colored("\nInstructions:", "purple")
        print_colored("  1. Type Python code in the editor area", "purple")
        print_colored("  2. Click the 'Run' button to execute the code with visualization", "purple")
        print_colored("  3. Click the 'Step' button to execute one step at a time", "purple")
        print_colored("  4. Click on line numbers to toggle breakpoints", "purple")
        print_colored("  5. Use the 'Faster' and 'Slower' buttons to adjust execution speed", "purple")
        print_colored("  6. View variables, call stack, and console output in real-time", "purple")
        
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
        print_colored("\nThank you for using the Modern Live Code Editor!", "cyan")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import socket
import time
import signal

class CanvasAppsLauncher:
    """
    A launcher application that provides a GUI to select and launch
    various socket canvas-based applications in the project.
    """
    
    def __init__(self, title="App Center", width=800, height=600):
        """Initialize the launcher application"""
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry(f"{width}x{height}")
        self.root.resizable(True, True)
        
        # Active processes
        self.active_processes = {}
        
        # Available apps
        self.apps = [
            {
                "name": "Text Editor",
                "description": "A feature-rich text editor with line numbers, copy/paste, and syntax highlighting.",
                "module": "main.py",
                "category": "Productivity",
                "image": "text_editor.png",
                "command": lambda: self.launch_app("./editor/main.py")
            },
            {
                "name": "Chess Game",
                "description": "A multiplayer chess game with a lobby system for creating and joining games.",
                "module": "chess.py",
                "category": "Games",
                "image": "chess.png",
                "command": lambda: self.launch_app("./chess/chess.py")
            },
            {
                "name": "Whiteboard",
                "description": "A collaborative drawing application with real-time updates across clients.",
                "module": "whiteboard_main.py",
                "category": "Productivity",
                "image": "whiteboard.png",
                "command": lambda: self.launch_app("./whiteboard/whiteboard_main.py")
            },
            {
                "name": "Code Editor",
                "description": "A Python code editor with execution visualization and debugging features.",
                "module": "code_editor.py",
                "category": "Development",
                "image": "code_editor.png",
                "command": lambda: self.launch_app("./coderpad/code_editor.py")
            },
        ]
        
        # Track if socket_canvas is running
        self.socket_canvas_process = None
        
        # Create the GUI
        self.create_widgets()
        
        # Register cleanup handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def on_treeview_click(self, event):
        """Handle clicks in the process treeview, especially on action buttons"""
        region = self.process_tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.process_tree.identify_column(event.x)
            if column == "#4":  # Actions column
                item = self.process_tree.identify_row(event.y)
                if item:
                    values = self.process_tree.item(item, "values")
                    if len(values) >= 4:  # Make sure we have the action column
                        action = values[3]
                        if action == "Stop":
                            self.stop_process(item)
                        elif action == "Remove":
                            # Remove from the treeview and dictionary
                            self.process_tree.delete(item)
                            if item in self.active_processes:
                                del self.active_processes[item]
    
    def create_widgets(self):
        """Create and arrange all GUI widgets"""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Style configuration
        style = ttk.Style()
        style.configure("Header.TLabel", font=("Arial", 16, "bold"))
        style.configure("AppTitle.TLabel", font=("Arial", 12, "bold"))
        style.configure("AppDesc.TLabel", font=("Arial", 10))
        style.configure("Category.TLabel", font=("Arial", 14, "bold"))
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        header_label = ttk.Label(
            header_frame, 
            text="Canvas Apps Launcher",
            style="Header.TLabel"
        )
        header_label.pack(side=tk.LEFT)
        
        # Socket Canvas status indicator
        self.status_var = tk.StringVar(value="Socket Canvas: Not Running")
        self.status_label = ttk.Label(
            header_frame,
            textvariable=self.status_var,
            foreground="red"
        )
        self.status_label.pack(side=tk.RIGHT)
        
        # Start/Stop Socket Canvas button
        self.socket_button_var = tk.StringVar(value="Start Socket Canvas")
        self.socket_button = ttk.Button(
            header_frame,
            textvariable=self.socket_button_var,
            command=self.toggle_socket_canvas,
            width=20
        )
        self.socket_button.pack(side=tk.RIGHT, padx=(0, 10))
        
        # Create a notebook for categories
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create category pages
        self.category_frames = {}
        categories = set(app["category"] for app in self.apps)
        
        # Add "All" category
        all_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(all_frame, text="All Apps")
        self.category_frames["All"] = all_frame
        
        # Add other categories
        for category in sorted(categories):
            category_frame = ttk.Frame(self.notebook, padding=10)
            self.notebook.add(category_frame, text=category)
            self.category_frames[category] = category_frame
        
        # Create app cards for each category
        self.create_app_cards()
        
        # Active processes frame
        process_frame = ttk.LabelFrame(main_frame, text="Active Processes", padding=10)
        process_frame.pack(fill=tk.X, pady=(20, 0))
        
        # Create a treeview for active processes
        columns = ("App", "PID", "Status", "Actions")
        self.process_tree = ttk.Treeview(process_frame, columns=columns, show="headings")
        
        # Set column headings
        for col in columns:
            self.process_tree.heading(col, text=col)
            if col == "App":
                self.process_tree.column(col, width=150, stretch=tk.YES)
            elif col == "PID":
                self.process_tree.column(col, width=80, anchor=tk.CENTER)
            elif col == "Status":
                self.process_tree.column(col, width=100, anchor=tk.CENTER)
            else:
                self.process_tree.column(col, width=100, anchor=tk.CENTER)
        
        # Bind click event to the tree for handling action buttons
        self.process_tree.bind("<Button-1>", self.on_treeview_click)
        
        self.process_tree.pack(fill=tk.X)
        
        # Add buttons below treeview
        process_button_frame = ttk.Frame(process_frame)
        process_button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(
            process_button_frame,
            text="Stop Selected",
            command=self.stop_selected_process
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            process_button_frame,
            text="Stop All",
            command=self.stop_all_processes
        ).pack(side=tk.LEFT)
        
        # Check socket_canvas status initially
        self.check_socket_canvas()
    
    def create_app_cards(self):
        """Create card-like displays for each app"""
        # Create cards for "All" category
        self.create_category_app_cards("All", self.apps)
        
        # Group apps by category
        apps_by_category = {}
        for app in self.apps:
            category = app["category"]
            if category not in apps_by_category:
                apps_by_category[category] = []
            apps_by_category[category].append(app)
        
        # Create cards for each category
        for category, apps in apps_by_category.items():
            self.create_category_app_cards(category, apps)
    
    def create_category_app_cards(self, category, apps):
        """Create app cards for a specific category"""
        frame = self.category_frames[category]
        
        # Create a canvas with scrollbar for the category
        canvas = tk.Canvas(frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Create app cards in grid layout
        row, col = 0, 0
        max_cols = 2  # Number of cards per row
        
        for i, app in enumerate(apps):
            # Create a card frame
            card = ttk.Frame(scrollable_frame, padding=10, relief="raised")
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            
            # App title
            title_label = ttk.Label(
                card,
                text=app["name"],
                style="AppTitle.TLabel"
            )
            title_label.pack(anchor="w")
            
            # App description
            desc_label = ttk.Label(
                card,
                text=app["description"],
                style="AppDesc.TLabel",
                wraplength=300
            )
            desc_label.pack(anchor="w", pady=(5, 10))
            
            # Launch button
            launch_button = ttk.Button(
                card,
                text=f"Launch {app['name']}",
                command=app["command"]
            )
            launch_button.pack(anchor="e")
            
            # Update grid position
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        # Configure grid to expand columns evenly
        for i in range(max_cols):
            scrollable_frame.columnconfigure(i, weight=1)
    
    def launch_app(self, module):
        """Launch a specific app"""
        if not self.check_socket_canvas():
            response = messagebox.askyesno(
                "Socket Canvas Required",
                "Socket Canvas is not running. Start it now?",
                parent=self.root
            )
            if response:
                self.start_socket_canvas()
                # Give it time to start
                time.sleep(1)
                if not self.check_socket_canvas():
                    messagebox.showerror(
                        "Error",
                        "Failed to start Socket Canvas. Cannot launch app.",
                        parent=self.root
                    )
                    return
            else:
                return
        
        # Launch the app
        try:
            # Launch without capturing output so the app can show its own UI
            process = subprocess.Popen(
                [sys.executable, module],
                # Don't capture stdout/stderr
                stdout=None,
                stderr=None
            )
            
            app_name = next((app["name"] for app in self.apps if app["module"] == module), module)
            
            # Add to active processes
            process_id = str(process.pid)
            self.active_processes[process_id] = {
                "process": process,
                "app_name": app_name,
                "module": module,
                "status": "Running"
            }
            
            # Add to treeview
            self.process_tree.insert(
                "", "end", process_id,
                values=(app_name, process_id, "Running", "Stop")
            )
            
            # Start monitoring thread for this process
            monitor_thread = threading.Thread(
                target=self.monitor_process,
                args=(process_id,),
                daemon=True
            )
            monitor_thread.start()
            
        except Exception as e:
            messagebox.showerror(
                "Launch Error",
                f"Failed to launch {module}: {str(e)}",
                parent=self.root
            )
    
    def monitor_process(self, process_id):
        """Monitor a running process"""
        if process_id not in self.active_processes:
            return
        
        process_info = self.active_processes[process_id]
        process = process_info["process"]
        
        # Wait for process to finish
        process.wait()
        
        # Update status if the process is still in our dictionary
        if process_id in self.active_processes:
            return_code = process.returncode
            status = "Finished" if return_code == 0 else f"Error ({return_code})"
            
            # Update the status in the dictionary
            self.active_processes[process_id]["status"] = status
            
            # Update the treeview if it still exists
            try:
                # Update the UI from the main thread
                self.root.after(0, lambda: self.update_process_status(process_id, status))
            except Exception:
                # The item might have been removed
                pass
    
    def update_process_status(self, process_id, status):
        """Update process status in the treeview (called from main thread)"""
        try:
            if process_id in self.active_processes:
                process_info = self.active_processes[process_id]
                self.process_tree.item(process_id, values=(
                    process_info["app_name"],
                    process_id,
                    status,
                    "Remove"
                ))
        except tk.TclError:
            # Item might have been removed
            pass
    
    def stop_selected_process(self):
        """Stop the selected process"""
        selected = self.process_tree.selection()
        if not selected:
            messagebox.showinfo(
                "No Selection",
                "Please select a process to stop.",
                parent=self.root
            )
            return
        
        for item in selected:
            self.stop_process(item)
    
    def stop_process(self, process_id):
        """Stop a specific process"""
        if process_id not in self.active_processes:
            # Remove from treeview if it exists
            try:
                self.process_tree.delete(process_id)
            except tk.TclError:
                pass
            return
        
        process_info = self.active_processes[process_id]
        process = process_info["process"]
        
        try:
            # Try to terminate gracefully
            process.terminate()
            
            # Give it some time to terminate
            for _ in range(5):  # Wait up to 0.5 seconds
                if process.poll() is not None:
                    break
                time.sleep(0.1)
            
            # Force kill if still running
            if process.poll() is None:
                if sys.platform == "win32":
                    os.kill(process.pid, signal.CTRL_BREAK_EVENT)
                else:
                    os.kill(process.pid, signal.SIGKILL)
            
            # Update status in treeview
            self.process_tree.item(process_id, values=(
                process_info["app_name"],
                process_id,
                "Stopped",
                "Remove"
            ))
            
            # Update dictionary
            self.active_processes[process_id]["status"] = "Stopped"
            
        except Exception as e:
            messagebox.showerror(
                "Stop Error",
                f"Failed to stop process {process_id}: {str(e)}",
                parent=self.root
            )
    
    def stop_all_processes(self):
        """Stop all running processes"""
        if not self.active_processes:
            messagebox.showinfo(
                "No Processes",
                "No active processes to stop.",
                parent=self.root
            )
            return
        
        for process_id in list(self.active_processes.keys()):
            self.stop_process(process_id)
    
    def check_socket_canvas(self):
        """Check if socket_canvas is running"""
        # Check if our process is running
        if self.socket_canvas_process and self.socket_canvas_process.poll() is None:
            self.update_socket_canvas_status(True)
            return True
        
        # Check if port 5005 is in use
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex(('127.0.0.1', 5005))
            sock.close()
            
            is_running = result == 0
            self.update_socket_canvas_status(is_running)
            return is_running
        except:
            self.update_socket_canvas_status(False)
            return False
    
    def update_socket_canvas_status(self, is_running):
        """Update the socket canvas status display"""
        if is_running:
            self.status_var.set("Socket Canvas: Running")
            self.status_label.config(foreground="green")
            self.socket_button_var.set("Stop Socket Canvas")
        else:
            self.status_var.set("Socket Canvas: Not Running")
            self.status_label.config(foreground="red")
            self.socket_button_var.set("Start Socket Canvas")
    
    def toggle_socket_canvas(self):
        """Start or stop the socket canvas"""
        is_running = self.check_socket_canvas()
        
        if is_running:
            # Stop the socket canvas
            if self.socket_canvas_process:
                try:
                    self.socket_canvas_process.terminate()
                    
                    # Give it some time to terminate
                    for _ in range(5):  # Wait up to 0.5 seconds
                        if self.socket_canvas_process.poll() is not None:
                            break
                        time.sleep(0.1)
                    
                    # Force kill if still running
                    if self.socket_canvas_process.poll() is None:
                        if sys.platform == "win32":
                            os.kill(self.socket_canvas_process.pid, signal.CTRL_BREAK_EVENT)
                        else:
                            os.kill(self.socket_canvas_process.pid, signal.SIGKILL)
                    
                    self.socket_canvas_process = None
                    self.update_socket_canvas_status(False)
                    
                except Exception as e:
                    messagebox.showerror(
                        "Error",
                        f"Failed to stop Socket Canvas: {str(e)}",
                        parent=self.root
                    )
            else:
                # If we detected it running but don't have the process,
                # just update the status
                self.update_socket_canvas_status(False)
        else:
            # Start the socket canvas
            self.start_socket_canvas()
    
    def start_socket_canvas(self):
        """Start the socket canvas process"""
        try:
            # Launch socket_canvas without capturing its output
            self.socket_canvas_process = subprocess.Popen(
                [sys.executable, "socket_canvas.py"],
                # Don't capture stdout/stderr so it can display its own window
                stdout=None,
                stderr=None
            )
            
            # Give it some time to start
            time.sleep(0.5)
            
            # Check if it's running
            if self.socket_canvas_process.poll() is None:
                self.update_socket_canvas_status(True)
            else:
                # Process terminated quickly - something went wrong
                error_msg = "Socket canvas process terminated unexpectedly"
                self.socket_canvas_process = None
                messagebox.showerror(
                    "Start Error",
                    f"Failed to start Socket Canvas: {error_msg}",
                    parent=self.root
                )
        except Exception as e:
            messagebox.showerror(
                "Start Error",
                f"Failed to start Socket Canvas: {str(e)}",
                parent=self.root
            )
    
    def on_close(self):
        """Cleanup when the application is closing"""
        # Ask for confirmation if there are active processes
        if self.active_processes:
            response = messagebox.askyesno(
                "Confirm Exit",
                "There are active processes. Stop them and exit?",
                parent=self.root
            )
            if not response:
                return
            
            # Stop all processes
            self.stop_all_processes()
        
        # Stop socket canvas if we started it
        if self.socket_canvas_process and self.socket_canvas_process.poll() is None:
            try:
                self.socket_canvas_process.terminate()
                time.sleep(0.1)
                if self.socket_canvas_process.poll() is None:
                    if sys.platform == "win32":
                        os.kill(self.socket_canvas_process.pid, signal.CTRL_BREAK_EVENT)
                    else:
                        os.kill(self.socket_canvas_process.pid, signal.SIGKILL)
            except:
                pass
        
        # Close the application
        self.root.destroy()
    
    def run(self):
        """Run the launcher application"""
        # Set up periodic socket canvas check
        def check_socket_periodically():
            self.check_socket_canvas()
            self.root.after(5000, check_socket_periodically)
        
        # Start the periodic check
        self.root.after(5000, check_socket_periodically)
        
        # Start the mainloop
        self.root.mainloop()


def main():
    """Main entry point for the application"""
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Canvas Apps Launcher")
    parser.add_argument("--width", type=int, default=800, help="Window width")
    parser.add_argument("--height", type=int, default=600, help="Window height")
    args = parser.parse_args()
    
    # Create and run the launcher
    launcher = CanvasAppsLauncher(width=args.width, height=args.height)
    launcher.run()


if __name__ == "__main__":
    main()
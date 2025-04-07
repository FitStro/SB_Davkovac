import tkinter as tk
from tkinter import ttk, messagebox
import serial
import threading
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import serial.tools.list_ports


def get_available_port():
    ports = list(serial.tools.list_ports.comports())
    if ports:
        return ports[0].device  
    else:
        return None

port = get_available_port()
if port:
    arduino = serial.Serial(port, 9600, timeout=1)
else:
    print("No serial port found.")

target_count = 0
count = 0
mode = "target"
last_count_time = time.time()
counts_over_time = []

# Global statuses dictionary
statuses = {"Motor": "Unknown", "Servo": "Neutral", "Vibration": "Unknown"}

def update_status_label():
    status_label["text"] = (f"Status - Motor: {statuses['Motor']}, "
                            f"Servo: {statuses['Servo']}, "
                            f"Vibration: {statuses['Vibration']}")

def set_motor_pwm(value):
    pwm_value = int(value)
    arduino.write(f"MOTORPIN2:{pwm_value}\n".encode())
    statuses["Motor"] = f"PWM: {pwm_value}" if pwm_value != 0 else "OFF"
    update_status_label()

def update_item_count():
    global target_count, count, mode, last_count_time, counts_over_time
    while True:
        if arduino.in_waiting > 0:
            try:
                data = arduino.readline().decode(errors="ignore").strip()
                if "Item count:" in data:
                    count = int(data.split(":")[1].strip())
                    counts_over_time.append(count)
                    item_label["text"] = f"Detected objects: {count}"
                    
                    # Ak je režim na cieľ a počet prekročí limit, ukážeme prekročenie
                    if mode == "target" and target_count > 0:
                        if count > target_count:
                            last_excess = count - target_count
                        excess_label["text"] = f"(+{last_excess} nad limit)"
                    else:
                        excess_label["text"] = f"(+{last_excess} nad limit)"
                    
                    last_count_time = time.time()
                    update_graph()
                    
                    if mode == "target" and target_count > 0 and count >= target_count:
                        statuses["Servo"] = "Activated"
                        update_status_label()
                        arduino.write("SERVO: -90\n".encode())
                        set_motor_pwm(0)
                        statuses["Vibration"] = "OFF"
                        update_status_label()
                        messagebox.showinfo("Restart", "Target count reached. Click to restart counting.")
                        arduino.write("SERVO: 0\n".encode())
                        statuses["Servo"] = "Neutral"
                        update_status_label()
                        reset_count()
            except Exception as e:
                print(f"Error reading from serial port: {e}")
        
        if time.time() - last_count_time > 120:
            messagebox.showwarning("Warning", 
              "No object detected for 2 minutes. Possibly material is finished or an error occurred.")
            last_count_time = time.time()

def reset_count():
    global count
    count = 0
    item_label["text"] = "Detected objects: 0"
    arduino.write("RESET_COUNT\n".encode())
    arduino.write("MOTOR_ON\n".encode())
    statuses["Vibration"] = "ON"
    update_status_label()
    set_motor_pwm(225)
    excess_label["text"] = ""

def update_graph():
    ax.clear()
    ax.plot(counts_over_time, marker='o', linestyle='-')
    ax.set_title("Detected Objects Over Time")
    ax.set_xlabel("Time (iterations)")
    ax.set_ylabel("Count")
    canvas.draw()

def set_mode(selected_mode):
    global mode, count, last_count_time, target_count
    mode = selected_mode
    reset_count()
    if mode == "target":
        try:
            target_count = int(target_entry.get())
            messagebox.showinfo("Mode",
              f"Target count mode activated. Target: {target_count} items.")
        except ValueError:
            messagebox.showwarning("Error", "Enter a valid target count.")
    else:
        target_count = 0
        messagebox.showinfo("Mode", "Counter mode activated.")

root = tk.Tk()
root.title("Object Counting")
root.geometry("700x600")
root.configure(bg="#e1e1e1")

frame = ttk.Frame(root, padding=20)
frame.pack(fill="both", expand=True)

welcome_label = ttk.Label(frame, text="Select mode", font=("Arial", 16, "bold"))
welcome_label.pack(pady=10)

button_frame = ttk.Frame(frame)
button_frame.pack(pady=10)

target_button = ttk.Button(button_frame, text="Target Count", command=lambda: set_mode("target"))
target_button.pack(side=tk.LEFT, padx=10)

counter_button = ttk.Button(button_frame, text="Counter", command=lambda: set_mode("counter"))
counter_button.pack(side=tk.LEFT, padx=10)

target_entry = ttk.Entry(frame, width=10, font=("Arial", 14))
target_entry.pack(pady=10)

# Label pre zobrazenie prekročenia limitu
excess_label = ttk.Label(frame, text="", font=("Arial", 12))
excess_label.pack(pady=5)

set_target_button = ttk.Button(frame, text="Set Target", command=lambda: set_mode("target"))
set_target_button.pack(pady=5)

item_label = ttk.Label(frame, text="Detected objects: 0", font=("Arial", 14))
item_label.pack(pady=10)

status_label = ttk.Label(frame, text="Status - Motor: Unknown, Servo: Neutral, Vibration: Unknown", font=("Arial", 12))
status_label.pack(pady=5)

fig, ax = plt.subplots()
canvas = FigureCanvasTkAgg(fig, master=frame)
canvas.get_tk_widget().pack()

threading.Thread(target=update_item_count, daemon=True).start()

root.mainloop()
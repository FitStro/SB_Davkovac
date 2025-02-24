import tkinter as tk
from tkinter import ttk, messagebox
import serial
import threading

arduino = serial.Serial("COM4", 9600, timeout=1)
target_count = 0

def update_item_count():
    global target_count
    while True:
        if arduino.in_waiting > 0:
            try:
                data = arduino.readline().decode(errors="ignore").strip()
                if "Item count:" in data:
                    count = int(data.split(":")[1].strip())
                    item_label["text"] = f"Počet detekovaných objektov: {count}"
                    if target_count > 0 and count >= target_count:
                        arduino.write("SERVO: -360\n".encode())
                        set_motor_pwm(0)
                        messagebox.showinfo("Upozornenie", "Dosiahol sa požadovaný počet kusov!")
                        target_count = 0
            except Exception as e:
                print(f"Chyba pri čítaní zo sériového portu: {e}")

def rotate_motor():
    try:
        degrees = int(degree_entry.get())
        arduino.write(f"TURN:{degrees}\n".encode())
    except ValueError:
        degree_entry.delete(0, tk.END)
        degree_entry.insert(0, "Zadajte platnú hodnotu")

def toggle_vibrator(index):
    arduino.write(f"VIBRATE:{index}\n".encode())

def set_motor_pwm(value):
    pwm_value = int(value)
    arduino.write(f"MOTORPIN2:{pwm_value}\n".encode())
    pwm_label["text"] = f"Sila vibrácii: {pwm_value}"

def set_vibr_pwm(value1):
    pwm_value1 = int(value1)
    arduino.write(f"VibrPin2:{pwm_value1}\n".encode())
    pwm_label["text"] = f"VibrPin2: {pwm_value1}"

def set_target_count():
    global target_count
    try:
        target_count = int(target_entry.get())
        messagebox.showinfo("Upozornenie", f"Nastavený cieľový počet kusov: {target_count}")
    except ValueError:
        target_entry.delete(0, tk.END)
        target_entry.insert(0, "Zadajte platnú hodnotu")

def reset_all():
    global target_count
    target_count = 0
    degree_entry.delete(0, tk.END)
    degree_entry.insert(0, "0")
    pwm_slider.set(0)
    target_entry.delete(0, tk.END)
    target_entry.insert(0, "0")
    pwm_label["text"] = "PWM: 0"
    item_label["text"] = "Počet detekovaných objektov: 0"

root = tk.Tk()
root.title("Ovládanie a bloková schéma")

style = ttk.Style()
style.configure("TButton", font=("Times new roman", 12), padding=10)
style.configure("TLabel", font=("Times new roman", 14), padding=10)

# Create separate frames for the controls and the diagram
control_frame = ttk.Frame(root)
control_frame.pack(side=tk.LEFT, fill="both", expand=True, padx=10, pady=10)

diagram_frame = ttk.Frame(root)
diagram_frame.pack(side=tk.RIGHT, fill="both", expand=True, padx=10, pady=10)

# --- Control Panel Widgets (in control_frame) ---

# Stepper Motor
stepper_frame = ttk.LabelFrame(control_frame, text="Stepper Motor", padding=(10, 5))
stepper_frame.pack(padx=20, pady=15, fill="x")
degree_label = ttk.Label(stepper_frame, text="Otočiť o :")
degree_label.pack(side=tk.LEFT, padx=5)
degree_entry = ttk.Entry(stepper_frame, width=10)
degree_entry.pack(side=tk.LEFT, padx=5)
degree_entry.insert(0, "10")
rotate_button = ttk.Button(stepper_frame, text="Otočiť", command=rotate_motor)
rotate_button.pack(side=tk.LEFT, padx=5)

# Vibračné moduly
vibrator_frame = ttk.LabelFrame(control_frame, text="Vibračné moduly", padding=(10, 5))
vibrator_frame.pack(padx=20, pady=15, fill="x")
for i in range(4):
    button = ttk.Button(vibrator_frame, text=f"Vibrátor {i+1}", command=lambda i=i: toggle_vibrator(i))
    button.pack(side=tk.LEFT, padx=10)

# PWM motorPin2
pwm_frame = ttk.LabelFrame(control_frame, text="Sila vibrácii", padding=(20, 10))
pwm_frame.pack(padx=20, pady=15, fill="x")
pwm_label = ttk.Label(pwm_frame, text="PWM: 0", font=("Times new roman", 14))
pwm_label.pack()
pwm_slider = tk.Scale(pwm_frame, from_=0, to=255, orient=tk.HORIZONTAL, command=set_motor_pwm)
pwm_slider.pack(fill="x", padx=10)

# Cieľový počet kusov
target_frame = ttk.LabelFrame(control_frame, text="Cieľový počet kusov", padding=(10, 5))
target_frame.pack(padx=20, pady=15, fill="x")
target_label = ttk.Label(target_frame, text="Zadajte cieľový počet kusov:")
target_label.pack(side=tk.LEFT, padx=5)
target_entry = ttk.Entry(target_frame, width=5, font=("Times new roman", 20))
target_entry.pack(side=tk.LEFT, padx=5)
target_button = ttk.Button(target_frame, text="Nastaviť", command=set_target_count)
target_button.pack(side=tk.LEFT, padx=5)

# Reset Button
reset_button = ttk.Button(control_frame, text="Reset", command=reset_all)
reset_button.pack(pady=10)

# Object counter display
item_label = ttk.Label(control_frame, text="Počet detekovaných objektov: 0", font=("Times new roman", 16))
item_label.pack(pady=20)

# --- Block Diagram (in diagram_frame) ---

def update_block_states():
    global active_states
    try:
        data = arduino.readline().decode(errors="ignore").strip()
        if "BLOCK_STATES:" in data:
            states = data.split(":")[1].strip().split(",")
            for i, name in enumerate(blocks.keys()):
                active_states[name] = (states[i] == '1')
                new_color = "lightgreen" if active_states[name] else "lightgray"
                diagram_canvas.itemconfigure(block_items[name], fill=new_color)
    except Exception as e:
        print(f"Error updating block states: {e}")
    root.after(100, update_block_states)  # Schedule the update every 100 ms


diagram_canvas = tk.Canvas(diagram_frame, width=600, height=450, bg="white")
diagram_canvas.pack()

blocks = {
    "Náklon": (50, 50, 150, 80),
    "Vibračné moduly": (250, 50, 150, 80),
    "Servo": (450, 50, 150, 80),
    "Vibračné motory": (50, 180, 150, 80),
    "Cieľový počet": (250, 180, 150, 80),
    "Detekcia objektov": (450, 180, 150, 80)
}

block_items = {}
active_states = {name: False for name in blocks}

def draw_blocks():
    for name, (x, y, w, h) in blocks.items():
        rect = diagram_canvas.create_rectangle(x, y, x+w, y+h, fill="white", outline="blue", width=2)
        diagram_canvas.create_text(x+w/2, y+h/2, text=name, font=("Times new roman", 12))
        block_items[name] = rect

def toggle_block(name):
    active_states[name] = not active_states[name]
    new_color = "blue" if active_states[name] else "white"
    diagram_canvas.itemconfigure(block_items[name], fill=new_color)

def on_canvas_click(event):
    for name, (x, y, w, h) in blocks.items():
        if x <= event.x <= x+w and y <= event.y <= y+h:
            toggle_block(name)
            break

draw_blocks()
diagram_canvas.bind("<Button-1>", on_canvas_click)

# Start the thread to update the item count
threading.Thread(target=update_item_count, daemon=True).start()

root.mainloop()

import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Button
from collections import deque
import threading
import queue

# Serial port configuration
PORT = '/dev/tty.usbmodem102'  # Adjust depending on your specified port
BAUDRATE = 115200
MAX_POINTS = 1000  # For high-resolution plotting

# Initialize serial port
try:
    ser = serial.Serial(PORT, BAUDRATE, timeout=1)
    print(f"Serial port {PORT} opened successfully")
except serial.SerialException as e:
    print(f"Error opening serial port {PORT}: {e}")
    exit(1)

# Data queue for serial input
data_queue = queue.Queue()

# Thread function to read serial data
def serial_reader():
    while True:
        try:
            line = ser.readline().decode('utf-8').strip()
            if line:
                data_queue.put(line)
        except serial.SerialException as e:
            print(f"Serial error: {e}")
            break

# Start the serial reading thread
thread = threading.Thread(target=serial_reader, daemon=True)
thread.start()

# Data buffers
time_buffer = deque(maxlen=MAX_POINTS)
data_buffer = deque(maxlen=MAX_POINTS)
current_time = 0  # Time in seconds

# Set up the plot with a dark oscilloscope theme
plt.style.use('dark_background')
fig, ax = plt.subplots(figsize=(10, 6), facecolor='black')
ax.set_facecolor('black')
ax.set_ylim(-0.5, 3.8)  # For 0V to 3.3V signal
ax.set_xlim(0, 0.1)  # 100ms time window
ax.set_xlabel('Time (s)', color='white')
ax.set_ylabel('Voltage (V)', color='white')
ax.set_title('Live Oscilloscope - Single Signal (0V to 3.3V)', color='white')
ax.axhline(0, color='gray', linewidth=0.8, linestyle='--')
ax.grid(True, color='gray', linestyle='--', linewidth=0.5)
ax.tick_params(axis='both', colors='white')
line, = ax.plot([], [], color='lime', label='Signal')
ax.legend(loc='upper right')

# Pause control
paused = False

def toggle_pause(event):
    global paused
    paused = not paused
    pause_button.label.set_text("Resume" if paused else "Pause")
    fig.canvas.draw_idle()

# Update function for animation
def update(frame):
    global current_time
    if paused:
        return line,

    try:
        while data_queue.qsize() > 0:
            line_str = data_queue.get()
            print(f"Received: {line_str}")  # Debug output
            adc = int(line_str)  # Parse raw ADC value
            if 0 <= adc <= 4095:
                voltage = adc * (3.3 / 4095)  # Convert to voltage, no offset
                time_buffer.append(current_time)
                data_buffer.append(voltage)
                current_time += 0.001  # 1ms per sample
    except ValueError as e:
        print(f"Error parsing data: {e}")

    # Update x-axis to show the last 100ms
    if len(time_buffer) > 0:
        ax.set_xlim(max(0, time_buffer[-1] - 0.1), time_buffer[-1])
    line.set_data(list(time_buffer), list(data_buffer))
    return line,

# Animation setup
ani = animation.FuncAnimation(fig, update, interval=10)

# Button functions for scaling
def increase_volt_div(event):
    y_min, y_max = ax.get_ylim()
    ax.set_ylim(y_min * 1.2, y_max * 1.2)
    fig.canvas.draw_idle()

def decrease_volt_div(event):
    y_min, y_max = ax.get_ylim()
    ax.set_ylim(y_min * 0.8, y_max * 0.8)
    fig.canvas.draw_idle()

def increase_time_div(event):
    x_min, x_max = ax.get_xlim()
    ax.set_xlim(x_min, x_max * 1.2)
    fig.canvas.draw_idle()

def decrease_time_div(event):
    x_min, x_max = ax.get_xlim()
    ax.set_xlim(x_min, x_max * 0.8)
    fig.canvas.draw_idle()

# Button positions
btn_width = 0.1
btn_height = 0.05
x_pos = 0.88
spacing = 0.07

btn_ax_pause = plt.axes([x_pos, 0.92, btn_width, btn_height])
btn_ax_vup = plt.axes([x_pos, 0.85, btn_width, btn_height])
btn_ax_vdown = plt.axes([x_pos, 0.78, btn_width, btn_height])
btn_ax_tup = plt.axes([x_pos, 0.71, btn_width, btn_height])
btn_ax_tdown = plt.axes([x_pos, 0.64, btn_width, btn_height])

# Create buttons
pause_button = Button(btn_ax_pause, 'Pause')
pause_button.on_clicked(toggle_pause)
vup_button = Button(btn_ax_vup, '+V/div')
vup_button.on_clicked(increase_volt_div)
vdown_button = Button(btn_ax_vdown, '-V/div')
vdown_button.on_clicked(decrease_volt_div)
tup_button = Button(btn_ax_tup, '+T/div')
tup_button.on_clicked(increase_time_div)
tdown_button = Button(btn_ax_tdown, '-T/div')
tdown_button.on_clicked(decrease_time_div)

# Style buttons
buttons = [pause_button, vup_button, vdown_button, tup_button, tdown_button]
for btn in buttons:
    btn.color = 'lime'
    btn.hovercolor = 'yellow'
    btn.label.set_color('black')

plt.subplots_adjust(right=0.85)
plt.show()

# Clean up
ser.close()
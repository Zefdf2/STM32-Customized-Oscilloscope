import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Button
from collections import deque
import threading
import queue

# Serial port configuration
PORT = '/dev/tty.usbmodem102'  # Your specified port
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
data_buffer1 = deque(maxlen=MAX_POINTS)
data_buffer2 = deque(maxlen=MAX_POINTS)
diff_buffer = deque(maxlen=MAX_POINTS)
current_time = 0  # Time in seconds

# Set up dark oscilloscope-style theme with three subplots
plt.style.use('dark_background')
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 9), facecolor='black', sharex=True)
fig.subplots_adjust(hspace=0.4, right=0.85)

# Configure Signal 1 plot
ax1.set_facecolor('black')
ax1.set_ylim(-1.5, 1.5)  # For -1V to +1V
ax1.set_ylabel('Signal 1 (V)', color='white')
ax1.set_title('Signal 1 (ADC1)', color='white')
ax1.axhline(0, color='gray', linewidth=0.8, linestyle='--')
ax1.grid(True, color='gray', linestyle='--', linewidth=0.5)
ax1.tick_params(axis='both', colors='white')
line1, = ax1.plot([], [], color='lime', label='Signal 1')
ax1.legend(loc='upper right')

# Configure Signal 2 plot
ax2.set_facecolor('black')
ax2.set_ylim(-1.5, 1.5)  # For -1V to +1V
ax2.set_ylabel('Signal 2 (V)', color='white')
ax2.set_title('Signal 2 (ADC2)', color='white')
ax2.axhline(0, color='gray', linewidth=0.8, linestyle='--')
ax2.grid(True, color='gray', linestyle='--', linewidth=0.5)
ax2.tick_params(axis='both', colors='white')
line2, = ax2.plot([], [], color='cyan', label='Signal 2')
ax2.legend(loc='upper right')

# Configure Difference plot
ax3.set_facecolor('black')
ax3.set_ylim(-2.5, 2.5)  # Difference can range from -2V to +2V
ax3.set_xlim(0, 0.1)  # 100ms window
ax3.set_xlabel('Time (s)', color='white')
ax3.set_ylabel('Difference (V)', color='white')
ax3.set_title('Signal 1 - Signal 2', color='white')
ax3.axhline(0, color='gray', linewidth=0.8, linestyle='--')
ax3.grid(True, color='gray', linestyle='--', linewidth=0.5)
ax3.tick_params(axis='both', colors='white')
line3, = ax3.plot([], [], color='yellow', label='Difference')
ax3.legend(loc='upper right')

# Pause control
paused = False

def toggle_pause(event):
    global paused
    paused = not paused
    pause_button.label.set_text("Resume" if paused else "Pause")
    fig.canvas.draw_idle()

# Update function
def update(frame):
    global current_time
    if paused:
        return line1, line2, line3

    try:
        while data_queue.qsize() >= 2:
            # Read two lines for ADC1 and ADC2
            line1_str = data_queue.get()  # e.g., "Received: 1234"
            line2_str = data_queue.get()  # e.g., "Received: 5678"
            print(f"Received: {line1_str}, {line2_str}")  # Debug print
            
            # Extract ADC values from the formatted strings
            adc1_str = line1_str.split(": ")[1]  # Get "1234" from "Received: 1234"
            adc2_str = line2_str.split(": ")[1]  # Get "5678" from "Received: 5678"
            adc1 = int(adc1_str)
            adc2 = int(adc2_str)
            
            if 0 <= adc1 <= 4095 and 0 <= adc2 <= 4095:
                voltage1 = adc1 * (3.3 / 4095) - 1.5  # Adjust for 1.5V offset
                voltage2 = adc2 * (3.3 / 4095) - 1.5
                diff_voltage = voltage1 - voltage2
                time_buffer.append(current_time)
                data_buffer1.append(voltage1)
                data_buffer2.append(voltage2)
                diff_buffer.append(diff_voltage)
                current_time += 0.001  # 1ms per sample
    except (ValueError, IndexError) as e:
        print(f"Error parsing data: {e}")

    # Update x-axis to show last 100ms
    if len(time_buffer) > 0:
        ax3.set_xlim(max(0, time_buffer[-1] - 0.1), time_buffer[-1])
    line1.set_data(list(time_buffer), list(data_buffer1))
    line2.set_data(list(time_buffer), list(data_buffer2))
    line3.set_data(list(time_buffer), list(diff_buffer))
    return line1, line2, line3

# Animation setup
ani = animation.FuncAnimation(fig, update, interval=10)

# Button functions
def increase_volt_div(event):
    for ax in [ax1, ax2, ax3]:
        y_min, y_max = ax.get_ylim()
        ax.set_ylim(y_min * 1.2, y_max * 1.2)
    fig.canvas.draw_idle()

def decrease_volt_div(event):
    for ax in [ax1, ax2, ax3]:
        y_min, y_max = ax.get_ylim()
        ax.set_ylim(y_min * 0.8, y_max * 0.8)
    fig.canvas.draw_idle()

def increase_time_div(event):
    x_min, x_max = ax3.get_xlim()
    ax3.set_xlim(x_min, x_max * 1.2)
    fig.canvas.draw_idle()

def decrease_time_div(event):
    x_min, x_max = ax3.get_xlim()
    ax3.set_xlim(x_min, x_max * 0.8)
    fig.canvas.draw_idle()

# Create button positions
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

plt.show()

# Clean up
ser.close()
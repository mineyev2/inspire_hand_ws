"""
Interactive keyboard control for left hand fingers.
Joint order: [pinky, ring, middle, index, thumb-bend, thumb-rotation]

Controls:
- 1/q: Pinky up/down
- 2/w: Ring up/down
- 3/e: Middle up/down
- 4/r: Index up/down
- 5/t: Thumb-bend up/down
- 6/y: Thumb-rotation up/down
- ESC: Exit

Real-time control: Commands are sent immediately when you press keys!
"""

import sys
from inspire_sdkpy import inspire_sdk, inspire_hand_defaut
import time
import tty
import termios
import select

def get_key():
    """Get a single keypress without waiting for Enter."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        # Check if input is available (non-blocking)
        if select.select([sys.stdin], [], [], 0.01)[0]:
            ch = sys.stdin.read(1)
            # Handle ESC sequences
            if ch == '\x1b':
                # Read potential additional characters for arrow keys etc
                if select.select([sys.stdin], [], [], 0.01)[0]:
                    ch += sys.stdin.read(2)
            return ch
        return None
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def command_hand_to_angles(handler, angles, device_id=1):
    """
    Command the hand to move to specified angles.
    
    Args:
        handler: ModbusDataHandler instance
        angles: List of 6 angles (int16) for each joint [pinky, ring, middle, index, thumb-bend, thumb-rotation]
        device_id: Device ID (default: 1)
    """
    if len(angles) != 6:
        return False
    
    try:
        # Clamp angles to 0-1000 range
        clamped_angles = [max(0, min(1000, angle)) for angle in angles]
        
        # Write angle commands to register 1486 (angle_set register)
        handler.client.write_registers(1486, clamped_angles, device_id)
        return True
    except Exception as e:
        print(f"\nError writing angles: {e}")
        return False

def read_current_angles(handler, device_id=1):
    """
    Read current angle positions from the hand.
    
    Args:
        handler: ModbusDataHandler instance
        device_id: Device ID (default: 1)
    
    Returns:
        List of current angles or None on error
    """
    try:
        data_dict = handler.read()
        if data_dict and 'states' in data_dict:
            return data_dict['states']['ANGLE_ACT']
        return None
    except Exception as e:
        return None

def print_status(target_angles, current_angles, joint_names):
    """Print current status of all joints."""
    print("\r" + " " * 120 + "\r", end="")  # Clear line
    status = "Target: "
    for i, (name, target) in enumerate(zip(joint_names, target_angles)):
        current = current_angles[i] if current_angles else "?"
        status += f"{name}:{target:4d} "
    print(status, end="", flush=True)

if __name__ == "__main__":
    # Initialize handler for left hand
    print("Initializing left hand connection...")
    handler = inspire_sdk.ModbusDataHandler(ip='192.168.123.211', LR='l', device_id=1)
    time.sleep(0.5)
    
    # Joint names for display
    joint_names = ["Pinky", "Ring", "Middle", "Index", "ThumbB", "ThumbR"]
    
    # Initialize target angles to current positions
    print("Reading initial angles...")
    current_angles = read_current_angles(handler, device_id=1)
    if current_angles:
        target_angles = [int(max(0, min(1000, angle))) for angle in current_angles]
    else:
        target_angles = [0, 0, 0, 0, 0, 0]
    
    # Increment/decrement step size
    step = 10
    
    print("\n" + "="*80)
    print("KEYBOARD CONTROL MODE")
    print("="*80)
    print("Controls:")
    print("  1/q: Pinky up/down     2/w: Ring up/down       3/e: Middle up/down")
    print("  4/r: Index up/down     5/t: Thumb-bend up/down 6/y: Thumb-rotation up/down")
    print("  ESC: Exit")
    print("\nReal-time control: Commands are sent immediately!")
    print("="*80)
    
    try:
        while True:
            # Get keyboard input
            key = get_key()
            
            if key:
                # Handle ESC (exit)
                if key == '\x1b' or key.startswith('\x1b'):
                    print("\n\nExiting...")
                    break
                
                updated = False
                
                # Handle number keys (increase angles)
                if key == '1':
                    target_angles[0] = min(1000, target_angles[0] + step)
                    updated = True
                elif key == '2':
                    target_angles[1] = min(1000, target_angles[1] + step)
                    updated = True
                elif key == '3':
                    target_angles[2] = min(1000, target_angles[2] + step)
                    updated = True
                elif key == '4':
                    target_angles[3] = min(1000, target_angles[3] + step)
                    updated = True
                elif key == '5':
                    target_angles[4] = min(1000, target_angles[4] + step)
                    updated = True
                elif key == '6':
                    target_angles[5] = min(1000, target_angles[5] + step)
                    updated = True
                
                # Handle letter keys (decrease angles)
                elif key == 'q':
                    target_angles[0] = max(0, target_angles[0] - step)
                    updated = True
                elif key == 'w':
                    target_angles[1] = max(0, target_angles[1] - step)
                    updated = True
                elif key == 'e':
                    target_angles[2] = max(0, target_angles[2] - step)
                    updated = True
                elif key == 'r':
                    target_angles[3] = max(0, target_angles[3] - step)
                    updated = True
                elif key == 't':
                    target_angles[4] = max(0, target_angles[4] - step)
                    updated = True
                elif key == 'y':
                    target_angles[5] = max(0, target_angles[5] - step)
                    updated = True
                
                if updated:
                    # Send command immediately for real-time control
                    command_hand_to_angles(handler, target_angles, device_id=1)
                    # Read current angles from hand
                    current_angles = read_current_angles(handler, device_id=1)
                    print_status(target_angles, current_angles, joint_names)
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
    
    print("\nDone!")

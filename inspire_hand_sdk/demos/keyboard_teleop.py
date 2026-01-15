#!/usr/bin/env python3
"""
Keyboard Teleoperation for Inspire Hands
Controls both Left and Right hands simultaneously using InspireHandController.
Uses set_angle (position control) instead of set_velocity.
"""

import sys
import os
import time
import termios
import tty
import select
from unitree_sdk2py.core.channel import ChannelFactoryInitialize

# Add the parent directory to sys.path to allow importing from core
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

try:
    from core.hand_controller import InspireHandController
except ImportError:
    print("Error: Could not import InspireHandController from core.")
    print(f"Added path: {parent_dir}")
    print("Please ensure your directory structure is correct.")
    sys.exit(1)

# Key mappings
# 1-6 for "up" (positive angle change), q-y for "down" (negative angle change)
# Order: Pinky, Ring, Middle, Index, Thumb-Bend, Thumb-Rotate
KEY_MAPPING = {
    '1': (0, 1),   # Pinky Up
    '2': (1, 1),   # Ring Up
    '3': (2, 1),   # Middle Up
    '4': (3, 1),   # Index Up
    '5': (4, 1),   # Thumb Bend Up
    '6': (5, 1),   # Thumb Rotate Up
    'q': (0, -1),  # Pinky Down
    'w': (1, -1),  # Ring Down
    'e': (2, -1),  # Middle Down
    'r': (3, -1),  # Index Down
    't': (4, -1),  # Thumb Bend Down
    'y': (5, -1)   # Thumb Rotate Down
}

# Parameters
MIN_ANGLE = 0
MAX_ANGLE = 1000
ANGLE_STEP = 20  # Amount to change angle per loop iteration (approx 50Hz)

class KeyboardController:
    def __init__(self):
        # Initialize DDS (only once for the process)
        if len(sys.argv) > 1:
            ChannelFactoryInitialize(0, sys.argv[1])
        else:
            ChannelFactoryInitialize(0)
            
        print("Initializing Left Hand...")
        self.hand_l = InspireHandController('l', initialize_dds=False)
        print("Initializing Right Hand...")
        self.hand_r = InspireHandController('r', initialize_dds=False)
        
        self.settings = termios.tcgetattr(sys.stdin)

        # Set Force and Speed limits for all fingers
        print("Setting default Force and Speed (500)...")
        default_limits = [500] * 6
        self.hand_l.set_force(default_limits)
        self.hand_r.set_force(default_limits)
        self.hand_l.set_velocity(default_limits)
        self.hand_r.set_velocity(default_limits)
        
        # Initial angles state
        # Initialize to 1000 (Open/Extended) which is usually the safe default for hands
        # Changing this depends on your specific hand's calibration
        self.current_angles = [1000] * 6
        
        # Send initial position to sync (prevent sudden jump later if hands are at 0)
        # Note: This might cause a jump at startup if hands are not at 1000
        print("Sending initial position (1000)...")
        self.hand_l.set_angle(self.current_angles)
        self.hand_r.set_angle(self.current_angles)

    def get_key(self, timeout=0.1):
        """
        Non-blocking key read from stdin.
        Returns the key character or None if timeout.
        """
        tty.setraw(sys.stdin.fileno())
        rlist, _, _ = select.select([sys.stdin], [], [], timeout)
        if rlist:
            key = sys.stdin.read(1)
        else:
            key = None
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        return key

    def run(self):
        print("\n=== Inspire Hand Keyboard Teleop (Position Control) ===")
        print("Control Scheme:")
        print("  1-6 keys: Increase Angle (Move 'Up')")
        print("  q-y keys: Decrease Angle (Move 'Down')")
        print("  Hold key to move continuously.")
        print("  Ctrl+C: Exit")
        print("======================================================")

        try:
            while True:
                # Poll frequently (20ms) -> 50Hz
                key = self.get_key(timeout=0.02)
                
                angles_changed = False
                
                if key in KEY_MAPPING:
                    finger_idx, direction = KEY_MAPPING[key]
                    
                    # Update angle
                    current_val = self.current_angles[finger_idx]
                    new_val = current_val + (direction * ANGLE_STEP)
                    
                    # Clip to limits
                    new_val = max(MIN_ANGLE, min(MAX_ANGLE, new_val))
                    
                    if new_val != current_val:
                        self.current_angles[finger_idx] = int(new_val)
                        angles_changed = True
                        
                        # User Feedback
                        finger_names = ["Pinky", "Ring", "Middle", "Index", "Thumb-Bend", "Thumb-Rotate"]
                        msg = f"\rFinger: {finger_names[finger_idx]} | Angle: {self.current_angles[finger_idx]}   "
                        sys.stdout.write(msg)
                        sys.stdout.flush()
                
                elif key == '\x03': # Ctrl+C
                    break
                
                # If angles changed (or maybe periodically?), send command
                # Sending only on change is efficient, but sending continuously while key held is safer
                if angles_changed:
                    self.hand_l.set_angle(self.current_angles)
                    self.hand_r.set_angle(self.current_angles)
                    
        except KeyboardInterrupt:
            pass
        finally:
            print("\nExiting...")
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)

if __name__ == "__main__":
    controller = KeyboardController()
    controller.run()

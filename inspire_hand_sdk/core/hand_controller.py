"""
High-level controller interface for Inspire robotic hand.

This module provides a clean, intuitive API for controlling the Inspire hand
without needing to deal with DDS messages and binary mode flags directly.
"""

from inspire_sdkpy.inspire_dds import inspire_hand_ctrl
from inspire_sdkpy.inspire_hand_defaut import get_inspire_hand_ctrl
from unitree_sdk2py.core.channel import ChannelPublisher, ChannelFactoryInitialize


class InspireHandController:
    """
    High-level controller for Inspire robotic hand.
    
    This class provides a simplified interface for controlling the hand through
    DDS messaging, abstracting away the low-level details of mode flags and
    message construction.
    
    Example:
        >>> hand = InspireHandController('l')  # Left hand
        >>> hand.set_angle([100, 200, 300, 400, 500, 600])
        >>> hand.set_velocity([50, 50, 50, 50, 50, 50])
    """
    
    def __init__(self, hand_side='l', network=None, initialize_dds=True):
        """
        Initialize controller for left or right hand.
        
        Args:
            hand_side (str): 'l' for left hand, 'r' for right hand. Defaults to 'l'.
            network (str, optional): Network interface name for DDS. Defaults to None.
            initialize_dds (bool): Whether to initialize DDS factory. Set to False if
                                  already initialized elsewhere. Defaults to True.
        """
        if hand_side not in ['l', 'r']:
            raise ValueError("hand_side must be 'l' (left) or 'r' (right)")
        
        self.hand_side = hand_side
        
        # Initialize DDS if requested
        if initialize_dds:
            if network is None:
                ChannelFactoryInitialize(0)
            else:
                ChannelFactoryInitialize(0, network)
        
        # Create publisher for control commands
        self.pub = ChannelPublisher(f"rt/inspire_hand/ctrl/{hand_side}", inspire_hand_ctrl)
        self.pub.Init()
    
    def _send_command(self, mode, **kwargs):
        """
        Internal method to create and send a command.
        
        Args:
            mode (int): Binary mode flags
            **kwargs: Command fields to set (angle_set, pos_set, force_set, speed_set)
        
        Returns:
            bool: True if message was sent successfully
        """
        cmd = get_inspire_hand_ctrl()
        cmd.mode = mode
        
        for key, value in kwargs.items():
            setattr(cmd, key, value)
        
        return self.pub.Write(cmd)
    
    def set_angle(self, angles):
        """
        Set joint angles.
        
        Args:
            angles (list): List of 6 angle values for joints in order:
                          [pinky, ring, middle, index, thumb-bend, thumb-rotation]
        
        Returns:
            bool: True if command was sent successfully
        
        Example:
            >>> hand.set_angle([0, 0, 0, 0, 1000, 1000])
        """
        if len(angles) != 6:
            raise ValueError("angles must be a list of 6 values")
        return self._send_command(0b0001, angle_set=angles)
    
    def set_position(self, positions):
        """
        Set joint positions.
        
        Args:
            positions (list): List of 6 position values for joints in order:
                             [pinky, ring, middle, index, thumb-bend, thumb-rotation]
        
        Returns:
            bool: True if command was sent successfully
        
        Example:
            >>> hand.set_position([500, 500, 500, 500, 500, 500])
        """
        if len(positions) != 6:
            raise ValueError("positions must be a list of 6 values")
        return self._send_command(0b0010, pos_set=positions)
    
    def set_force(self, forces):
        """
        Set force control values.
        
        Args:
            forces (list): List of 6 force values for joints in order:
                          [pinky, ring, middle, index, thumb-bend, thumb-rotation]
        
        Returns:
            bool: True if command was sent successfully
        
        Example:
            >>> hand.set_force([100, 100, 100, 100, 100, 100])
        """
        if len(forces) != 6:
            raise ValueError("forces must be a list of 6 values")
        return self._send_command(0b0100, force_set=forces)
    
    def set_velocity(self, velocities):
        """
        Set joint velocities (speed).
        
        Args:
            velocities (list): List of 6 velocity values for joints in order:
                              [pinky, ring, middle, index, thumb-bend, thumb-rotation]
        
        Returns:
            bool: True if command was sent successfully
        
        Example:
            >>> hand.set_velocity([50, 50, 50, 50, 50, 50])
        """
        if len(velocities) != 6:
            raise ValueError("velocities must be a list of 6 values")
        return self._send_command(0b1000, speed_set=velocities)
    
    def set_angle_and_position(self, angles, positions):
        """
        Set both angles and positions simultaneously.
        
        Args:
            angles (list): List of 6 angle values
            positions (list): List of 6 position values
        
        Returns:
            bool: True if command was sent successfully
        """
        if len(angles) != 6 or len(positions) != 6:
            raise ValueError("angles and positions must each be lists of 6 values")
        return self._send_command(0b0011, angle_set=angles, pos_set=positions)
    
    def set_angle_and_velocity(self, angles, velocities):
        """
        Set both angles and velocities simultaneously.
        
        Args:
            angles (list): List of 6 angle values
            velocities (list): List of 6 velocity values
        
        Returns:
            bool: True if command was sent successfully
        """
        if len(angles) != 6 or len(velocities) != 6:
            raise ValueError("angles and velocities must each be lists of 6 values")
        return self._send_command(0b1001, angle_set=angles, speed_set=velocities)
    
    def stop(self):
        """
        Send a no-operation command (mode 0).
        
        Returns:
            bool: True if command was sent successfully
        """
        return self._send_command(0b0000)
    
    def __repr__(self):
        """String representation of the controller."""
        side = "Left" if self.hand_side == 'l' else "Right"
        return f"InspireHandController({side} Hand)"

import cv2
import numpy as np
import pyautogui
import time
import os
from datetime import datetime

def record_screen():
    # Get screen size
    SCREEN_SIZE = tuple(pyautogui.size())
    
    # Define the codec
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    
    # Output file
    filename = f"demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    fps = 20.0
    
    # Create video writer
    out = cv2.VideoWriter(filename, fourcc, fps, SCREEN_SIZE)
    
    print(f"Recording... Press 'q' to stop")
    
    while True:
        # Get screen content
        img = pyautogui.screenshot()
        frame = np.array(img)
        
        # Convert from BGR to RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Write frame
        out.write(frame)
        
        # Check if user wants to stop
        if cv2.waitKey(1) == ord('q'):
            break
    
    # Release everything
    out.release()
    cv2.destroyAllWindows()
    
    print(f"Video saved as {filename}")

if __name__ == "__main__":
    # Wait a few seconds before starting
    print("Starting recording in 3 seconds...")
    time.sleep(3)
    record_screen()

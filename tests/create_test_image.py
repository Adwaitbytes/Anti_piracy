import numpy as np
import cv2

# Create a 640x480 image with a gradient background
width, height = 640, 480
image = np.zeros((height, width, 3), dtype=np.uint8)

# Create gradient background
for y in range(height):
    for x in range(width):
        image[y, x] = [
            int(255 * (x / width)),
            int(255 * (y / height)),
            int(255 * ((x + y) / (width + height)))
        ]

# Add some text
font = cv2.FONT_HERSHEY_SIMPLEX
cv2.putText(image, 'SecureStream Test Image', (50, 50), font, 1, (255, 255, 255), 2)
cv2.putText(image, 'Copyright 2025', (50, 100), font, 1, (255, 255, 255), 2)

# Save the image
cv2.imwrite('test_image.png', image)
print("Test image created: test_image.png")

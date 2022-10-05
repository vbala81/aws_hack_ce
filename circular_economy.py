# Python program that uses rasp pi camera and AWS Rekogition to detect an image and alert
# if a recyclable object is detected

from picamera import PiCamera
import cv2 as cv
import argparse
import boto3
import time
import os
import sys
import json
from gpiozero import LED
from gpiozero import MotionSensor
import RPi.GPIO as GPIO
Bucket = "hackathon-ce-bucket"

GPIO.setmode(GPIO.BOARD)  # Set GPIO to pin numbering
pir = 8  # Assign pin 8 to PIR
led = 10  # Assign pin 10 to LED
GPIO.setup(pir, GPIO.IN)  # Setup GPIO pin PIR as input
print("Sensor initializing . . .")
time.sleep(2)  # Give sensor time to startup
print("Active")
print("Press Ctrl+c to end program")


def detect_motion():
    """Method that detects motion
    """
    try:
        while True:
            gpio_input = GPIO.input(pir)
            if (gpio_input == 1):  # If PIR pin goes high, motion is detected
                print("Motion Detected!")
                # GPIO.output(led, True)  # Turn on LED
                # time.sleep(4)  # Keep LED on for 4 seconds
                # GPIO.output(led, False)  # Turn off LED
                # time.sleep(0.1)
                main()

    except KeyboardInterrupt:
        print("Keyboard interrupted ")
    finally:
        GPIO.output(led, False)  # Turn off LED in case left on
        GPIO.cleanup()  # reset all GPIO
        print("Program ended")

def pushImagetoS3(image):
    """ Method that pushes the image to S3 and alerts through a lambda
            if it detects a recyclable object
        Args:
            image           : Local image from raspberry pi
        Raises:
            Exception(e) : General Exception when something fails during the process
    """
    try:
        upload_status = ''
        s3_client = boto3.client('s3')
        S3_KEY = 'images/'
        with open(image, 'rb') as data:
            upload_status = s3_client.upload_fileobj(data, Bucket, S3_KEY + image)
        os.remove(image)
    except Exception as excep:
        print('Exception in rekogniseface process {}' .format(sys.exc_info()))
        raise excep
    return upload_status

def storeImage(frame):	
    """ Method that stores the image in rasp pi in a folder based on frame that is sent through opencv
        Args:
            frame   : opencv identified image frame
        Raises:
            Exception(e) : General Exception when something fails during the process
    """
    try: 
        timestr = time.strftime("%Y%m%d-%H%M%S")
        image = '{0}/image_{1}.png'.format(directory, timestr)
        cv.imwrite(image, frame)
        # print('Your image was saved to %s' %image) 
    except Exception as excep:
        print('Exception in storeImage process {}' .format(sys.exc_info()))
        raise excep
    return image

def main():	
    """ Main method that orchestrates all the steps
    """
    # get args
    parser = argparse.ArgumentParser(description='Object recognition')
    parser.add_argument('--camera', help='Camera device number.', type=int, default=0)
    args = parser.parse_args()
    print('Start image capture')
    camera_device = args.camera

    # Read the video stream
    cam = cv.VideoCapture(camera_device)
    # setting the buffer size and frames per second, to reduce frames in buffer
    cam.set(cv.CAP_PROP_BUFFERSIZE, 1)
    cam.set(cv.CAP_PROP_FPS, 2)

    if not cam.isOpened:
        print('--(!)Error opening video capture')
        exit(0)
    print('New Object getting pushed to S3')
    # initialize reckognition sdk
    frame = {}
    # calling read() twice as a workaround to clear the buffer.
    cam.read()
    cam.read()
    success, frame = cam.read()
    if not success:
        sys.exit(
            'ERROR: Unable to read from webcam. Please verify your webcam settings.'
        )        
    image = storeImage(frame)
    if image is not None:
        pushImagetoS3(image)

    # When everything done, release the capture
    cam.release()
    cv.destroyAllWindows()

dirname = os.path.dirname(__file__)
directory = os.path.join(dirname, 'objects')
detect_motion()

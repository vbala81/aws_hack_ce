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
Bucket = "hackathon-ce-bucket"

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
        print(directory)
        image = '{0}/image_{1}.png'.format(directory, timestr)
        cv.imwrite(image, frame)
        # print('Your image was saved to %s' %image) 
    except Exception as excep:
        print('Exception in storeImage process {}' .format(sys.exc_info()))
        raise excep
    return image

def detect_motion():
    """Method that detects motion
    """
    green_led = LED(17)
    pir = MotionSensor(4)
    green_led.off()
    while True:
        pir.wait_for_motion()
        print("Motion Detected")
        green_led.on()
        pir.wait_for_no_motion()
        print("No Motion")
        green_led.off()

def main():	
    """ Main method that orchestrates all the steps
    """
    # get args
    parser = argparse.ArgumentParser(description='Object recognition')
    parser.add_argument('--camera', help='Camera device number.', type=int, default=0)
    args = parser.parse_args()

    camera_device = args.camera

    # Read the video stream
    cam = cv.VideoCapture(camera_device)
    # setting the buffer size and frames per second, to reduce frames in buffer
    cam.set(cv.CAP_PROP_BUFFERSIZE, 1)
    cam.set(cv.CAP_PROP_FPS, 2)

    if not cam.isOpened:
        print('--(!)Error opening video capture')
        exit(0)

    # initialize reckognition sdk
    while True:
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

        if cv.waitKey(20) & 0xFF == ord('q'):
            break

    # When everything done, release the capture
    cam.release()
    cv.destroyAllWindows()

dirname = os.path.dirname(__file__)
directory = os.path.join(dirname, 'objects')
detect_motion()

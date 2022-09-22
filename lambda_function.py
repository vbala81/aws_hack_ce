import datetime
import time
import boto3 
from botocore.exceptions import ClientError
import urllib.parse

#GLOBAL VARIABLES
s3_bucket_name = 'hackathon-ce-bucket'

def get_event_date(event):
    if "timestamp" in event[0]:
        mytimestamp = datetime.datetime.fromtimestamp(event[0]["timestamp"])
    else:
        mytimestamp = datetime.datetime.fromtimestamp(time.time())
    return mytimestamp.strftime("%Y%m%d")

def lambda_handler(event, context):
    # print("Received event: " + json.dumps(event, indent=2))
    rekognition_client = boto3.client('rekognition')
    # Get the object from the event and show its content type
    image = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    print("Image is ")
    print(image)
    try:
        response = rekognition_client.detect_labels(
            Image={
                    "S3Object": {
                        "Bucket": s3_bucket_name,
                        "Name": image
                    }
            },
            MinConfidence=70)
        print(response)
        
        labels = response["Labels"]
        organic_waste = 0
        hazardous_waste = 0
        recyclable_paper = 0
        recyclable_clothing = 0
        recyclable_cans = 0
        other_waste = 0
        organic_waste_dict = [
            "orange", "bread", "banana", "orange peel", "apple", "onion", "vegatable", "potato"
        ]
        recyclable_paper_dict = [
            "cardboard", "plastic", "paper", "bottle", "polethene", "paper ball"
        ]
        recyclable_clothing_dict = [
            "jeans", "pants", "shirts", "shoes", "sneakers", "socks"
        ]
        recyclable_cans_dict = [
            "can", "bottle", "soda"
        ]
        hazardous_waste_dict = ["batteries"]
        
        for label in labels:
            if label["Name"].lower() in organic_waste_dict:
                organic_waste += 1
            elif label["Name"].lower() in hazardous_waste_dict:
                hazardous_waste += 1
            elif label["Name"].lower() in recyclable_paper_dict:
                recyclable_paper += 1
            elif label["Name"].lower() in recyclable_clothing_dict:
                recyclable_clothing += 1
            elif label["Name"].lower() in recyclable_cans_dict:
                recyclable_cans += 1
            else:
                other_waste += 1

        print('Organic Waste Item Count: ', organic_waste)
        print('Hazardous Waste Item Count: ', hazardous_waste)
        print('Recyclable Paper Item Count: ', recyclable_paper)
        print('Recyclable Clothing Item Count: ', recyclable_clothing)
        print("Recyclable Canned Item Count: ", recyclable_cans)
        
        return True
    except ClientError as e:
        print(e)
        raise e
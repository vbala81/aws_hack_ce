import boto3 
from botocore.exceptions import ClientError
import urllib.parse
import sys
import rds_config
import pymysql
from datetime import datetime

#GLOBAL VARIABLES
BUCKET = 'hackathon-ce-bucket'
FEATURES_BLACKLIST = ["Landmarks", "Emotions", "Pose", "Quality", "BoundingBox"]

rds_host = 'iot-test.chfqqrhe8otz.us-east-1.rds.amazonaws.com'
name = rds_config.db_username
password = rds_config.db_password
db_name = rds_config.db_name

#SETUP DATABASE CONNECTIVITY
try:
    conn = pymysql.connect(host=rds_host, user=name, passwd=password, db=db_name, connect_timeout=5)
    print('Connection to RDS MySQL instance succeeded.')
except pymysql.MySQLError as e:
    print("ERROR: Unexpected error: Could not connect to MySQL instance.")
    print(e)
    sys.exit()

def detect_labels(bucket, key, max_labels=10, min_confidence=90, region="us-east-1"):
    rekognition_client = boto3.client('rekognition', region)
    try:
        response = rekognition_client.detect_labels(
            Image={
                    "S3Object": {
                        "Bucket": bucket,
                        "Name": key
                    }
            },
            MaxLabels=max_labels,
            MinConfidence=min_confidence)
        return response['Labels']
    except ClientError as e:
        print(e)
        raise e

def lambda_handler(event, context):
    # Get the object from the event and show its content type
    image = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    print("Image is ")
    print(image)
    """
    Item                                    Unit       Emissions that could be saved by recycling           Energy that could be saved                              Water that could be saved
    PET Plastic Water or Soda Bottle        1 bottle            24.84 g CO2 equivalent                              5774 Kwh                                    
    Paper source                            1 ton               1000 kg Co2 equivalent           enough to power avg American home for 6 months                     7000 gallons (26,000 liters)
    Aluminum Cans                           12 cans             1.18 kg Co2 equivalent   save enough energy to power a typical passenger car for more than 3 miles    
    Cardboard                               1 ton               403.5 kg CO2                every ton recycled saved enough energy to fuel 1000 miles driven in a car      7000 tons of water
    """
    
    bottles_dict = ["water", "bottle", "plastic bottle", "mineral water"]
    bottles_id = '1'
    cans_dict = ["can", "cans", "soda", "soda can", "aluminum can"]
    cans_id = '2'
    paper_dict = ["paper", "polyethene", "coffee cup"]
    paper_id = '3'
    cardboard_dict = ["cardboard"]
    cardboard_id = '4'

    batteries_dict = ["batteries"]
    batteries_id = '5'

    bottles = 0
    paper = 0
    cans = 0
    cardboard = 0
    batteries = 0
    other_waste = 0

    #Timestamp
    ts = datetime.now().isoformat(timespec='seconds')

    cursor = conn.cursor()
    cursor.execute('use IOT') #Name of database where objects live
    #Persist into "Waste_collection"
    for label in detect_labels(BUCKET, image):
        print(label)
        print("{Name} - {Confidence}%".format(**label))
                
        if label["Name"].lower() in batteries_dict:
            batteries += 1
        elif label["Name"].lower() in bottles_dict:
            print('Item analyzed to be a bottle.')
            params = (ts, bottles_id)
            bottles += 1
        elif label["Name"].lower() in paper_dict:
            print('Item analyzed to be paper.')
            params = (ts, paper_id)
            paper += 1
        elif label["Name"].lower() in cans_dict:
            print('Item analyzed to be a can.')
            params = (ts, cans_id)
            cans += 1
        elif label["Name"].lower() in cardboard_dict:
            print('Item analyzed to be cardboard.')
            params = (ts, cardboard_id)
            cardboard += 1
        else:
            other_waste += 1
            
    insert = 'INSERT INTO Waste_collection (TIME_STAMP, OBJECT_ID) VALUES (%s, %s)'
    cursor.execute(insert, params)

    # print('Hazardous Waste Item Count: ', batteries_dict)
    print("Recyclable Bottles Item Count: ", bottles)
    print('Recyclable Paper Item Count: ', paper)
    print("Recyclable Canned Item Count: ", cans)
    print("Recyclable Cardboard Item Count: ", cardboard)
    
    conn.commit() #Persist to db and close connection
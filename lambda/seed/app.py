import boto3
import cfnresponse
import os

def handler(event, context):
    try:
        if event['RequestType'] == 'Create' or event['RequestType'] == 'Update':
            # Initialize DynamoDB client
            dynamodb = boto3.resource('dynamodb')
            
            # Seed customers table
            customers_table = dynamodb.Table(os.environ['CUSTOMERS_TABLE'])
            customers = [
                {
                    "id": "cust_001",
                    "name": "Jane Smith",
                    "service_level": "basic",
                    "devices": [
                        {
                            "id": "dev_001",
                            "type": "SmartSpeaker",
                            "location": "living_room"
                        }
                    ]
                },
                {
                    "id": "cust_002",
                    "name": "John Doe",
                    "service_level": "premium",
                    "devices": [
                        {
                            "id": "dev_002",
                            "type": "SmartSpeaker",
                            "location": "bedroom"
                        },
                        {
                            "id": "dev_003",
                            "type": "SmartDisplay",
                            "location": "kitchen"
                        }
                    ]
                },
                {
                    "id": "cust_003",
                    "name": "Alice Johnson",
                    "service_level": "enterprise",
                    "devices": [
                        {
                            "id": "dev_004",
                            "type": "SmartSpeaker",
                            "location": "office"
                        },
                        {
                            "id": "dev_005",
                            "type": "SmartDisplay",
                            "location": "conference_room"
                        },
                        {
                            "id": "dev_006",
                            "type": "SmartHub",
                            "location": "reception"
                        }
                    ]
                }
            ]
            
            for customer in customers:
                customers_table.put_item(Item=customer)
            
            # Seed service levels table
            service_levels_table = dynamodb.Table(os.environ['SERVICE_LEVELS_TABLE'])
            service_levels = [
                {
                    "level": "basic",
                    "allowed_actions": [
                        "device_status",
                        "device_power"
                    ],
                    "max_devices": 1,
                    "support_priority": "standard"
                },
                {
                    "level": "premium",
                    "allowed_actions": [
                        "device_status",
                        "device_power",
                        "volume_control"
                    ],
                    "max_devices": 1,
                    "support_priority": "priority"
                },
                {
                    "level": "enterprise",
                    "allowed_actions": [
                        "device_status",
                        "device_power",
                        "volume_control",
                        "song_changes"
                    ],
                    "max_devices": 1,
                    "support_priority": "dedicated"
                }
            ]
            
            for service_level in service_levels:
                service_levels_table.put_item(Item=service_level)
                
            cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
        elif event['RequestType'] == 'Delete':
            # Nothing to do on delete
            cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
        else:
            cfnresponse.send(event, context, cfnresponse.FAILED, {})
    except Exception as e:
        print(f"Error: {str(e)}")
        cfnresponse.send(event, context, cfnresponse.FAILED, {"Error": str(e)}) 
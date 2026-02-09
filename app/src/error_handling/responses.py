import json


def success_response(data,status_code=200):
    return {
        "statusCode": status_code,
        "headers": {    
            "Content-Type": "application/json"
        },
        "body": json.dumps(data, default=str),
        "isBase64Encoded": False
    }

def error_response(message, status_code):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps({"error": message}, default=str),
        "isBase64Encoded": False
    }

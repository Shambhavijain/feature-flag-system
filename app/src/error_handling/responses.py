import json

def success_response(data,status_code=200):
    return {
        "statusCode": status_code,
        "body": json.dumps(data)
    }

def error_response(message, status_code):
    return {
        "statusCode": status_code,
        "body": json.dumps({"error": message})
    }

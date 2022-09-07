import json
import uuid
import boto3
import hashlib

def calculate_s3_etag(file_path, chunk_size=8 * 1024 * 1024):
    md5s = []

    with open(file_path, 'rb') as fp:
        while True:
            data = fp.read(chunk_size)
            if not data:
                break
            md5s.append(hashlib.md5(data))

    if len(md5s) < 1:
        return '"{}"'.format(hashlib.md5().hexdigest())

    if len(md5s) == 1:
        return '"{}"'.format(md5s[0].hexdigest())

    digests = b''.join(m.digest() for m in md5s)
    digests_md5 = hashlib.md5(digests)
    return '"{}-{}"'.format(digests_md5.hexdigest(), len(md5s))


def lambda_handler(event, context):
    """Sample pure Lambda function

    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict

        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """
    print(event)
    event_str = event['Records'][0]['body']
    stud_obj = json.loads(event_str)
    stud_obj = json.loads(stud_obj['Message'])

    try:
        s3_object = stud_obj['Records'][0]['s3']['object']
    except:
        return None
    s3_object = stud_obj['Records'][0]['s3']['object']
    s3_obj_key = stud_obj['Records'][0]['s3']['object']['key']
    s3_bucket = stud_obj['Records'][0]['s3']['bucket']['name']
    etag = stud_obj['Records'][0]['s3']['object']['eTag']

    segments = s3_object['key'].lstrip('processed/').split('.')[0].split('_')
    skus = segments[0]
    catalog = segments[1]
    types = segments[2]
    original_filename = s3_object['key'].lstrip('processed/')
    client = boto3.resource('dynamodb')
    s3_client = boto3.client('s3')
    s3_response_object = s3_client.get_object(Bucket=s3_bucket, Key=s3_obj_key)
    image_index = client.Table('GumpsImages')
    unique_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, etag))
    image_index.put_item(Item= {'unique_index': unique_id,'sku':  skus, 
                                'catalog':catalog, 'types': types, 'original_filename':original_filename, 'bucket': s3_bucket, 'object': s3_object})

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": "hello world",
            }
        ),
    }

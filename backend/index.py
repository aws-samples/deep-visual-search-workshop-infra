import base64
import json
from os import environ

import boto3
import requests
from urllib.parse import urlparse
from io import BytesIO

from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

# Global variables that are reused
sm_runtime_client = boto3.client('sagemaker-runtime')
s3_client = boto3.client('s3')


def get_features(sm_runtime_client, sagemaker_endpoint, img_bytes):
    response = sm_runtime_client.invoke_endpoint(
        EndpointName=sagemaker_endpoint,
        ContentType='application/x-image',
        Body=img_bytes)
    response_body = json.loads((response['Body'].read()))
    features = response_body['predictions'][0]

    return features


def get_neighbors(features, es, k_neighbors=3):
    idx_name = 'idx_zalando'
    res = es.search(
        request_timeout=30, index=idx_name,
        body={
            'size': k_neighbors,
            'query': {'knn': {'zalando_img_vector': {'vector': features, 'k': k_neighbors}}}}
        )
    s3_uris = [res['hits']['hits'][x]['_source']['image'] for x in range(k_neighbors)]

    return s3_uris


def generate_presigned_urls(s3_uris):
    presigned_urls = [s3_client.generate_presigned_url(
        'get_object',
        Params={
            'Bucket': urlparse(x).netloc,
            'Key': urlparse(x).path.lstrip('/')},
        ExpiresIn=300
    ) for x in s3_uris]

    return presigned_urls


def download_file(url):
    r = requests.get(url)
    if r.status_code == 200:
        file = BytesIO(r.content)
        return file
    else:
        print("file failed to download")


def handler(event, context):

    # opensearch variables
    region = environ['AWS_REGION']
    opensearch_endpoint = environ['OSS_ENDPOINT']

    credentials = boto3.Session().get_credentials()
    auth = AWSV4SignerAuth(credentials, region)

    oss = OpenSearch(
        hosts=[{'host': opensearch_endpoint, 'port': 443}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )

    # sagemaker variables
    sagemaker_endpoint = environ['SM_ENDPOINT']

    api_payload = json.loads(event['body'])
    k = api_payload['k']
    if event['path'] == '/postURL':
        image = download_file(api_payload['url'])
    else:
        img_string = api_payload['base64img']
        print(img_string)
        image = BytesIO(base64.b64decode(img_string))

    features = get_features(sm_runtime_client, sagemaker_endpoint, image)
    s3_uris_neighbors = get_neighbors(features, oss, k_neighbors=k)
    s3_presigned_urls = generate_presigned_urls(s3_uris_neighbors)

    return {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin":  "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "*"
        },
        "body": json.dumps({
            "images": s3_presigned_urls,
        }),
    }
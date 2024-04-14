from django.http import HttpResponse
import boto3
from django.views.decorators.csrf import csrf_exempt
import os
import logging

logger = logging.getLogger("django.server")

from botocore import crt
import requests
from botocore.awsrequest import AWSRequest

# export PROMETHEUS_AWS_ACCESS_KEY_ID
# export PROMETHEUS_AWS_REGION
# export PROMETHEUS_AWS_SECRET_ACCESS_KEY
# export PROMETHEUS_URL


#POC
class PrometheusRequestHandler:
    def __init__(self, session , prometheus_url, region):
        self.aws_session= session
        self.prometheus_url=prometheus_url
        self.region = region

    @csrf_exempt
    def query(self, request):
        if self.aws_session is None or self.prometheus_url is None or self.region is None:
            logger.error(f"something is not set up url: {self.prometheus_url}, region: {self.region}, or session {self.aws_session is None}")
            return HttpResponse("No prometheus client")
        api_path = os.path.join("api/v1",request.path.split("api/v1/")[1])
        logger.debug(api_path)
        if request.method == 'POST':
            response = self.sigv4_request('POST',request.POST,api_path)
        elif request.method == 'GET':

            response = self.sigv4_request('GET', request.GET, api_path)
        else:
            return HttpResponse("wrong method", status=400)
        return HttpResponse(response.text)

    def sigv4_request(self,method, data,api_path):
        session = self.aws_session
        signer = crt.auth.CrtS3SigV4Auth(session.get_credentials(), 'aps', self.region)
        endpoint = os.path.join(self.prometheus_url, api_path)
        print(endpoint)

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        if method == "POST":
            request = AWSRequest(method='POST', url=endpoint, data=data, headers=headers)
        elif method == "GET":
            request = AWSRequest(method='GET', url=endpoint, params=data, headers=headers)
        request.context["payload_signing_enabled"] = False  # payload signing is not supported
        signer.add_auth(request)

        prepped = request.prepare()

        response = requests.post(prepped.url, headers=prepped.headers, data=data)
        return response


def setup_session():
    aws_access_key_id = os.environ.get("PROMETHEUS_AWS_ACCESS_KEY_ID", None)
    aws_secret_access_key = os.environ.get("PROMETHEUS_AWS_SECRET_ACCESS_KEY", None)
    region_name = os.environ.get("PROMETHEUS_AWS_REGION", None)
    # if aws_access_key_id is None or aws_secret_access_key is None or region_name is None:
    #     return None
    print(type(aws_access_key_id))
    print(aws_access_key_id)
    try:
        return boto3.Session(
                     aws_access_key_id=aws_access_key_id,
                     aws_secret_access_key=aws_secret_access_key,
                     region_name=region_name
                     )
    except Exception as e:
        logger.error("An error occurred:", exc_info=True)
        return None

prometheus_request_handler = PrometheusRequestHandler(session=setup_session(), prometheus_url=os.getenv("PROMETHEUS_URL"), region=os.getenv("PROMETHEUS_AWS_REGION"))
x =1
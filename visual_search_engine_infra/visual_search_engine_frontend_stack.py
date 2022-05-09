from aws_cdk import (
    Stack,
    Fn,
    aws_s3_deployment as s3deploy,
    aws_s3 as s3
)

from constructs import Construct


class VisualSearchEngineFrontendStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        s3_hosting_bucket_name = Fn.import_value("S3HostingBucket")
        s3_hosting_bucket = s3.Bucket.from_bucket_name(self, "ImportS3HostingBucket", s3_hosting_bucket_name)
        s3deploy.BucketDeployment(self, "DeployFrontendWebsite",
                                  sources=[s3deploy.Source.asset("./frontend/build")],
                                  destination_bucket=s3_hosting_bucket,
                                  memory_limit=1024
                                  )

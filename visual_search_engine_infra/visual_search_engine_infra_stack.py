from aws_cdk import (
    aws_iam as iam,
    aws_ec2 as ec2,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_opensearchservice as opensearch,
    aws_apigateway as apigw,
    Stack,
    CfnOutput
)

from aws_cdk.aws_lambda_python_alpha import PythonFunction
from aws_cdk.aws_lambda import Runtime
from constructs import Construct

import sagemaker_studio_constructs


class VisualSearchEngineInfraStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        role_sagemaker_studio_domain = iam.Role(self, 'RoleForSagemakerStudioUsers',
                                                assumed_by=iam.ServicePrincipal('sagemaker.amazonaws.com'),
                                                role_name="RoleSagemakerStudioUsers",
                                                managed_policies=[
                                                    iam.ManagedPolicy.from_managed_policy_arn(self,
                                                                                              id="SagemakerFullAccess",
                                                                                              managed_policy_arn="arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"),
                                                    iam.ManagedPolicy.from_managed_policy_arn(self,
                                                                                              id="CloudFormationReadOnlyAccess",
                                                                                              managed_policy_arn="arn:aws:iam::aws:policy/AWSCloudFormationReadOnlyAccess")
                                                ])
        self.role_sagemaker_studio_domain = role_sagemaker_studio_domain
        self.sagemaker_domain_name = "DomainForSagemakerStudio"

        default_vpc_id = ec2.Vpc.from_lookup(self, "VPC",
                                             is_default=True,
                                             vpc_id=self.node.try_get_context('existing_vpc_id')
                                             )

        self.vpc_id = default_vpc_id.vpc_id
        self.public_subnet_ids = [public_subnet.subnet_id for public_subnet in default_vpc_id.public_subnets]

        # noinspection PyTypeChecker
        oss_domain = opensearch.Domain(self, "Domain",
                                       version=opensearch.EngineVersion.OPENSEARCH_1_2,
                                       enable_version_upgrade=True
                                       )

        oss_domain.grant_read_write(role_sagemaker_studio_domain)
        self.oss_domain = oss_domain

        CfnOutput(self, "OpenSearchHostName",
                  value=oss_domain.domain_endpoint,
                  description="OpenSearch hostname",
                  export_name="OpenSearchHostName"
                  )

        CfnOutput(self, "OpenSearchDomainName",
                  value=oss_domain.domain_name,
                  description="OpenSearch domain name",
                  export_name="OpenSearchDomainName"
                  )

        s3_training_bucket = s3.Bucket(self, "S3TrainingBucket")

        s3deploy.BucketDeployment(self, "DeploySampleData",
                                  sources=[s3deploy.Source.asset("./training_data")],
                                  destination_bucket=s3_training_bucket,
                                  memory_limit=1024
                                  )

        s3_training_bucket.grant_read_write(role_sagemaker_studio_domain)

        s3_hosting_bucket = s3.Bucket(self, "S3HostingBucket", website_index_document="index.html",
                                      website_error_document="error.html",
                                      public_read_access=True
                                      )

        s3_hosting_bucket.grant_read_write(role_sagemaker_studio_domain)

        CfnOutput(self, "S3TrainingBucketOutput",
                  value=s3_training_bucket.bucket_name,
                  description="S3 training bucket name",
                  export_name="S3TrainingBucket"
                  )

        CfnOutput(self, "S3HostingBucketOutput",
                  value=s3_hosting_bucket.bucket_name,
                  description="S3 hosting bucket name",
                  export_name="S3HostingBucket"
                  )

        CfnOutput(self, "S3WebsiteURLOutput",
                  value=s3_hosting_bucket.bucket_website_url,
                  description="S3 hosting bucket website url",
                  export_name="S3WebsiteURL"
                  )

        backend_lambda = PythonFunction(self, "VisualSearchBackendLambda",
                                        entry="./backend",  # required
                                        runtime=Runtime.PYTHON_3_8,  # required
                                        environment={
                                            "OSS_ENDPOINT": oss_domain.domain_endpoint,
                                            "SM_ENDPOINT": ""
                                        }
                                        )
        backend_lambda.role.attach_inline_policy(iam.Policy(self, "visualsearch-backend-lambda-policy",
                                                            statements=[iam.PolicyStatement(
                                                                actions=["sagemaker:InvokeEndpoint"],
                                                                resources=["*"]
                                                            )]
                                                            ))
        oss_domain.grant_read_write(backend_lambda)
        s3_training_bucket.grant_read(backend_lambda)
        self.role_sagemaker_studio_domain.add_to_policy(
            iam.PolicyStatement(
                actions=["lambda:UpdateFunctionConfiguration"],
                resources=[backend_lambda.function_arn]
            )
        )
        CfnOutput(self, "PostFetchSimilarPhotosLambda",
                  value=backend_lambda.function_arn,
                  description="Lambda function to fetch similar photos",
                  export_name="PostFetchSimilarPhotosLambda"
                  )
        CfnOutput(self, "PostFetchSimilarPhotosLambdaIamRole",
                  value=backend_lambda.role.role_arn,
                  description="Implicit IAM Role created for PostFetchSimilarPhotosLambda",
                  export_name="PostFetchSimilarPhotosLambdaIamRole"
                  )
        api = apigw.LambdaRestApi(
            self, 'VisualSearchBackendLambdaAPIEndpoint',
            handler=backend_lambda,
            default_cors_preflight_options=apigw.CorsOptions(allow_origins=apigw.Cors.ALL_ORIGINS,
                                                             allow_methods=apigw.Cors.ALL_METHODS,
                                                             allow_headers=apigw.Cors.DEFAULT_HEADERS)
        )
        post_url = api.root.add_resource("postURL")
        post_url.add_method("POST")
        post_image = api.root.add_resource("postImage")
        post_image.add_method("POST")
        CfnOutput(self, "ImageSimilarityApi",
                  value=api.url,
                  description="API Gateway endpoint URL for Prod stage for fetchPhoto function",
                  export_name="ImageSimilarityApi"
                  )

        my_sagemaker_domain = sagemaker_studio_constructs.SagemakerStudioDomainConstruct(self,
                                                                                         "mySagemakerStudioDomain",
                                                                                         sagemaker_domain_name=self.sagemaker_domain_name,
                                                                                         vpc_id=self.vpc_id,
                                                                                         subnet_ids=self.public_subnet_ids,
                                                                                         role_sagemaker_studio_users=self.role_sagemaker_studio_domain,
                                                                                         default_kernel_instance="ml.m5.2xlarge")

        team_to_add_in_sagemaker_studio = ["ml-engineer-1"]
        for _team in team_to_add_in_sagemaker_studio:
            my_default_datascience_user = sagemaker_studio_constructs.SagemakerStudioUserConstruct(self,
                                                                                                   _team,
                                                                                                   sagemaker_domain_id=my_sagemaker_domain.sagemaker_domain_id,
                                                                                                   user_profile_name=_team)
            CfnOutput(self, f"cfnoutput{_team}",
                      value=my_default_datascience_user.user_profile_arn,
                      description="The User Arn Team domain ID",
                      export_name=F"UserArn{_team}"
                      )

        CfnOutput(self, "DomainIdSagemaker",
                  value=my_sagemaker_domain.sagemaker_domain_id,
                  description="The sagemaker domain ID",
                  export_name="DomainIdSagemaker"
                  )
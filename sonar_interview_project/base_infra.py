
import aws_cdk as cdk

from aws_cdk import (
    Duration,
    Stack,
    aws_ec2 as ec2,
    aws_s3 as s3
)

from constructs import Construct

from sonar_interview_project.util.config_loader import ConfigLoader

class BaseInfraStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, project_config: ConfigLoader, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        project_name = project_config.get("project_name")
        region = cdk.Stack.of(self).region

        # VPC
        # - VPC size?
        #   - this affects subnet sizing
        # - region? (how do we determine CIDR range of subnets?)

        # S3
        # - IAM roles for access
        # - lifecycle bucket policies


        # Create S3 and VPC
        # the idea is this infra shouldn't really ever change, so we can deploy it separately
        
        # Create the s3 buckets

        s3_asset_bucket = s3.Bucket(self, "AssetBucket",
                              bucket_name=f"{project_name}-assets-{region}",
                              block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
                              enforce_ssl=True,
                              versioned=True,
                              # figure out if we need to give an IAM role for the application
                              # or cloudfront? access_control defaults to private.
                              # access_control=s3.BucketAccessControl.LOG_DELIVERY_WRITE,  
                              encryption=s3.BucketEncryption.S3_MANAGED,
                              # also should give users the ability to specify their own custom lifecycle rules
                              lifecycle_rules=[
                                  s3.LifecycleRule(
                                      id="DefaultDataRule",
                                      abort_incomplete_multipart_upload_after=Duration.days(7),
                                      # current version actions?
                                      noncurrent_version_transitions=[
                                          s3.NoncurrentVersionTransition(
                                              transition_after=Duration.days(2),
                                              storage_class=s3.StorageClass.INTELLIGENT_TIERING
                                          )
                                      ],  
                                      noncurrent_version_expiration=Duration.days(14)
                                  )       
                              ]
                            )
        
        # Create the VPC
        # Use nat gateways here since I don't have the time to figure out nat instances
        
        vpc = ec2.Vpc(self, "VPC",
                      vpc_name=f"{project_name}-vpc-{region}",
                      ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
                      nat_gateways=1,
                      max_azs=3,
                      # subnet_configuration - we're fine with the default (public and private)
                      # max_azs - also fine with default (3) 
                      # - HAVE TO SPECIFY ACCOUNT/REGION TO GET THIS, otherwise you get 2
                      # should I do restrict_default_security_group?
                      gateway_endpoints={
                            "S3": ec2.GatewayVpcEndpointOptions(
                                service=ec2.GatewayVpcEndpointAwsService.S3
                            )
                        }
                    )

        # export the vpc and s3 bucket
        self.vpc = vpc
        self.s3_assets = s3_asset_bucket

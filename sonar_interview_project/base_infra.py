
from aws_cdk import (
    Duration,
    Stack,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_s3 as s3
)

from constructs import Construct

class BaseInfraStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # what do I want to pass in here?
        # Project name
        # - tag name to everything

        # VPC
        # - VPC size?
        #   - this affects subnet sizing
        # - region? (how do we determine CIDR range of subnets?)
        # - vpc flow log destination? (individudal bucket or shared?)

        # S3
        # - IAM roles for access
        # - lifecycle bucket policies
        # - flag for log bucket?


        # Create S3 and VPC
        # the idea is this infra shouldn't really ever change, so we can deploy it separately
        
        # Create the s3 buckets

        s3_logs = s3.Bucket(self, "projectVPCFlowLogBucket",
                            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
                            enforce_ssl=True,
                            versioned=True,
                            access_control=s3.BucketAccessControl.LOG_DELIVERY_WRITE,
                            encryption=s3.BucketEncryption.S3_MANAGED,
                            intelligent_tiering_configurations=[
                                s3.IntelligentTieringConfiguration(
                                    name="FlowLogArchivePolicy",
                                    archive_access_tier_time=Duration.days(90),
                                    deep_archive_access_tier_time=Duration.days(180)
                                )]
                            )
        
        vpc_flow_log_rule = iam.Role(self, "vpcFlowLogRule",
                                     assumed_by=iam.ServicePrincipal("vpc-flow-logs.amazonaws.com")
                                     )
        
        s3_logs.grant_write(vpc_flow_log_rule,["projectVpcFlowLogs/*"])

        s3_assets = s3.Bucket(self, "projectAssetBucket",
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
        
        # VPC CIDRs should follow basic pattern:
        # 10.X.Y.Z
        #    | | |
        #    AWS region - us-east-1 = 0, us-east-2 = 1, us-west-2 = 2
        #    come back to this

        # Create the VPC
        # Use nat gateways here since I don't have the time to figure out nat instances
        
        vpc = ec2.Vpc(self, "projectVPC",
                      vpc_name="Project VPC",
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

        # Hook up VPC flow logs to bucket
        vpc_flow_log = ec2.FlowLog(self, "projectVpcFlowLogs",
                                   destination=ec2.FlowLogDestination.to_s3(s3_logs, "projectVpcFlowLogs/"),
                                   traffic_type=ec2.FlowLogTrafficType.ALL,
                                   flow_log_name="projectVpcFlowLogs",
                                   resource_type=ec2.FlowLogResourceType.from_vpc(vpc))

        # export the vpc
        self.vpc = vpc


import aws_cdk as cdk

from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
)

from constructs import Construct

from sonar_interview_project.util.config_loader import ConfigLoader

class BaseInfraStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, project_config: ConfigLoader, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        project_name = project_config.get("project_name")
        region = cdk.Stack.of(self).region
        
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

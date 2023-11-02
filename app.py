#!/usr/bin/env python3
import os

import aws_cdk as cdk

from sonar_interview_project.base_infra import BaseInfraStack
from sonar_interview_project.sg_infra import SgInfraStack
from sonar_interview_project.db_infra import DbInfraStack
from sonar_interview_project.cluster_infra import ClusterInfraStack
# from sonar_interview_project.ecs_service_infra import LbEcsServiceStack

env = cdk.Environment(account='726431819040', region='us-east-1')

app = cdk.App()
#SonarInterviewProjectStack(app, "SonarInterviewProjectStack",
    # If you don't specify 'env', this stack will be environment-agnostic.
    # Account/Region-dependent features and context lookups will not work,
    # but a single synthesized template can be deployed anywhere.

    # Uncomment the next line to specialize this stack for the AWS Account
    # and Region that are implied by the current CLI configuration.

    #env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),

    # Uncomment the next line if you know exactly what Account and Region you
    # want to deploy the stack to. */

    # For more information, see https://docs.aws.amazon.com/cdk/latest/guide/environments.html
 #   )

# S3, VPC
base_infra_stack = BaseInfraStack(app, "SonarInterviewBaseInfraStack", env=env)

sg_infra_stack = SgInfraStack(app, "SonarInterviewSgInfraStack", env=env,
                             vpc=base_infra_stack.vpc)

# DB infra
db_infra_stack = DbInfraStack(app, "SonarInterviewDbInfraStack", env=env, 
                              vpc=base_infra_stack.vpc,
                              db_sg=sg_infra_stack.db_sg)

# ASG, ECS cluster
ecs_cluster_infra_stack = ClusterInfraStack(app, "SonarInterviewASGInfraStack", env=env, 
                                vpc=base_infra_stack.vpc,
                                db_sg=sg_infra_stack.db_sg,
                                ecs_cluster_sg=sg_infra_stack.ecs_cluster_sg
                                )

# Application, ALB
# lb_ecs_service_stack = LbEcsServiceStack(app, "SonarInterviewLbEcsServiceStack", env=env,
#                                          vpc=base_infra_stack.vpc, 
#                                          ecs_cluster=ecs_cluster_infra_stack.ecs_cluster,
#                                          ecs_cluster_sg=ecs_cluster_infra_stack.ecs_cluster_sg)

app.synth()

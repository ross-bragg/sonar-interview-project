#!/usr/bin/env python3
import os
import sys

import aws_cdk as cdk

from sonar_interview_project.base_infra import BaseInfraStack
from sonar_interview_project.sg_infra import SgInfraStack
from sonar_interview_project.db_infra import DbInfraStack
from sonar_interview_project.cluster_infra import ClusterInfraStack
from sonar_interview_project.ecs_service_infra import LbEcsServiceStack
from sonar_interview_project.s3_stack import S3ReplicatedStack

from sonar_interview_project.util.config_loader import ConfigLoader

app = cdk.App()
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

# Get project
project = app.node.try_get_context("project")
if not project:
    raise SystemExit("No project provided, pass in as `-c project=XXX")

# Load and validate project config
config = ConfigLoader(project)

project_name = config.get("project_name")

main_env = cdk.Environment(account=config.get("aws_config").get("account"), 
                           region=config.get("aws_config").get("main_region")
                        )

dr_env = cdk.Environment(account=config.get("aws_config").get("account"), 
                         region=config.get("aws_config").get("dr_region")
                      )

print(project_name)
print(main_env)
print(dr_env)

# VPC
base_infra_stack = BaseInfraStack(app, f"{project_name}BaseInfra", env=main_env,
                                  project_config=config
                                )

dr_base_infra_stack = BaseInfraStack(app, f"{project_name}BaseInfraDr", env=dr_env,
                                  project_config=config
                                )

s3_dr_region = S3ReplicatedStack(app, f"{project_name}S3Dr", env=dr_env,
                                 project_config=config)

s3_main_region = S3ReplicatedStack(app, f"{project_name}S3", env=main_env,
                                 project_config=config)

# # Need to figure out how to use custom SGs without a circular dependency
# sg_infra_stack = SgInfraStack(app, "SonarInterviewSgInfraStack", env=env,
#                              vpc=base_infra_stack.vpc)
# I think I need to do the add_deps thing here.

# # DB infra
# db_infra_stack = DbInfraStack(app, "SonarInterviewDbInfraStack", env=env, 
#                               project_config=config,
#                               vpc=base_infra_stack.vpc
#                             )

# # ASG, ECS cluster
# ecs_cluster_infra_stack = ClusterInfraStack(app, "SonarInterviewASGInfraStack", env=env, 
#                                             project_config=config,
#                                             vpc=base_infra_stack.vpc
#                                           )

# # Application, ALB
# lb_ecs_service_stack = LbEcsServiceStack(app, "SonarInterviewLbEcsServiceStack", env=env,
#                                          project_config=config,
#                                          vpc=base_infra_stack.vpc,
#                                          ecs_cluster=ecs_cluster_infra_stack.ecs_cluster
#                                       )

app.synth()

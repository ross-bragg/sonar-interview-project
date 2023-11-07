#!/usr/bin/env python3

import aws_cdk as cdk

from sonar_interview_project.base_infra import BaseInfraStack
from sonar_interview_project.sg_infra import SgInfraStack
from sonar_interview_project.global_db_infra import GlobalDbInfraStack
from sonar_interview_project.cluster_infra import ClusterInfraStack
from sonar_interview_project.ecs_service_infra import LbEcsServiceStack
from sonar_interview_project.s3_stack import S3ReplicatedStack

from sonar_interview_project.util.config_loader import ConfigLoader

app = cdk.App()

# Get project
project = app.node.try_get_context("project")
if not project:
    raise SystemExit("No project provided, pass in as `-c project=XXX")

# is it a disaster?
is_disaster = False
if app.node.try_get_context("is_disaster") and app.node.try_get_context("is_disaster") == "true":
   is_disaster = True

# Load and validate project config
config = ConfigLoader(project)

project_name = config.get("project_name")

main_env = cdk.Environment(account=config.get("aws_config").get("account"), 
                           region=config.get("aws_config").get("main_region")
                        )

dr_env = cdk.Environment(account=config.get("aws_config").get("account"), 
                         region=config.get("aws_config").get("dr_region")
                        )

# VPC Infra
base_infra_main_region = BaseInfraStack(app, f"{project_name}BaseInfra", env=main_env,
                                  project_config=config
                                )

base_infra_dr_region = BaseInfraStack(app, f"{project_name}BaseInfraDr", env=dr_env,
                                  project_config=config
                                )

# S3 replication infra
s3_dr_region = S3ReplicatedStack(app, f"{project_name}S3Dr", env=dr_env,
                                 project_config=config
                              )

s3_main_region = S3ReplicatedStack(app, f"{project_name}S3", env=main_env,
                                 project_config=config
                              )
s3_main_region.add_dependency(s3_dr_region)

# Security Groups
sgs_main_region = SgInfraStack(app, f"{project_name}SGs", env=main_env,
                             vpc=base_infra_main_region.vpc,
                             project_config=config)

sgs_dr_region = SgInfraStack(app, f"{project_name}SGsDr", env=dr_env,
                             vpc=base_infra_dr_region.vpc,
                             project_config=config)

# Aurora Global DB infra
global_db_main_region = GlobalDbInfraStack(app, f"{project_name}GlobalDb", env=main_env,
                                           vpc=base_infra_main_region.vpc,
                                           project_config=config,
                                           db_sg=sgs_main_region.db_sg
                                          )

global_db_dr_region = GlobalDbInfraStack(app, f"{project_name}GlobalDbDr", env=dr_env,
                                          vpc=base_infra_dr_region.vpc,
                                          project_config=config,
                                          db_sg=sgs_dr_region.db_sg,
                                          is_disaster=is_disaster
                                       )
global_db_dr_region.add_dependency(global_db_main_region)

# # ASG, ECS cluster
ecs_cluster_main_region = ClusterInfraStack(app, f"{project_name}ASG", env=main_env, 
                                            project_config=config,
                                            vpc=base_infra_main_region.vpc,
                                            cluster_sg=sgs_main_region.ecs_cluster_sg
                                          )

ecs_cluster_dr_region = ClusterInfraStack(app, f"{project_name}ASGDr", env=dr_env, 
                                            project_config=config,
                                            vpc=base_infra_dr_region.vpc,
                                            cluster_sg=sgs_dr_region.ecs_cluster_sg
                                          )

# Application, ALB
lb_ecs_service_main_region = LbEcsServiceStack(app, f"{project_name}ECSService", env=main_env,
                                         project_config=config,
                                         vpc=base_infra_main_region.vpc,
                                         ecs_cluster=ecs_cluster_main_region.ecs_cluster,
                                         alb_sg=sgs_main_region.alb_sg
                                      )

lb_ecs_service_dr_region = LbEcsServiceStack(app, f"{project_name}ECSServiceDr", env=dr_env,
                                         project_config=config,
                                         vpc=base_infra_dr_region.vpc,
                                         ecs_cluster=ecs_cluster_dr_region.ecs_cluster,
                                         alb_sg=sgs_dr_region.alb_sg
                                      )

app.synth()

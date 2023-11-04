from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_rds as rds
)

from constructs import Construct

from sonar_interview_project.util.config_loader import ConfigLoader

class DbInfraStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, project_config: ConfigLoader, vpc: ec2.Vpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # make this configurable
        db_instance_type = ec2.InstanceType.of(ec2.InstanceClass.T4G, ec2.InstanceSize.MEDIUM)
        # credentials automatically created in secretsManager
        # needs to be somehow configurable
        # probably do this in the base infra since it needs to be created first and shared

        # DB cluster

        cluster = rds.DatabaseCluster(self, "projectDatabase",
                                      vpc=vpc,
                                      cluster_identifier="ProjectDatabase",
                                      engine=rds.DatabaseClusterEngine.aurora_postgres(version=rds.AuroraPostgresEngineVersion.VER_15_3),
                                      writer=rds.ClusterInstance.provisioned("writer", instance_type=db_instance_type),
                                    #   readers=[
                                    #     rds.ClusterInstance.provisioned("reader1", instance_type=db_instance_type),
                                    #     rds.ClusterInstance.provisioned("reader2", instance_type=db_instance_type)
                                    #   ],
                                      readers=[],
                                      default_database_name="project",
                                    )
        
        cluster.connections.allow_from(
            ec2.Peer.any_ipv4(), # should match the VPC CIDR
            ec2.Port.tcp(5432),
            "Incoming DB access"
        )

    # Once done, create a custom DNS for the DB Writer endponit and Reader endpoint, emit as CFN output
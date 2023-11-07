import aws_cdk as cdk

from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_rds as rds
)

from constructs import Construct

from sonar_interview_project.util.config_loader import ConfigLoader

class GlobalDbInfraStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, project_config: ConfigLoader, vpc: ec2.Vpc, db_sg: ec2.SecurityGroup, is_disaster=False, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        project_name = project_config.get("project_name")
        main_region = project_config.get("aws_config").get("main_region")
        dr_region = project_config.get("aws_config").get("dr_region")

        db_name = project_name.replace('-', '_')
        db_cluster_name = f"{project_name}-cluster"
        global_db_cluster_name = f"{project_name}-global"

        db_instance_type = ec2.InstanceType(project_config.get("db_config").get("instance_type"))
        
        num_readers = project_config.get("db_config").get("readers")
        
        db_readers = []
        for i in range(num_readers):
            db_readers.append(rds.ClusterInstance.provisioned(f"reader{i}", instance_type=db_instance_type))

        if self.region == main_region:
            cluster = rds.DatabaseCluster(self, f"{project_name}Database",
                                        vpc=vpc,
                                        cluster_identifier=db_cluster_name,
                                        engine=rds.DatabaseClusterEngine.aurora_postgres(version=rds.AuroraPostgresEngineVersion.VER_15_3),
                                        writer=rds.ClusterInstance.provisioned("writer", instance_type=db_instance_type),
                                        readers=db_readers,
                                        default_database_name=db_name,
                                        security_groups=[db_sg],
                                        # Don't snapshot cluster on delete (speeds things up for this purpose, wouldn't do IRL)
                                        removal_policy=cdk.RemovalPolicy.DESTROY
                                        )

            # Don't snapshot cluster on delete (speeds things up for this purpose, wouldn't do IRL)

            cluster_arn = f"arn:aws:rds:{self.region}:{self.account}:cluster:{db_cluster_name}"

            global_cluster = rds.CfnGlobalCluster(self, f"{project_name}GlobalCluster",
                                                deletion_protection=False,
                                                global_cluster_identifier=global_db_cluster_name,
                                                source_db_cluster_identifier=cluster_arn
                                                )
            
            global_cluster.node.add_dependency(cluster)

        elif self.region == dr_region:

            # I think the most correct way to do this would be to create an empty cluster to start repl
            # AND THEN when we pass is_dr, add instances accordingly.
            # unfortunately requires all the DB CFN components, etc and I need this done

            if not is_disaster:
                db_readers = []

            cluster = rds.DatabaseCluster(self, f"{project_name}Database",
                                        vpc=vpc,
                                        cluster_identifier=db_cluster_name,
                                        engine=rds.DatabaseClusterEngine.aurora_postgres(version=rds.AuroraPostgresEngineVersion.VER_15_3),
                                        writer=rds.ClusterInstance.provisioned("writer", instance_type=db_instance_type),
                                        readers=db_readers,
                                        security_groups=[db_sg],
                                        # Don't snapshot cluster on delete (speeds things up for this assignment, wouldn't do IRL)
                                        removal_policy=cdk.RemovalPolicy.DESTROY
                                        )

            cfn_db_cluster = cluster.node.default_child

            cfn_db_cluster.global_cluster_identifier = global_db_cluster_name
            cfn_db_cluster.manage_master_user_password = False
            cfn_db_cluster.add_property_deletion_override("MasterUsername")
            cfn_db_cluster.add_property_deletion_override("MasterUserPassword")
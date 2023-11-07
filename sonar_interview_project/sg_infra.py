from aws_cdk import (
    Stack,
    CfnOutput,
    aws_ec2 as ec2,
)

from constructs import Construct
from sonar_interview_project.util.config_loader import ConfigLoader

class SgInfraStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, vpc: ec2.Vpc, project_config: ConfigLoader, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        project_name = project_config.get("project_name")

        alb_config = project_config.get("ecs_service_config").get(f"{self.region}_config".replace('-', '_')).get("alb")
        alb_custom_ingress = alb_config.get("custom_ingress_rules")
        
        # Manage the SGs separately so that we don't run into "dependency in use" issues when deleting
        db_sg = ec2.SecurityGroup(self, f"{project_name}DbSg",
                            vpc=vpc,
                            description="Allow ingress from application",
                            allow_all_outbound=False)
        
        ecs_cluster_sg = ec2.SecurityGroup(self, f"{project_name}EcsClusterSg",
                            vpc=vpc,
                            description="Allow egress to DB, ingress from alb",
                            allow_all_outbound=True)
        
        alb_sg = ec2.SecurityGroup(self, f"{project_name}AlbSg",
                            vpc=vpc,
                            description="Allow egress to instances, ingress from internet",
                            allow_all_outbound=False)
        
        # export sgs as cfn outputs

        db_sg.connections.allow_from(
            ecs_cluster_sg,
            ec2.Port.tcp(5432),
            "Allow connections from ASG"
        )

        ecs_cluster_sg.connections.allow_to(
            db_sg,
            ec2.Port.tcp(5432),
            "Allow connections to DB"
        )

        ecs_cluster_sg.connections.allow_from(
            alb_sg,
            ec2.Port.all_tcp(),
            "Allow connections from ALB"
        )

        # ecs_cluster_sg.connections.allow_from(
        #     ec2.Peer.any_ipv4(),
        #     ec2.Port.all_tcp(),
        #     "Allow connections from ALB"
        # )


        alb_sg.connections.allow_to(
            ecs_cluster_sg,
            ec2.Port.all_tcp(),
            "Allow connections to ASG"
        )

        for ingress_rule in alb_custom_ingress:
            alb_sg.connections.allow_from(
                ec2.Peer.ipv4(ingress_rule.get("cidr")),
                ec2.Port.tcp(ingress_rule.get("port")),
                ingress_rule.get("description")
            )

        self.db_sg = db_sg
        self.ecs_cluster_sg = ecs_cluster_sg
        self.alb_sg = alb_sg
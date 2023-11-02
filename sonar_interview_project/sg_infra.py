from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
)

from constructs import Construct

class SgInfraStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, vpc: ec2.Vpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        db_sg = ec2.SecurityGroup(self, "projectDbSg",
                            vpc=vpc,
                            description="Allow ingress from application",
                            allow_all_outbound=False)
        
        ecs_cluster_sg = ec2.SecurityGroup(self, "projectEcsClusterSg",
                            vpc=vpc,
                            description="Allow egress to DB, ingress from alb",
                            allow_all_outbound=False)
        
        alb_sg = ec2.SecurityGroup(self, "projectAlbSg",
                            vpc=vpc,
                            description="Allow egress to instances, ingress from internet",
                            allow_all_outbound=False)
        
        # export sgs
        self.db_sg = db_sg
        self.ecs_cluster_sg = ecs_cluster_sg
        self.alb_sg = alb_sg
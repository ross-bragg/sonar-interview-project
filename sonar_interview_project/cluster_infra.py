from aws_cdk import (
    Stack,
    aws_autoscaling as autoscaling,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_elasticloadbalancingv2 as elbv2,
    aws_rds as rds
)

from constructs import Construct

from sonar_interview_project.util.config_loader import ConfigLoader

class ClusterInfraStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, project_config: ConfigLoader, vpc: ec2.Vpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        asg_instance_type = ec2.InstanceType(project_config.get("ecs_cluster_config").get("instance_type"))
        min_capacity = project_config.get("ecs_cluster_config").get("min")
        max_capacity = project_config.get("ecs_cluster_config").get("max")
        
        ecs_cluster = ecs.Cluster(self, "projectECSCluster",
                                  vpc=vpc)
        
        ecs_asg = autoscaling.AutoScalingGroup(self, "ProjectECSClusterASG",
                                               vpc=vpc,
                                               instance_type=asg_instance_type,
                                               machine_image=ecs.EcsOptimizedImage.amazon_linux2023(hardware_type=ecs.AmiHardwareType.ARM),
                                               max_capacity=min_capacity,
                                               min_capacity=max_capacity,
                                               new_instances_protected_from_scale_in=False,
                                               # defaults to placement in private subnets.
                                            )
        
        # enable_managed_termination_protection prevents cleaning up the ASG from hanging during deletion
        # When true this should make it so that ECS won't scale down any instances with containers still on them
        # But it seems to just block scale down regardless. 
        # May need to use managed container scaling too, but that's outside the scope of this.
        ecs_asg_cap_provider = ecs.AsgCapacityProvider(self, "EcsAsgCapacityProvider",
                                                       auto_scaling_group=ecs_asg,
                                                       enable_managed_termination_protection=False
                                                    )
        
        ecs_cluster.add_asg_capacity_provider(ecs_asg_cap_provider)

        # grant s3 access here too?

        # Allow ingress to instances from Nat GW (private IP?)
        ecs_asg.connections.allow_from(
            ec2.Peer.ipv4('10.0.28.221/32'),
            ec2.Port.tcp(22),
            "ssh from Nat Gateway"
        )

        ecs_asg.connections.allow_to(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(5432),
            "EC2 instance access to DBs"
        )

        ecs_asg.connections.allow_from(
            ec2.Peer.any_ipv4(),
            ec2.Port.all_tcp(),
            "Instance access from ALB"
        )

        # export ecs cluster
        self.ecs_cluster = ecs_cluster

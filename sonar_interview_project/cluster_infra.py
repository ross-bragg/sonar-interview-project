from aws_cdk import (
    Stack,
    aws_autoscaling as autoscaling,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_elasticloadbalancingv2 as elbv2,
    aws_rds as rds
)

from constructs import Construct

class ClusterInfraStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, vpc: ec2.Vpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        asg_instance_type = ec2.InstanceType.of(ec2.InstanceClass.T4G, ec2.InstanceSize.SMALL)
        
        ecs_cluster = ecs.Cluster(self, "projectECSCluster",
                                  vpc=vpc)
        
        ecs_asg = autoscaling.AutoScalingGroup(self, "ProjectECSClusterASG",
                                               vpc=vpc,
                                               instance_type=asg_instance_type,
                                               machine_image=ecs.EcsOptimizedImage.amazon_linux2023(hardware_type=ecs.AmiHardwareType.ARM),
                                               max_capacity=1,
                                               min_capacity=1,
                                               new_instances_protected_from_scale_in=False,
                                               # defaults to placement in private subnets.
                                               key_name="ross_key"
                                            )
        
        ecs_asg_cap_provider = ecs.AsgCapacityProvider(self, "EcsAsgCapacityProvider",
                                                       auto_scaling_group=ecs_asg)
        
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

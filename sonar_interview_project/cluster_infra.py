from aws_cdk import (
    Stack,
    aws_autoscaling as autoscaling,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_elasticloadbalancingv2 as elbv2,
)

from constructs import Construct

class ClusterInfraStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, vpc: ec2.Vpc, db_sg: ec2.SecurityGroup, ecs_cluster_sg: ec2.SecurityGroup, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        asg_instance_type = ec2.InstanceType.of(ec2.InstanceClass.T4G, ec2.InstanceSize.SMALL)
        
        # Allow ingress to instances from Nat GW (private IP?)
        ecs_cluster_sg.add_ingress_rule(ec2.Peer.ipv4('10.0.28.221/32'), ec2.Port.tcp(22), 'ssh from Nat Gateway')

        # Hook into DB SG, allow access from EC2 instances
        db_sg.add_ingress_rule(ec2.Peer.security_group_id(db_sg.security_group_id), ec2.Port.tcp(5432), 'DB access from EC2 instances')

        ecs_cluster = ecs.Cluster(self, "projectECSCluster",
                                  vpc=vpc)
        
        ecs_asg = autoscaling.AutoScalingGroup(self, "ProjectECSClusterASG",
                                               vpc=vpc,
                                               instance_type=asg_instance_type,
                                               machine_image=ecs.EcsOptimizedImage.amazon_linux2023(hardware_type=ecs.AmiHardwareType.ARM),
                                               max_capacity=1,
                                               min_capacity=1,
                                               # defaults to placement in private subnets.
                                               security_group=ecs_cluster_sg
                                            )
        
        ecs_asg_cap_provider = ecs.AsgCapacityProvider(self, "EcsAsgCapacityProvider",
                                                       auto_scaling_group=ecs_asg)
        
        ecs_cluster.add_asg_capacity_provider(ecs_asg_cap_provider)

        # export ecs cluster?
        self.ecs_cluster = ecs_cluster
        self.ecs_cluster_sg = ecs_cluster_sg
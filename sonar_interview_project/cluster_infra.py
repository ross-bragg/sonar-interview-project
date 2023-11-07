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

    def __init__(self, scope: Construct, construct_id: str, project_config: ConfigLoader, vpc: ec2.Vpc, cluster_sg: ec2.SecurityGroup, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        project_name = project_config.get("project_name")

        asg_instance_type = ec2.InstanceType(project_config.get("ecs_cluster_config").get("instance_type"))
        min_capacity = project_config.get("ecs_cluster_config").get("min")
        max_capacity = project_config.get("ecs_cluster_config").get("max")
        
        ecs_cluster = ecs.Cluster(self, f"{project_name}ECSCluster",
                                  vpc=vpc)
        
        # Need to grant S3 access here
        ecs_asg = autoscaling.AutoScalingGroup(self, f"{project_name}ECSClusterASG",
                                               vpc=vpc,
                                               instance_type=asg_instance_type,
                                               machine_image=ecs.EcsOptimizedImage.amazon_linux2023(hardware_type=ecs.AmiHardwareType.ARM),
                                               max_capacity=max_capacity,
                                               min_capacity=min_capacity,
                                               new_instances_protected_from_scale_in=False,
                                               security_group=cluster_sg
                                               # defaults to placement in private subnets.
                                            )
        
        # enable_managed_termination_protection prevents cleaning up the ASG from hanging during deletion
        # When true this should make it so that ECS won't scale down any instances with containers still on them
        # But it seems to just block scale down regardless. 
        # May need to use managed container scaling too, but that's outside the scope of this.
        ecs_asg_cap_provider = ecs.AsgCapacityProvider(self, f"{project_name}AsgCapProvider",
                                                       auto_scaling_group=ecs_asg,
                                                       enable_managed_termination_protection=False
                                                    )
        
        ecs_cluster.add_asg_capacity_provider(ecs_asg_cap_provider)

        # grant s3 access here too?

        # export ecs cluster
        self.ecs_cluster = ecs_cluster

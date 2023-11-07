from aws_cdk import (
    Duration,
    Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_elasticloadbalancingv2 as elbv2,
    aws_logs as logs
)

from constructs import Construct

from sonar_interview_project.util.config_loader import ConfigLoader

class LbEcsServiceStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, project_config: ConfigLoader, vpc: ec2.Vpc, ecs_cluster: ecs.Cluster, alb_sg: ec2.SecurityGroup, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        project_name = project_config.get("project_name")

        ecs_task_image = project_config.get("ecs_service_config").get("image")
        mem_limit = project_config.get("ecs_service_config").get("mem_limit")
        
        env_config = project_config.get("ecs_service_config").get(f"{self.region}_config".replace('-', '_'))
        container_config = env_config.get("container")

        ecs_task_definition = ecs.Ec2TaskDefinition(self, f"{project_name}ECSTask")

        # need to also grant S3 access here too
        ecs_task_container = ecs_task_definition.add_container(
            f"{project_name}TaskContainer",
            image=ecs.ContainerImage.from_registry(ecs_task_image),
            memory_limit_mib=mem_limit,
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix=f"{project_name}Logs",
                log_retention=logs.RetentionDays.ONE_WEEK
            ),
            environment=container_config
        )

        ecs_task_container_port_mapping = ecs.PortMapping(
            container_port=80,
            host_port=0,
            protocol=ecs.Protocol.TCP
        )

        ecs_task_container.add_port_mappings(ecs_task_container_port_mapping)

        ecs_service = ecs.Ec2Service(self, f"{project_name}ECSService",
                                     cluster=ecs_cluster,
                                     task_definition=ecs_task_definition)

        # have to manually create the service/alb because the pattern doesn't let you chose the SG.
        alb = elbv2.ApplicationLoadBalancer(self, f"{project_name}ALB",
                                            vpc=vpc,
                                            security_group=alb_sg,
                                            internet_facing=True)
        
        alb_listener = alb.add_listener(
            "http_listener",
            port=80,
            open=False
        )

        alb_health_check = elbv2.HealthCheck(
            interval=Duration.seconds(60),
            path="/",
            timeout=Duration.seconds(5)
        )

        alb_listener.add_targets(
            f"{project_name}ECSService",
            port=80,
            targets=[ecs_service],
            health_check=alb_health_check
        )

        # export ALB DNS
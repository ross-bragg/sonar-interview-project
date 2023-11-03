from aws_cdk import (
    Duration,
    Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_elasticloadbalancingv2 as elbv2,
    aws_logs as logs
)

from constructs import Construct

class LbEcsServiceStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, vpc: ec2.Vpc, ecs_cluster: ecs.Cluster, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Task def, service construction
        # does this need to change with deployments or does it get automatically versioned?
        ecs_task_definition = ecs.Ec2TaskDefinition(self, "projectTaskDef")

        ecs_task_container = ecs_task_definition.add_container(
            "ProjectTaskContainer",
            image=ecs.ContainerImage.from_registry("public.ecr.aws/nginx/nginx:1.25-alpine-slim-arm64v8"),
            memory_limit_mib=256,
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="ProjectLogs",
                log_retention=logs.RetentionDays.ONE_WEEK
            )
        )

        ecs_task_container_port_mapping = ecs.PortMapping(
            container_port=80,
            host_port=0,
            protocol=ecs.Protocol.TCP
        )

        ecs_task_container.add_port_mappings(ecs_task_container_port_mapping)

        ecs_service = ecs.Ec2Service(self, "ProjectEcsService",
                                     cluster=ecs_cluster,
                                     task_definition=ecs_task_definition)

        # have to manually create the service/alb because the pattern doesn't let you chose the SG.
        alb = elbv2.ApplicationLoadBalancer(self, "ProjectALB",
                                            vpc=vpc,
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
            "ProjectEcsService",
            port=80,
            targets=[ecs_service],
            health_check=alb_health_check
        )

        alb.connections.allow_to(
            ec2.Peer.any_ipv4(),
            ec2.Port.all_tcp(),
            'Egress from ALB to EC2'
        )

        # custom rules
        alb.connections.allow_from(
            ec2.Peer.ipv4('136.49.202.53/32'),
            ec2.Port.tcp(80),
            "Http from Ross"
        )
        # may not be relevant if we don't have an SSL cert to use
        alb.connections.allow_from(
            ec2.Peer.ipv4('136.49.202.53/32'),
            ec2.Port.tcp(443),
            "Https from Ross"
        )
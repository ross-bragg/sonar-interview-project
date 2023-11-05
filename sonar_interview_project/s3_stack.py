import aws_cdk as cdk

from aws_cdk import (
    Duration,
    Stack,
    aws_iam as iam,
    aws_s3 as s3
)

from constructs import Construct

from sonar_interview_project.util.config_loader import ConfigLoader

class S3ReplicatedStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, project_config: ConfigLoader, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        project_name = project_config.get("project_name")
        main_region = project_config.get("aws_config").get("main_region")
        dr_region = project_config.get("aws_config").get("dr_region")

        region = cdk.Stack.of(self).region

        source_bucket_name = f"{project_name}-assets-{main_region}"
        source_bucket_arn = f"arn:aws:s3:::{source_bucket_name}"
        source_bucket_objects = f"{source_bucket_arn}/*"

        dest_bucket_name = f"{project_name}-assets-{dr_region}"
        dest_bucket_arn = f"arn:aws:s3:::{dest_bucket_name}"
        dest_bucket_objects = f"{dest_bucket_arn}/*"


        # Primary S3 - cfnBucket because we need to get to the replication configs
        # Secondary S3 - regular bucket

        if self.region == dr_region:
            s3_bucket = s3.Bucket(self, "AssetBucketReplica",
                                    bucket_name=dest_bucket_name,
                                    block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
                                    enforce_ssl=True,
                                    versioned=True,
                                    lifecycle_rules=[
                                        s3.LifecycleRule(
                                            id="DefaultDataLcRule",
                                            abort_incomplete_multipart_upload_after=Duration.days(7),
                                            noncurrent_version_transitions=[
                                                s3.NoncurrentVersionTransition(
                                                    transition_after=Duration.days(2),
                                                    storage_class=s3.StorageClass.INTELLIGENT_TIERING
                                                )
                                            ],  
                                            noncurrent_version_expiration=Duration.days(14)
                                        )       
                                    ]
                                )
            
        elif self.region == main_region:
            # Create repl role for source bucket
            self.replication_role = iam.Role(self, "AssetBucketReplRole",
                                        assumed_by=iam.ServicePrincipal("s3.amazonaws.com")
                                        )
            # Attach repl policy to role
            iam.Policy(self, "AssetBucketReplPolicy",
                        roles=[
                            self.replication_role
                        ],
                        statements=[
                            iam.PolicyStatement(
                                actions=[
                                    "s3:GetReplicationConfiguration",
                                    "s3:ListBucket"
                                ],
                                effect=iam.Effect.ALLOW,
                                resources=[
                                    source_bucket_arn,
                                    dest_bucket_arn
                                ]
                            ),
                            iam.PolicyStatement(
                                actions=[
                                    "s3:GetObjectVersionForReplication",
                                    "s3:GetObjectVersionAcl",
                                    "s3:GetObjectVersionTagging",
                                    "s3:ReplicateObject",
                                    "s3:ReplicateDelete",
                                    "s3:ReplicateTag"
                                ],
                                effect=iam.Effect.ALLOW,
                                resources=[
                                    source_bucket_objects,
                                    dest_bucket_objects
                                ]
                            )
                        ])
            
            replication_config = s3.CfnBucket.ReplicationConfigurationProperty(
                role=self.replication_role.role_arn,
                rules=[
                    s3.CfnBucket.ReplicationRuleProperty(
                        id='asset-replication-rule',
                        destination=s3.CfnBucket.ReplicationDestinationProperty(
                            bucket=dest_bucket_arn
                        ),
                        prefix='',
                        status='Enabled'
                    )
                ]
            )
            
            s3_bucket = s3.CfnBucket(self, "AssetBucket",
                                        bucket_name=source_bucket_name,
                                        access_control='Private',
                                        versioning_configuration=s3.CfnBucket.VersioningConfigurationProperty(
                                            status='Enabled'
                                        ),
                                        replication_configuration=replication_config
                                    )


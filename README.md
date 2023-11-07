
# The Sonar Interview Project

This project deploys the infrastructure requested by the assignment.

# Deployment instructions

Create a config yaml file in the `project-config` directory. Update the accounts/regions accordingly, and update the nat_gateways to 3, db readers to 2, and ecs cluster config to min/max 3. The image deployed is any publicly available docker image.

Run CDK synth referencing that file: `cdk synth -c project=base` where base is the name of the config file (`base.yml`). All deploy commands etc need to be appended with that context flag.

Deploy the base infra, s3, and SG stacks, making sure to do the S3 DR stack before the regular S3 stack. The replication destination bucket has to exist before a replicaton rule can be configured.

Deploy the DB stack, then the DB DR stack. The DB stack will create an Aurora Global database in the main region, and the DR stack will create a smaller cluster in the recovery region.

# Disaster Recovery

S3 is automatically replicated.

Thanks to Aurora Global, the database is already replicated from us-east-1 to us-west-2.

To recover the database, deploy the Project DB DR stack with the context `is_disaster=true`, e.g. `cdk deploy sonar-proj-1GlobalDbDr -c project=base -c is_disaster=true`. 

Wait for the new instances to come up. Once the new instances are avaialble you can failover the database:

Go into the RDS console and run the DB Switchover command on the Global Database, selecting your DR region as the new priamry. AWS does the rest.

Deploy the DR ASG and ECS service stacks.

From here, I make the assumption that whatever top-level DNS pointing to the service would be updated to the new DR ALB.

# Issues I had/Caveats

You can't update the autoscaling group for the ECS cluster, at least through Cloudformation. At my current place, we have a whole separate process that builds a whole new ECS cluster and copies the existing ECS Service into a new one when a change to the ASG (New instance type, new AMI) is made.

There are two main issues I think I had with this:

* Modifying shared resources - I expected to be able to pass the SGs around and modify them as needed when they're used, i.e. create a DB SG in the DB stack, import it into the ECS ASG stack, and grant DB-ASG access on _both_ security groups. I'm not sure if the right answer is ordering (precreating/puplating the SGs and passing them to consuming resources) or some other thing. 

This is also why the IAM roles aren't added to the S3 bucket- we need to modify the Bucket Policy and that would involve either reaching back or pre-computing the IAM roles that need access. I could also do these things like the security groups (create and populate ahead of time, pass to ECS cluster/ASG at creation time) but I just realized this about 2 hours before this is due.

* I realized too late that the _correct_ way to do the DR DB is to create a DB cluster construct and join it to the existing Aurora Global cluster. This would allow us a truly headless Aurora cluster in the DR region that we could then add instances to for DR instead of having one running and have more control over the DB secret.

## Other potential improvements

* A potential addition is to put a JsonSchema in the config loader. This will help catch config errors earlier than runtime validation. Additionally, validation and testing of the stacks.

* in the ecs service stack, I address parameters differently than in other stacks (region-hardcoded config names vs "is main region or dr region?"). This should be fixed.
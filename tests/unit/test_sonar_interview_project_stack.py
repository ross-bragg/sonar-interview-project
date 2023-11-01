import aws_cdk as core
import aws_cdk.assertions as assertions

from sonar_interview_project.sonar_interview_project_stack import SonarInterviewProjectStack

# example tests. To run these tests, uncomment this file along with the example
# resource in sonar_interview_project/sonar_interview_project_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = SonarInterviewProjectStack(app, "sonar-interview-project")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })

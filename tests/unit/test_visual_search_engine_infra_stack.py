import aws_cdk as core
import aws_cdk.assertions as assertions

from visual_search_engine_infra.visual_search_engine_infra_stack import VisualSearchEngineInfraStack


# example tests. To run these tests, uncomment this file along with the example
# resource in visual_search_engine_infra/visual_search_engine_infra_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = VisualSearchEngineInfraStack(app, "visual-search-engine-infra")
    template = assertions.Template.from_stack(stack)

    template.has_resource_properties("AWS::SageMaker::Domain")

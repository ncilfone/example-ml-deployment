#!/usr/bin/env python
from constructs import Construct
from endpoint import SMEndpointConstruct
from cdktf import App, TerraformStack, TerraformVariable, TerraformOutput
from info import AWSInfo, BlueGreenInfo, AutoscalingInfo

from cdktf_cdktf_provider_aws.provider import AwsProvider
from cdktf import DataTerraformRemoteStateS3


class SMEndpointStack(TerraformStack):
    def __init__(
            self,
            scope: Construct,
            id: str,
            model_name: str,
            aws_info: AWSInfo,
            bg_info: BlueGreenInfo,
            autoscaling_info: AutoscalingInfo,
        ) -> None:
        super().__init__(scope, id)

        self.provider = AwsProvider(
            self,
            "AWS",
            region=aws_info.region,
            allowed_account_ids=[aws_info.account]
        )

        # assumes existing DDB
        self.remote_state = DataTerraformRemoteStateS3(
            self,
            "remote_state",
            encrypt=True,
            bucket=f"{aws_info.tf_bucket}-terraform-s3",
            key=f"infra/endpoints/{aws_info.env}/{aws_info.region}/terraform.tfstate",
            region=aws_info.region.
            dynamodb_table="sm-endpoints-tflock"
        )

        self.ecr_image = TerraformVariable(
            self,
            "ecr_image_path",
            nullable=False,
            type='string'
        )

        self.sm_endpoint = SMEndpointConstruct(
            self,
            "{name}-Endpoint",
            aws_info=aws_info,
            bg_info=bg_info,
            autoscaling_info=autoscaling_info,
            model_name=model_name,
            ecr_image=self.ecr_image
        )

        # Would need to do some API GW stuff here but that's a lot to show
        # Most importantly if using a shared stage we need to manage the stage separately from
        # the deployment and manage a hash to figure out when to update the API GW stage since it's
        # a snapshot in time across all endpoints
        # STUFF...

        # Throw some outputs to consume later
        TerraformOutput(
            self,
            "endpoint_name",
            value=self.sm_endpoint.endpoint.name
        )


app = App()
SMEndpointStack(app, "example-ml-deployment")
app.synth()
from constructs import Construct
from cdktf import TerraformResourceLifecycle, TerraformVariable
from cdktf_cdktf_provider_aws.sagemaker_model import (
    SagemakerModel,
    SagemakerModelPrimaryContainer,
    SagemakerModelVpcConfig
)
from cdktf_cdktf_provider_aws.sagemaker_endpoint_configuration import (
    SagemakerEndpointConfiguration
)
from cdktf_cdktf_provider_aws.sagemaker_endpoint import (
    SagemakerEndpoint,
    SagemakerEndpointDeploymentConfig,
    SagemakerEndpointDeploymentConfigBlueGreenUpdatePolicy,
    SagemakerEndpointDeploymentConfigBlueGreenUpdatePolicyTrafficRoutingConfiguration
)
from cdktf_cdktf_provider_aws.appautoscaling_target import AppautoscalingTarget
from cdktf_cdktf_provider_aws.appautoscaling_policy import (
    AppautoscalingPolicy,
    AppautoscalingPolicyTargetTrackingScalingPolicyConfiguration,
    AppautoscalingPolicyTargetTrackingScalingPolicyConfigurationPredefinedMetricSpecification,
)

from info import AWSInfo, BlueGreenInfo, AutoscalingInfo


class SMModelConstruct(Construct):
    primary_container: SagemakerModelPrimaryContainer
    model: SagemakerModel

    def __init__(
            self,
            scope: Construct,
            id: str,
            ecr_image: str,
            model_name: str,
            aws_info: AWSInfo,
            vpc_config: SagemakerModelVpcConfig
        ) -> None:
        super().__init__(scope, id)

        self.primary_container = SagemakerModelPrimaryContainer(
            image=ecr_image, model_data_url=aws_info.s3_path
        )

        self.model = SagemakerModel(
            self,
            "SM-Model",
            name=model_name,
            primary_container=self.primary_container,
            execution_role_arn=aws_info.execution_role,
            vpc_config=vpc_config,
            lifecycle=TerraformResourceLifecycle(
                replace_triggered_by=[
                    f"terraform_data.replacement_{model_name}"
                ]
            )
        )


class SMEndpointConstruct(Construct):
    
    def __init__(
            self,
            scope: Construct,
            id: str,
            aws_info: AWSInfo,
            bg_info: BlueGreenInfo,
            autoscaling_info: AutoscalingInfo,
            model_name: str,
            ecr_image: TerraformVariable
        ) -> None:
        super().__init__(scope, id)

        self.vpc_config = SagemakerModelVpcConfig(
            security_group_ids=aws_info.security_group_ids,
            subnets=aws_info.subnets
        )

        self.primary_model = SMModelConstruct(
            self,
            "SM-Model-Primary",
            ecr_image=ecr_image,
            vpc_config=self.vpc_config,
            aws_info=aws_info,
            model_name=model_name
        )
        depends = [self.primary_model]
        self.endpoint_config = SagemakerEndpointConfiguration(
            self,
            "SM-Endpoint-Config",
            name=model_name
            production_variants=[self.primary_model],
            shadow_production_variants=None,
            lifecycle=TerraformResourceLifecycle(create_before_destroy=True),
            depends_on=depends
        )
        depends.append(self.endpoint_config)
        self.endpoint = SagemakerEndpoint(
            self,
            "SM-Endpoint",
            name=model_name,
            endpoint_config_name=self.endpoint_config.name,
            depends_on=depends,
            deployment_config=SagemakerEndpointDeploymentConfig(
                blue_green_update_policy=SagemakerEndpointDeploymentConfigBlueGreenUpdatePolicy(
                    traffic_routing_configuration=SagemakerEndpointDeploymentConfigBlueGreenUpdatePolicyTrafficRoutingConfiguration(
                        type=bg_info.route_strategy,
                        wait_interval_in_seconds=bg_info.wait_interval
                    ),
                    maximum_execution_timeout_in_seconds=bg_info.max_exec_timeout,
                    termination_wait_in_seconds=bg_info.term_wait
                )
            )
        )
        depends.append(self.endpoint)
        self.autoscaling_target = AppautoscalingTarget(
            self,
            "Autoscaling-Target",
            min_capacity=autoscaling_info.min_instance,
            max_capacity=autoscaling_info.max_instance,
            resource_id=f"endpoint/{self.endpoint.name}/variant/main",
            role_arn=f"arn:aws:iam::{aws_info.account}:role/sagemaker.application-autoscaling.amazonaws.com/AWSServiceRoleForApplicationAutoScaling_SageMakerEndpoint",
            scalable_dimension="sagemaker:variant:DesiredInstanceCount",
            service_namespace="sagemaker",
            depends_on=depends
        )
        depends.append(self.autoscaling)
        self.autoscaling_policy = AppautoscalingPolicy(
            self,
            "Autoscaling-Policy",
            name=f"{self.endpoint.name}-as-policy",
            policy_type="TargetTrackingScaling",
            resource_id=self.autoscaling_target.resource_id,
            scalable_dimension=self.autoscaling_target.scalable_dimension,
            service_namespace=self.autoscaling_target.service_namespace,
            target_tracking_scaling_policy_configuration=AppautoscalingPolicyTargetTrackingScalingPolicyConfiguration(
                predefined_metric_specification=AppautoscalingPolicyTargetTrackingScalingPolicyConfigurationPredefinedMetricSpecification(
                    predefined_metric_type="SageMakerVariantCPUUtilizationNormalized"
                ),
                target_value=autoscaling_info.target_value,
                scale_in_cooldown=autoscaling_info.scale_in_cooldown,
                scale_out_cooldown=autoscaling_info.scale_out_cooldown
            )
        )

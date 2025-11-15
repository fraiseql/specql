"""
CloudFormation Generator

Generates AWS CloudFormation templates from universal infrastructure format.
"""

import json
from typing import Dict, Any
from src.infrastructure.universal_infra_schema import UniversalInfrastructure, DatabaseType


class CloudFormationGenerator:
    """Generate CloudFormation templates from universal format"""

    def generate(self, infrastructure: UniversalInfrastructure) -> str:
        """Generate CloudFormation template"""
        template = {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Description": f"CloudFormation template for {infrastructure.name}",
            "Parameters": self._generate_parameters(infrastructure),
            "Resources": self._generate_resources(infrastructure),
            "Outputs": self._generate_outputs(infrastructure)
        }

        return json.dumps(template, indent=2, sort_keys=False)

    def _generate_parameters(self, infrastructure: UniversalInfrastructure) -> Dict[str, Any]:
        """Generate CloudFormation parameters"""
        parameters = {}

        if infrastructure.database:
            parameters["DBPassword"] = {
                "Type": "String",
                "Description": "Password for the database",
                "NoEcho": True
            }

        return parameters

    def _generate_resources(self, infrastructure: UniversalInfrastructure) -> Dict[str, Any]:
        """Generate CloudFormation resources"""
        resources = {}

        # VPC and Networking
        if infrastructure.network:
            resources.update(self._generate_network_resources(infrastructure))

        # Security Groups
        resources.update(self._generate_security_groups(infrastructure))

        # Compute resources
        if infrastructure.compute:
            resources.update(self._generate_compute_resources(infrastructure))

        # Database
        if infrastructure.database:
            resources.update(self._generate_database_resources(infrastructure))

        # Load Balancer
        if infrastructure.load_balancer:
            resources.update(self._generate_load_balancer_resources(infrastructure))

        return resources

    def _generate_network_resources(self, infrastructure: UniversalInfrastructure) -> Dict[str, Any]:
        """Generate VPC, subnets, and networking resources"""
        resources = {}

        # VPC
        resources[f"{infrastructure.name}VPC"] = {
            "Type": "AWS::EC2::VPC",
            "Properties": {
                "CidrBlock": infrastructure.network.vpc_cidr,
                "EnableDnsHostnames": True,
                "EnableDnsSupport": True,
                "Tags": [
                    {"Key": "Name", "Value": f"{infrastructure.name}-vpc"}
                ]
            }
        }

        # Internet Gateway
        resources[f"{infrastructure.name}InternetGateway"] = {
            "Type": "AWS::EC2::InternetGateway",
            "Properties": {
                "Tags": [
                    {"Key": "Name", "Value": f"{infrastructure.name}-igw"}
                ]
            }
        }

        # Attach IGW to VPC
        resources[f"{infrastructure.name}VPCGatewayAttachment"] = {
            "Type": "AWS::EC2::VPCGatewayAttachment",
            "Properties": {
                "VpcId": {"Ref": f"{infrastructure.name}VPC"},
                "InternetGatewayId": {"Ref": f"{infrastructure.name}InternetGateway"}
            }
        }

        # Public Subnets
        for i, subnet_cidr in enumerate(infrastructure.network.public_subnets):
            resources[f"{infrastructure.name}PublicSubnet{i+1}"] = {
                "Type": "AWS::EC2::Subnet",
                "Properties": {
                    "VpcId": {"Ref": f"{infrastructure.name}VPC"},
                    "CidrBlock": subnet_cidr,
                    "AvailabilityZone": {"Fn::Select": [i, {"Fn::GetAZs": ""}]},
                    "MapPublicIpOnLaunch": True,
                    "Tags": [
                        {"Key": "Name", "Value": f"{infrastructure.name}-public-{i+1}"}
                    ]
                }
            }

        # Private Subnets
        for i, subnet_cidr in enumerate(infrastructure.network.private_subnets):
            resources[f"{infrastructure.name}PrivateSubnet{i+1}"] = {
                "Type": "AWS::EC2::Subnet",
                "Properties": {
                    "VpcId": {"Ref": f"{infrastructure.name}VPC"},
                    "CidrBlock": subnet_cidr,
                    "AvailabilityZone": {"Fn::Select": [i, {"Fn::GetAZs": ""}]},
                    "Tags": [
                        {"Key": "Name", "Value": f"{infrastructure.name}-private-{i+1}"}
                    ]
                }
            }

        # NAT Gateway (if enabled)
        if infrastructure.network.enable_nat_gateway:
            resources[f"{infrastructure.name}EIP"] = {
                "Type": "AWS::EC2::EIP",
                "Properties": {
                    "Domain": "vpc"
                }
            }

            resources[f"{infrastructure.name}NATGateway"] = {
                "Type": "AWS::EC2::NatGateway",
                "Properties": {
                    "AllocationId": {"Fn::GetAtt": [f"{infrastructure.name}EIP", "AllocationId"]},
                    "SubnetId": {"Ref": f"{infrastructure.name}PublicSubnet1"}
                }
            }

        # Route Tables
        resources[f"{infrastructure.name}PublicRouteTable"] = {
            "Type": "AWS::EC2::RouteTable",
            "Properties": {
                "VpcId": {"Ref": f"{infrastructure.name}VPC"},
                "Tags": [
                    {"Key": "Name", "Value": f"{infrastructure.name}-public-rt"}
                ]
            }
        }

        resources[f"{infrastructure.name}PublicRoute"] = {
            "Type": "AWS::EC2::Route",
            "Properties": {
                "RouteTableId": {"Ref": f"{infrastructure.name}PublicRouteTable"},
                "DestinationCidrBlock": "0.0.0.0/0",
                "GatewayId": {"Ref": f"{infrastructure.name}InternetGateway"}
            }
        }

        # Route Table Associations
        for i in range(len(infrastructure.network.public_subnets)):
            resources[f"{infrastructure.name}PublicSubnet{i+1}RouteTableAssociation"] = {
                "Type": "AWS::EC2::SubnetRouteTableAssociation",
                "Properties": {
                    "SubnetId": {"Ref": f"{infrastructure.name}PublicSubnet{i+1}"},
                    "RouteTableId": {"Ref": f"{infrastructure.name}PublicRouteTable"}
                }
            }

        return resources

    def _generate_security_groups(self, infrastructure: UniversalInfrastructure) -> Dict[str, Any]:
        """Generate security groups"""
        resources = {}

        # Load Balancer Security Group
        if infrastructure.load_balancer:
            resources[f"{infrastructure.name}LoadBalancerSecurityGroup"] = {
                "Type": "AWS::EC2::SecurityGroup",
                "Properties": {
                    "GroupDescription": "Security group for load balancer",
                    "VpcId": {"Ref": f"{infrastructure.name}VPC"},
                    "SecurityGroupIngress": [
                        {
                            "IpProtocol": "tcp",
                            "FromPort": 80,
                            "ToPort": 80,
                            "CidrIp": "0.0.0.0/0"
                        }
                    ] + ([
                        {
                            "IpProtocol": "tcp",
                            "FromPort": 443,
                            "ToPort": 443,
                            "CidrIp": "0.0.0.0/0"
                        }
                    ] if infrastructure.load_balancer.https else []),
                    "Tags": [
                        {"Key": "Name", "Value": f"{infrastructure.name}-lb-sg"}
                    ]
                }
            }

        # Application Security Group
        resources[f"{infrastructure.name}ApplicationSecurityGroup"] = {
            "Type": "AWS::EC2::SecurityGroup",
            "Properties": {
                "GroupDescription": "Security group for application instances",
                "VpcId": {"Ref": f"{infrastructure.name}VPC"},
                "SecurityGroupIngress": [
                    {
                        "IpProtocol": "tcp",
                        "FromPort": infrastructure.container.port if infrastructure.container else 80,
                        "ToPort": infrastructure.container.port if infrastructure.container else 80,
                        "SourceSecurityGroupId": {"Ref": f"{infrastructure.name}LoadBalancerSecurityGroup"} if infrastructure.load_balancer else {"CidrIp": "0.0.0.0/0"}
                    }
                ],
                "Tags": [
                    {"Key": "Name", "Value": f"{infrastructure.name}-app-sg"}
                ]
            }
        }

        # Database Security Group
        if infrastructure.database:
            resources[f"{infrastructure.name}DatabaseSecurityGroup"] = {
                "Type": "AWS::EC2::SecurityGroup",
                "Properties": {
                    "GroupDescription": "Security group for database",
                    "VpcId": {"Ref": f"{infrastructure.name}VPC"},
                    "SecurityGroupIngress": [
                        {
                            "IpProtocol": "tcp",
                            "FromPort": 5432,
                            "ToPort": 5432,
                            "SourceSecurityGroupId": {"Ref": f"{infrastructure.name}ApplicationSecurityGroup"}
                        }
                    ],
                    "Tags": [
                        {"Key": "Name", "Value": f"{infrastructure.name}-db-sg"}
                    ]
                }
            }

        return resources

    def _generate_compute_resources(self, infrastructure: UniversalInfrastructure) -> Dict[str, Any]:
        """Generate EC2 Auto Scaling Group"""
        resources = {}

        # Launch Template
        launch_template = {
            "Type": "AWS::EC2::LaunchTemplate",
            "Properties": {
                "LaunchTemplateName": f"{infrastructure.name}-lt",
                "LaunchTemplateData": {
                    "ImageId": {"Fn::FindInMap": ["RegionMap", {"Ref": "AWS::Region"}, "AMI"]},
                    "InstanceType": self._map_instance_type(infrastructure.compute),
                    "SecurityGroupIds": [{"Ref": f"{infrastructure.name}ApplicationSecurityGroup"}],
                    "TagSpecifications": [
                        {
                            "ResourceType": "instance",
                            "Tags": [
                                {"Key": "Name", "Value": infrastructure.name}
                            ]
                        }
                    ]
                }
            }
        }

        if infrastructure.container:
            launch_template["Properties"]["LaunchTemplateData"]["UserData"] = {
                "Fn::Base64": {
                    "Fn::Sub": f"""#!/bin/bash
apt-get update
apt-get install -y docker.io
docker run -d -p {infrastructure.container.port}:{infrastructure.container.port} {infrastructure.container.image}:{infrastructure.container.tag}
"""
                }
            }

        resources[f"{infrastructure.name}LaunchTemplate"] = launch_template

        # Auto Scaling Group
        asg = {
            "Type": "AWS::AutoScaling::AutoScalingGroup",
            "Properties": {
                "AutoScalingGroupName": f"{infrastructure.name}-asg",
                "LaunchTemplate": {
                    "LaunchTemplateId": {"Ref": f"{infrastructure.name}LaunchTemplate"},
                    "Version": "$Latest"
                },
                "MinSize": str(infrastructure.compute.min_instances),
                "MaxSize": str(infrastructure.compute.max_instances),
                "DesiredCapacity": str(infrastructure.compute.instances),
                "VPCZoneIdentifier": [
                    {"Ref": f"{infrastructure.name}PrivateSubnet{i+1}"}
                    for i in range(len(infrastructure.network.private_subnets))
                ],
                "Tags": [
                    {
                        "Key": "Name",
                        "Value": infrastructure.name,
                        "PropagateAtLaunch": True
                    }
                ]
            }
        }

        if infrastructure.load_balancer:
            asg["Properties"]["TargetGroupARNs"] = [{"Ref": f"{infrastructure.name}TargetGroup"}]

        resources[f"{infrastructure.name}AutoScalingGroup"] = asg

        # Auto Scaling Policy
        resources[f"{infrastructure.name}ScaleUpPolicy"] = {
            "Type": "AWS::AutoScaling::ScalingPolicy",
            "Properties": {
                "AutoScalingGroupName": {"Ref": f"{infrastructure.name}AutoScalingGroup"},
                "PolicyType": "TargetTrackingScaling",
                "TargetTrackingConfiguration": {
                    "PredefinedMetricSpecification": {
                        "PredefinedMetricType": "ASGAverageCPUUtilization"
                    },
                    "TargetValue": infrastructure.compute.cpu_target
                }
            }
        }

        return resources

    def _generate_database_resources(self, infrastructure: UniversalInfrastructure) -> Dict[str, Any]:
        """Generate RDS database resources"""
        resources = {}

        # DB Subnet Group
        resources[f"{infrastructure.name}DBSubnetGroup"] = {
            "Type": "AWS::RDS::DBSubnetGroup",
            "Properties": {
                "DBSubnetGroupDescription": f"Subnet group for {infrastructure.name} database",
                "SubnetIds": [
                    {"Ref": f"{infrastructure.name}PrivateSubnet{i+1}"}
                    for i in range(len(infrastructure.network.private_subnets))
                ],
                "Tags": [
                    {"Key": "Name", "Value": f"{infrastructure.name}-db-subnet-group"}
                ]
            }
        }

        # RDS Instance
        db_instance = {
            "Type": "AWS::RDS::DBInstance",
            "Properties": {
                "DBInstanceIdentifier": f"{infrastructure.name}-db",
                "DBInstanceClass": infrastructure.database.instance_class or "db.t3.medium",
                "Engine": self._map_database_engine(infrastructure.database.type),
                "EngineVersion": infrastructure.database.version,
                "AllocatedStorage": infrastructure.database.storage.replace('GB', ''),
                "StorageType": infrastructure.database.storage_type,
                "DBName": infrastructure.name.replace('-', '_'),
                "MasterUsername": "admin",
                "MasterUserPassword": {"Ref": "DBPassword"},
                "MultiAZ": infrastructure.database.multi_az,
                "BackupRetentionPeriod": infrastructure.database.backup_retention_days,
                "StorageEncrypted": infrastructure.security.encryption_at_rest,
                "PubliclyAccessible": infrastructure.database.publicly_accessible,
                "VPCSecurityGroups": [{"Ref": f"{infrastructure.name}DatabaseSecurityGroup"}],
                "DBSubnetGroupName": {"Ref": f"{infrastructure.name}DBSubnetGroup"},
                "Tags": [
                    {"Key": "Name", "Value": f"{infrastructure.name}-database"}
                ]
            }
        }

        resources[f"{infrastructure.name}DBInstance"] = db_instance

        return resources

    def _generate_load_balancer_resources(self, infrastructure: UniversalInfrastructure) -> Dict[str, Any]:
        """Generate Load Balancer resources"""
        resources = {}

        # Application Load Balancer
        resources[f"{infrastructure.name}LoadBalancer"] = {
            "Type": "AWS::ElasticLoadBalancingV2::LoadBalancer",
            "Properties": {
                "Name": f"{infrastructure.name}-lb",
                "Type": infrastructure.load_balancer.type,
                "Scheme": "internet-facing",
                "SecurityGroups": [{"Ref": f"{infrastructure.name}LoadBalancerSecurityGroup"}],
                "Subnets": [
                    {"Ref": f"{infrastructure.name}PublicSubnet{i+1}"}
                    for i in range(len(infrastructure.network.public_subnets))
                ]
            }
        }

        # Target Group
        resources[f"{infrastructure.name}TargetGroup"] = {
            "Type": "AWS::ElasticLoadBalancingV2::TargetGroup",
            "Properties": {
                "Name": f"{infrastructure.name}-tg",
                "Protocol": "HTTP",
                "Port": infrastructure.container.port if infrastructure.container else 80,
                "VpcId": {"Ref": f"{infrastructure.name}VPC"},
                "HealthCheckPath": infrastructure.load_balancer.health_check_path
            }
        }

        # Listener
        listener = {
            "Type": "AWS::ElasticLoadBalancingV2::Listener",
            "Properties": {
                "LoadBalancerArn": {"Ref": f"{infrastructure.name}LoadBalancer"},
                "Protocol": "HTTP",
                "Port": 80,
                "DefaultActions": [
                    {
                        "Type": "forward",
                        "TargetGroupArn": {"Ref": f"{infrastructure.name}TargetGroup"}
                    }
                ]
            }
        }

        resources[f"{infrastructure.name}Listener"] = listener

        return resources

    def _generate_outputs(self, infrastructure: UniversalInfrastructure) -> Dict[str, Any]:
        """Generate CloudFormation outputs"""
        outputs = {
            "VPCId": {
                "Description": "VPC ID",
                "Value": {"Ref": f"{infrastructure.name}VPC"},
                "Export": {"Name": f"{infrastructure.name}-vpc-id"}
            }
        }

        if infrastructure.load_balancer:
            outputs["LoadBalancerDNS"] = {
                "Description": "Load Balancer DNS Name",
                "Value": {"Fn::GetAtt": [f"{infrastructure.name}LoadBalancer", "DNSName"]},
                "Export": {"Name": f"{infrastructure.name}-lb-dns"}
            }

        if infrastructure.database:
            outputs["DatabaseEndpoint"] = {
                "Description": "Database Endpoint",
                "Value": {"Fn::GetAtt": [f"{infrastructure.name}DBInstance", "Endpoint.Address"]},
                "Export": {"Name": f"{infrastructure.name}-db-endpoint"}
            }

        return outputs

    def _map_instance_type(self, compute_config) -> str:
        """Map universal compute config to AWS instance type"""
        if compute_config.instance_type:
            return compute_config.instance_type

        cpu = compute_config.cpu
        memory_gb = int(compute_config.memory.replace("GB", "").replace("MB", "")) / 1000 if "MB" in compute_config.memory else int(compute_config.memory.replace("GB", ""))

        if cpu <= 1 and memory_gb <= 2:
            return "t3.small"
        elif cpu <= 2 and memory_gb <= 4:
            return "t3.medium"
        elif cpu <= 4 and memory_gb <= 8:
            return "t3.large"
        else:
            return "t3.xlarge"

    def _map_database_engine(self, db_type: DatabaseType) -> str:
        """Map universal database type to AWS RDS engine"""
        engine_map = {
            DatabaseType.POSTGRESQL: "postgres",
            DatabaseType.MYSQL: "mysql",
            DatabaseType.REDIS: "redis",
            DatabaseType.ELASTICSEARCH: "elasticsearch",
        }
        return engine_map.get(db_type, "postgres")
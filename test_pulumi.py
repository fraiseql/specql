"""Pulumi infrastructure as code"""

import pulumi
import pulumi_aws as aws

# Configuration
config = pulumi.Config()


# VPC and Networking
vpc = aws.ec2.Vpc("test-app-vpc",
    cidr_block="10.0.0.0/16",
    enable_dns_hostnames=True,
    enable_dns_support=True,
    tags={
        "Name": "test-app-vpc"
    }
)

igw = aws.ec2.InternetGateway("test-app-igw",
    vpc_id=vpc.id,
    tags={
        "Name": "test-app-igw"    }
)

public_subnet_1 = aws.ec2.Subnet("test-app-public-1",
    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",
    availability_zone=data_aws_availability_zones.available.names[0],
    map_public_ip_on_launch=True,
    tags={
        "Name": "test-app-public-1"    }
)

public_subnet_2 = aws.ec2.Subnet("test-app-public-2",
    vpc_id=vpc.id,
    cidr_block="10.0.2.0/24",
    availability_zone=data_aws_availability_zones.available.names[1],
    map_public_ip_on_launch=True,
    tags={
        "Name": "test-app-public-2"    }
)

private_subnet_1 = aws.ec2.Subnet("test-app-private-1",
    vpc_id=vpc.id,
    cidr_block="10.0.10.0/24",
    availability_zone=data_aws_availability_zones.available.names[0],
    tags={
        "Name": "test-app-private-1"    }
)

private_subnet_2 = aws.ec2.Subnet("test-app-private-2",
    vpc_id=vpc.id,
    cidr_block="10.0.20.0/24",
    availability_zone=data_aws_availability_zones.available.names[1],
    tags={
        "Name": "test-app-private-2"    }
)

public_rt = aws.ec2.RouteTable("test-app-public-rt",
    vpc_id=vpc.id,
    routes=[{
        "cidr_block": "0.0.0.0/0",
        "gateway_id": igw.id
    }],
    tags={
        "Name": "test-app-public-rt"    }
)

public_rta_1 = aws.ec2.RouteTableAssociation("test-app-public-rta-1",
    subnet_id=public_subnet_1.id,
    route_table_id=public_rt.id
)
public_rta_2 = aws.ec2.RouteTableAssociation("test-app-public-rta-2",
    subnet_id=public_subnet_2.id,
    route_table_id=public_rt.id
)

eip = aws.ec2.Eip("test-app-eip", vpc=True)

nat_gw = aws.ec2.NatGateway("test-app-nat",
    allocation_id=eip.id,
    subnet_id=public_subnet_1.id,
    tags={
        "Name": "test-app-nat"    }
)

private_rt = aws.ec2.RouteTable("test-app-private-rt",
    vpc_id=vpc.id,
    routes=[{
        "cidr_block": "0.0.0.0/0",
        "nat_gateway_id": nat_gw.id
    }],
    tags={
        "Name": "test-app-private-rt"    }
)

private_rta_1 = aws.ec2.RouteTableAssociation("test-app-private-rta-1",
    subnet_id=private_subnet_1.id,
    route_table_id=private_rt.id
)
private_rta_2 = aws.ec2.RouteTableAssociation("test-app-private-rta-2",
    subnet_id=private_subnet_2.id,
    route_table_id=private_rt.id
)

data_aws_availability_zones = aws.get_availability_zones(
    state="available"
)

# Security Groups
lb_sg = aws.ec2.SecurityGroup("test-app-lb-sg",
    name_prefix=f"{infrastructure.name}-lb-",
    vpc_id=vpc.id,
    ingress=[{
        "protocol": "tcp",
        "from_port": 80,
        "to_port": 80,
        "cidr_blocks": ["0.0.0.0/0"]
    }],
    egress=[{
        "protocol": "-1",
        "from_port": 0,
        "to_port": 0,
        "cidr_blocks": ["0.0.0.0/0"]
    }],
    tags={
        "Name": "test-app-lb-sg"    }
)

app_sg = aws.ec2.SecurityGroup("test-app-app-sg",
    name_prefix=f"{infrastructure.name}-app-",
    vpc_id=vpc.id,
    ingress=[{
        "protocol": "tcp",
        "from_port": 80,
        "to_port": 80,
        "security_groups": [lb_sg.id]
    }],
    egress=[{
        "protocol": "-1",
        "from_port": 0,
        "to_port": 0,
        "cidr_blocks": ["0.0.0.0/0"]
    }],
    tags={
        "Name": "test-app-app-sg"    }
)

db_sg = aws.ec2.SecurityGroup("test-app-db-sg",
    name_prefix=f"{infrastructure.name}-db-",
    vpc_id=vpc.id,
    ingress=[{
        "protocol": "tcp",
        "from_port": 5432,
        "to_port": 5432,
        "security_groups": [app_sg.id]
    }],
    egress=[{
        "protocol": "-1",
        "from_port": 0,
        "to_port": 0,
        "cidr_blocks": ["0.0.0.0/0"]
    }],
    tags={
        "Name": "test-app-db-sg"    }
)


# Compute Resources
launch_template = aws.ec2.LaunchTemplate("test-app-lt",
    name_prefix="test-app-",
    image_id=aws.ec2.get_ami(
        most_recent=True,
        owners=["099720109477"],
        filters=[{
            "name": "name",
            "values": ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
        }]
    ).id,
    instance_type="t3.small",
    user_data=pulumi.Output.all().apply(lambda _: """#!/bin/bash
apt-get update
apt-get install -y docker.io
docker run -d \
  -p 80:80 \
  nginx:latest"""),
    vpc_security_group_ids=[app_sg.id],
    tags={
        "Name": "test-app"
    }
)

asg = aws.autoscaling.Group("test-app-asg",
    name="test-app-asg",
    vpc_zone_identifiers=[
        private_subnet_1.id,
        private_subnet_2.id,
    ],
    min_size=1,
    max_size=5,
    desired_capacity=2,
    launch_template={
        "id": launch_template.id,
        "version": "$Latest"
    },
    target_group_arns=[target_group.arn],
    health_check_type="ELB",
    health_check_grace_period=300,
    tags=[{
        "key": "Name",
        "value": "test-app",
        "propagate_at_launch": True
    }],
)

scale_up_policy = aws.autoscaling.Policy("test-app-scale-up",
    autoscaling_group_name=asg.name,
    policy_type="TargetTrackingScaling",
    target_tracking_configuration={
        "predefined_metric_specification": {
            "predefined_metric_type": "ASGAverageCPUUtilization"
        },
        "target_value": 70
    },
)

# Database
db_subnet_group = aws.rds.SubnetGroup("test-app-db-subnet-group",
    subnet_ids=[
        private_subnet_1.id,
        private_subnet_2.id,
    ],
    tags={
        "Name": "test-app-db-subnet-group"    }
)

db_instance = aws.rds.Instance("test-app-db",
    identifier="test-app-db",
    engine="postgres",
    engine_version="15",
    instance_class="db.t3.medium",
    allocated_storage=50,
    storage_type="gp3",
    db_name="test_app",
    username="admin",
    password=config.require_secret("db_password"),
    multi_az=false,
    backup_retention_period=7,
    storage_encrypted=true,
    publicly_accessible=false,
    vpc_security_group_ids=[db_sg.id],
    db_subnet_group_name=db_subnet_group.name,
    tags={
        "Name": "test-app-database"    }
)

# Load Balancer
target_group = aws.lb.TargetGroup("test-app-tg",
    port=80,
    protocol="HTTP",
    vpc_id=vpc.id,
    health_check={
        "path": "/health",
        "interval": 30,
        "timeout": 5,
        "healthy_threshold": 2,
        "unhealthy_threshold": 3
    }},
    tags={
        "Name": "test-app-tg"    }
)

load_balancer = aws.lb.LoadBalancer("test-app-lb",
    name=f"{infrastructure.name}-lb",
    internal=False,
    load_balancer_type="application",
    security_groups=[lb_sg.id],
    subnets=[
        public_subnet_1.id,
        public_subnet_2.id,
    ],
    enable_deletion_protection=True,
    tags={
        "Name": "test-app-lb"    }
)

listener = aws.lb.Listener("test-app-listener",
    load_balancer_arn=load_balancer.arn,
    port=80,
    protocol="HTTP",
    default_actions=[{
        "type": "forward",
        "target_group_arn": target_group.arn
    }],
)

# Exports
pulumi.export("vpc_id", vpc.id)
pulumi.export("load_balancer_dns", load_balancer.dns_name)
pulumi.export("database_endpoint", db_instance.endpoint)
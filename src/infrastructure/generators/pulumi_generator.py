"""
Pulumi Generator

Generates Pulumi programs in Python from universal infrastructure format.
Pulumi supports multiple languages (Python, TypeScript, Go, C#, etc.) but we'll use Python as the primary target.
"""

import textwrap
from typing import List
from src.infrastructure.universal_infra_schema import UniversalInfrastructure, DatabaseType


class PulumiGenerator:
    """Generate Pulumi Python programs from universal format"""

    def generate(self, infrastructure: UniversalInfrastructure) -> str:
        """Generate Pulumi Python program"""
        code_lines = [
            '"""Pulumi infrastructure as code"""',
            "",
            "import pulumi",
            "import pulumi_aws as aws",
            "",
            "# Configuration",
            "config = pulumi.Config()",
            "",
        ]

        # Add VPC and networking
        if infrastructure.network:
            code_lines.extend(self._generate_network_code(infrastructure))

        # Add security groups
        code_lines.extend(self._generate_security_groups_code(infrastructure))

        # Add compute resources
        if infrastructure.compute:
            code_lines.extend(self._generate_compute_code(infrastructure))

        # Add database
        if infrastructure.database:
            code_lines.extend(self._generate_database_code(infrastructure))

        # Add load balancer
        if infrastructure.load_balancer:
            code_lines.extend(self._generate_load_balancer_code(infrastructure))

        # Add exports
        code_lines.extend(self._generate_exports_code(infrastructure))

        return "\n".join(code_lines)

    def _generate_network_code(self, infrastructure: UniversalInfrastructure) -> List[str]:
        """Generate VPC and networking code"""
        code = [
            "",
            "# VPC and Networking",
            f'vpc = aws.ec2.Vpc("{infrastructure.name}-vpc",',
            f'    cidr_block="{infrastructure.network.vpc_cidr}",',
            '    enable_dns_hostnames=True,',
            '    enable_dns_support=True,',
            '    tags={',
            f'        "Name": "{infrastructure.name}-vpc"',
            '    }',
            ')',
            "",
            f'igw = aws.ec2.InternetGateway("{infrastructure.name}-igw",',
            '    vpc_id=vpc.id,',
            '    tags={',
            f'        "Name": "{infrastructure.name}-igw"'
            '    }',
            ')',
            "",
        ]

        # Public subnets
        for i, subnet_cidr in enumerate(infrastructure.network.public_subnets):
            code.extend([
                f'public_subnet_{i+1} = aws.ec2.Subnet("{infrastructure.name}-public-{i+1}",',
                '    vpc_id=vpc.id,',
                f'    cidr_block="{subnet_cidr}",',
                f'    availability_zone=data_aws_availability_zones.available.names[{i}],',
                '    map_public_ip_on_launch=True,',
                '    tags={',
                f'        "Name": "{infrastructure.name}-public-{i+1}"'
                '    }',
                ')',
                "",
            ])

        # Private subnets
        for i, subnet_cidr in enumerate(infrastructure.network.private_subnets):
            code.extend([
                f'private_subnet_{i+1} = aws.ec2.Subnet("{infrastructure.name}-private-{i+1}",',
                '    vpc_id=vpc.id,',
                f'    cidr_block="{subnet_cidr}",',
                f'    availability_zone=data_aws_availability_zones.available.names[{i}],',
                '    tags={',
                f'        "Name": "{infrastructure.name}-private-{i+1}"'
                '    }',
                ')',
                "",
            ])

        # Route tables
        code.extend([
            f'public_rt = aws.ec2.RouteTable("{infrastructure.name}-public-rt",',
            '    vpc_id=vpc.id,',
            '    routes=[{',
            '        "cidr_block": "0.0.0.0/0",',
            '        "gateway_id": igw.id',
            '    }],',
            '    tags={',
            f'        "Name": "{infrastructure.name}-public-rt"'
            '    }',
            ')',
            "",
        ])

        # Route table associations
        for i in range(len(infrastructure.network.public_subnets)):
            code.append(f'public_rta_{i+1} = aws.ec2.RouteTableAssociation("{infrastructure.name}-public-rta-{i+1}",')
            code.append(f'    subnet_id=public_subnet_{i+1}.id,')
            code.append('    route_table_id=public_rt.id')
            code.append(')')

        # NAT Gateway (if enabled)
        if infrastructure.network.enable_nat_gateway:
            code.extend([
                "",
                f'eip = aws.ec2.Eip("{infrastructure.name}-eip", vpc=True)',
                "",
                f'nat_gw = aws.ec2.NatGateway("{infrastructure.name}-nat",',
                '    allocation_id=eip.id,',
                '    subnet_id=public_subnet_1.id,',
                '    tags={',
                f'        "Name": "{infrastructure.name}-nat"'
                '    }',
                ')',
                "",
                f'private_rt = aws.ec2.RouteTable("{infrastructure.name}-private-rt",',
                '    vpc_id=vpc.id,',
                '    routes=[{',
                '        "cidr_block": "0.0.0.0/0",',
                '        "nat_gateway_id": nat_gw.id',
                '    }],',
                '    tags={',
                f'        "Name": "{infrastructure.name}-private-rt"'
                '    }',
                ')',
                "",
            ])

            for i in range(len(infrastructure.network.private_subnets)):
                code.append(f'private_rta_{i+1} = aws.ec2.RouteTableAssociation("{infrastructure.name}-private-rta-{i+1}",')
                code.append(f'    subnet_id=private_subnet_{i+1}.id,')
                code.append('    route_table_id=private_rt.id')
                code.append(')')

        # Data source for availability zones
        code.extend([
            "",
            "data_aws_availability_zones = aws.get_availability_zones(",
            '    state="available"',
            ")",
        ])

        return code

    def _generate_security_groups_code(self, infrastructure: UniversalInfrastructure) -> List[str]:
        """Generate security groups code"""
        code = [
            "",
            "# Security Groups",
        ]

        # Load Balancer Security Group
        if infrastructure.load_balancer:
            code.extend([
                f'lb_sg = aws.ec2.SecurityGroup("{infrastructure.name}-lb-sg",',
                '    name_prefix=f"{infrastructure.name}-lb-",',
                '    vpc_id=vpc.id,',
                '    ingress=[{',
                '        "protocol": "tcp",',
                '        "from_port": 80,',
                '        "to_port": 80,',
                '        "cidr_blocks": ["0.0.0.0/0"]',
                '    }],',
                '    egress=[{',
                '        "protocol": "-1",',
                '        "from_port": 0,',
                '        "to_port": 0,',
                '        "cidr_blocks": ["0.0.0.0/0"]',
                '    }],',
                '    tags={',
                f'        "Name": "{infrastructure.name}-lb-sg"'
                '    }',
                ')',
                "",
            ])

        # Application Security Group
        port = infrastructure.container.port if infrastructure.container else 80
        code.extend([
            f'app_sg = aws.ec2.SecurityGroup("{infrastructure.name}-app-sg",',
            '    name_prefix=f"{infrastructure.name}-app-",',
            '    vpc_id=vpc.id,',
            '    ingress=[{',
            '        "protocol": "tcp",',
            f'        "from_port": {port},',
            f'        "to_port": {port},',
            '        "security_groups": [lb_sg.id]' if infrastructure.load_balancer else '        "cidr_blocks": ["0.0.0.0/0"]',
            '    }],',
            '    egress=[{',
            '        "protocol": "-1",',
            '        "from_port": 0,',
            '        "to_port": 0,',
            '        "cidr_blocks": ["0.0.0.0/0"]',
            '    }],',
            '    tags={',
            f'        "Name": "{infrastructure.name}-app-sg"'
            '    }',
            ')',
            "",
        ])

        # Database Security Group
        if infrastructure.database:
            code.extend([
                f'db_sg = aws.ec2.SecurityGroup("{infrastructure.name}-db-sg",',
                '    name_prefix=f"{infrastructure.name}-db-",',
                '    vpc_id=vpc.id,',
                '    ingress=[{',
                '        "protocol": "tcp",',
                '        "from_port": 5432,',
                '        "to_port": 5432,',
                '        "security_groups": [app_sg.id]',
                '    }],',
                '    egress=[{',
                '        "protocol": "-1",',
                '        "from_port": 0,',
                '        "to_port": 0,',
                '        "cidr_blocks": ["0.0.0.0/0"]',
                '    }],',
                '    tags={',
                f'        "Name": "{infrastructure.name}-db-sg"'
                '    }',
                ')',
                "",
            ])

        return code

    def _generate_compute_code(self, infrastructure: UniversalInfrastructure) -> List[str]:
        """Generate compute resources code"""
        code = [
            "",
            "# Compute Resources",
        ]

        # Launch Template
        launch_template_code = [
            f'launch_template = aws.ec2.LaunchTemplate("{infrastructure.name}-lt",',
            f'    name_prefix="{infrastructure.name}-",',
            '    image_id=aws.ec2.get_ami(',
            '        most_recent=True,',
            '        owners=["099720109477"],',
            '        filters=[{',
            '            "name": "name",',
            '            "values": ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]',
            '        }]',
            '    ).id,',
            f'    instance_type="{self._map_instance_type(infrastructure.compute)}",',
        ]

        if infrastructure.container:
            user_data = textwrap.dedent(f'''
                #!/bin/bash
                apt-get update
                apt-get install -y docker.io
                docker run -d \\
                  -p {infrastructure.container.port}:{infrastructure.container.port} \\
                  {infrastructure.container.image}:{infrastructure.container.tag}
            ''').strip()

            launch_template_code.extend([
                '    user_data=pulumi.Output.all().apply(lambda _: """' + user_data + '"""),'
            ])

        launch_template_code.extend([
            '    vpc_security_group_ids=[app_sg.id],',
            '    tags={',
            f'        "Name": "{infrastructure.name}"',
            '    }',
            ')',
            "",
        ])

        code.extend(launch_template_code)

        # Auto Scaling Group
        asg_code = [
            f'asg = aws.autoscaling.Group("{infrastructure.name}-asg",',
            f'    name="{infrastructure.name}-asg",',
            '    vpc_zone_identifiers=[',
        ]

        for i in range(len(infrastructure.network.private_subnets)):
            asg_code.append(f'        private_subnet_{i+1}.id,')
        asg_code.append('    ],')

        asg_code.extend([
            '    min_size=' + str(infrastructure.compute.min_instances) + ',',
            '    max_size=' + str(infrastructure.compute.max_instances) + ',',
            '    desired_capacity=' + str(infrastructure.compute.instances) + ',',
            '    launch_template={',
            '        "id": launch_template.id,',
            '        "version": "$Latest"',
            '    },',
        ])

        if infrastructure.load_balancer:
            asg_code.append('    target_group_arns=[target_group.arn],')

        asg_code.extend([
            '    health_check_type="ELB",',
            '    health_check_grace_period=300,',
            '    tags=[{',
            '        "key": "Name",',
            f'        "value": "{infrastructure.name}",',
            '        "propagate_at_launch": True',
            '    }],',
            ')',
            "",
        ])

        code.extend(asg_code)

        # Auto Scaling Policy
        code.extend([
            f'scale_up_policy = aws.autoscaling.Policy("{infrastructure.name}-scale-up",',
            '    autoscaling_group_name=asg.name,',
            '    policy_type="TargetTrackingScaling",',
            '    target_tracking_configuration={',
            '        "predefined_metric_specification": {',
            '            "predefined_metric_type": "ASGAverageCPUUtilization"',
            '        },',
            f'        "target_value": {infrastructure.compute.cpu_target}',
            '    },',
            ')',
        ])

        return code

    def _generate_database_code(self, infrastructure: UniversalInfrastructure) -> List[str]:
        """Generate database code"""
        code = [
            "",
            "# Database",
        ]

        # DB Subnet Group
        code.extend([
            f'db_subnet_group = aws.rds.SubnetGroup("{infrastructure.name}-db-subnet-group",',
            '    subnet_ids=[',
        ])

        for i in range(len(infrastructure.network.private_subnets)):
            code.append(f'        private_subnet_{i+1}.id,')
        code.append('    ],')

        code.extend([
            '    tags={',
            f'        "Name": "{infrastructure.name}-db-subnet-group"'
            '    }',
            ')',
            "",
        ])

        # RDS Instance
        db_code = [
            f'db_instance = aws.rds.Instance("{infrastructure.name}-db",',
            f'    identifier="{infrastructure.name}-db",',
            f'    engine="{self._map_database_engine(infrastructure.database.type)}",',
            f'    engine_version="{infrastructure.database.version}",',
            f'    instance_class="{infrastructure.database.instance_class or "db.t3.medium"}",',
            f'    allocated_storage={infrastructure.database.storage.replace("GB", "")},',
            f'    storage_type="{infrastructure.database.storage_type}",',
            f'    db_name="{infrastructure.name.replace("-", "_")}",',
            '    username="admin",',
            '    password=config.require_secret("db_password"),',
            f'    multi_az={str(infrastructure.database.multi_az).lower()},',
            f'    backup_retention_period={infrastructure.database.backup_retention_days},',
            f'    storage_encrypted={str(infrastructure.security.encryption_at_rest).lower()},',
            f'    publicly_accessible={str(infrastructure.database.publicly_accessible).lower()},',
            '    vpc_security_group_ids=[db_sg.id],',
            '    db_subnet_group_name=db_subnet_group.name,',
            '    tags={',
            f'        "Name": "{infrastructure.name}-database"'
            '    }',
            ')',
        ]

        code.extend(db_code)
        return code

    def _generate_load_balancer_code(self, infrastructure: UniversalInfrastructure) -> List[str]:
        """Generate load balancer code"""
        code = [
            "",
            "# Load Balancer",
        ]

        # Target Group
        port = infrastructure.container.port if infrastructure.container else 80
        code.extend([
            f'target_group = aws.lb.TargetGroup("{infrastructure.name}-tg",',
            '    port=' + str(port) + ',',
            '    protocol="HTTP",',
            '    vpc_id=vpc.id,',
            '    health_check={',
            f'        "path": "{infrastructure.load_balancer.health_check_path}",',
            f'        "interval": {infrastructure.load_balancer.health_check_interval},',
            '        "timeout": 5,',
            f'        "healthy_threshold": {infrastructure.load_balancer.healthy_threshold},',
            f'        "unhealthy_threshold": {infrastructure.load_balancer.unhealthy_threshold}',
            '    }},',
            '    tags={',
            f'        "Name": "{infrastructure.name}-tg"'
            '    }',
            ')',
            "",
        ])

        # Load Balancer
        code.extend([
            f'load_balancer = aws.lb.LoadBalancer("{infrastructure.name}-lb",',
            '    name=f"{infrastructure.name}-lb",',
            '    internal=False,',
            f'    load_balancer_type="{infrastructure.load_balancer.type}",',
            '    security_groups=[lb_sg.id],',
            '    subnets=[',
        ])

        for i in range(len(infrastructure.network.public_subnets)):
            code.append(f'        public_subnet_{i+1}.id,')
        code.append('    ],')

        code.extend([
            '    enable_deletion_protection=True,',
            '    tags={',
            f'        "Name": "{infrastructure.name}-lb"'
            '    }',
            ')',
            "",
        ])

        # Listener
        code.extend([
            f'listener = aws.lb.Listener("{infrastructure.name}-listener",',
            '    load_balancer_arn=load_balancer.arn,',
            '    port=80,',
            '    protocol="HTTP",',
            '    default_actions=[{',
            '        "type": "forward",',
            '        "target_group_arn": target_group.arn',
            '    }],',
            ')',
        ])

        return code

    def _generate_exports_code(self, infrastructure: UniversalInfrastructure) -> List[str]:
        """Generate exports"""
        code = [
            "",
            "# Exports",
        ]

        code.append('pulumi.export("vpc_id", vpc.id)')

        if infrastructure.load_balancer:
            code.append('pulumi.export("load_balancer_dns", load_balancer.dns_name)')

        if infrastructure.database:
            code.append('pulumi.export("database_endpoint", db_instance.endpoint)')

        return code

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
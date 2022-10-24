# App Installation and Setup 

The project uses pipenv as a python package manager. Essentially, it's pip and venv combined, once you're in pipenv's virtual environment, just treat pipenv as you would pip commands. For more information see here: https://realpython.com/pipenv-guide/

Clone app repository
```
git clone https://github.com/Vladpetr/Fake-Video-Studios.git
```

Install pipenv (or with homebrew for mac)
```
pip3 install pipenv
```
Create and enter pipenv virtual environment
```
pipenv shell
```
Install Pipfile.lock
```
pipenv install
```
Run the app file to test if you can successfully access the server
```
python app.py
```
Exit virtual environment
```
exit
```


# AWS Architecture Configuration

Create an AWS account (for more details see https://aws.amazon.com/premiumsupport/knowledge-center/create-and-activate-aws-account/).

Install/update AWS CLI (follow instructions here: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html).

Make sure your AWS CLI is properly configured (check this article for more details: https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html#cli-configure-quickstart-creds-create). In this project, the default region is set as "us-east-1".

Create a VPC.
```
aws ec2 create-vpc --cidr-block 10.0.0.0/16 --query Vpc.VpcId --output text
```

Record the id of the newly created VPC.

Start creating subnets. We need to create 6 subnets in total. Three subnets will be located in one availability zone and remaining three will be located in another. This is done for the purposes of replication and fault tolerance. Out of the subnets in each availanility zone, make one subnet public (later will be used by webserver) and another two — private (one for application server (video generator) and another one for database server). Since we have multiple subnets, we need to divide the range of IP addresses established during the VPC creation between 6 subnets.Please refer to the initial architecture diagram for more information.
```
aws ec2 create-subnet --vpc-id [insert your vpc id] --cidr-block 10.0.1.0/24 --availability-zone us-east-1a --tag-specifications "ResourceType=subnet,Tags=[{Key=Name, Value=public-web-subnet-1}]"

aws ec2 create-subnet --vpc-id [insert your vpc id] --cidr-block 10.0.2.0/24 --availability-zone us-east-1b --tag-specifications "ResourceType=subnet,Tags=[{Key=Name, Value=public-web-subnet-2}]"

aws ec2 create-subnet --vpc-id [insert your vpc id] --cidr-block 10.0.3.0/24 --availability-zone us-east-1a --tag-specifications "ResourceType=subnet,Tags=[{Key=Name, Value=private-app-subnet-1}]"

aws ec2 create-subnet --vpc-id [insert your vpc id] --cidr-block 10.0.4.0/24 --availability-zone us-east-1b --tag-specifications "ResourceType=subnet,Tags=[{Key=Name, Value=private-app-subnet-2}]"

aws ec2 create-subnet --vpc-id [insert your vpc id] --cidr-block 10.0.5.0/24 --availability-zone us-east-1a --tag-specifications "ResourceType=subnet,Tags=[{Key=Name, Value=private-db-subnet-1}]"

aws ec2 create-subnet --vpc-id [insert your vpc id] --cidr-block 10.0.6.0/24 --availability-zone us-east-1b --tag-specifications "ResourceType=subnet,Tags=[{Key=Name, Value=private-db-subnet-2}]"
```

Create an Internet gateway for communication between the VPC and the Internet.
```
aws ec2 create-internet-gateway --query InternetGateway.InternetGatewayId --output text 
```

Record the id of the newly created internet gateway.

Attach the internet gateway to the VPC.
```
aws ec2 attach-internet-gateway --vpc-id [insert your vpc id] --internet-gateway-id [insert your interent gateway id]
```

Define route tables for every subnet tier (web, app, database) and establish where the traffic from the subnets is directed.
```
aws ec2 create-route-table --vpc-id [insert your vpc id] --query RouteTable.RouteTableId --output text --tag-specifications "ResourceType=route-table, Tags=[{Key=Name, Value=public-web-route-table}]"

aws ec2 create-route-table --vpc-id [insert your vpc id] --query RouteTable.RouteTableId --output text --tag-specifications "ResourceType=route-table, Tags=[{Key=Name, Value=private-app-route-table-1}]"

aws ec2 create-route-table --vpc-id [insert your vpc id] --query RouteTable.RouteTableId --output text --tag-specifications "ResourceType=route-table, Tags=[{Key=Name, Value=private-app-route-table-2}]"
```

Record the ids of the newly created route tables.

Associate route tables with the corresponding subnets (app route table will be related to app subnets, etc.)
```
aws ec2 associate-route-table --route-table-id [insert web route table id] --subnet-id [insert web subnet 1 id]

aws ec2 associate-route-table --route-table-id [insert web route table id] --subnet-id [insert web subnet 2 id]

aws ec2 associate-route-table --route-table-id [insert app route table 1 id] --subnet-id [insert app subnet 1]

aws ec2 associate-route-table --route-table-id [insert app route table 2 id] --subnet-id [insert app subnet 2]
```

Allocate elastic IP addresses, which allow quick remapping of requests to another instance in case the chosen instance fails (repeat the command twice).
```
aws ec2 allocate-address
```

Record the ids of the newly allocated elastic IP addresses.

Create a public NAT gateway so that instances in private subnets can connect to external services. At the same time, instances in private subnets will not receive traffic from the external services (internet). Create two NAT gateways, one for every public subnet.
```
aws ec2 create-nat-gateway --allocation-id [insert elastic IP address 1] --subnet-id [insert public subnet 1 id] --tag-specifications "ResourceType=natgateway, Tags=[{Key=Name, Value=nat-gateway-1}]" --connectivity-type public

aws ec2 create-nat-gateway --allocation-id [insert elastic IP address 2] --subnet-id [insert public subnet 2 id] --tag-specifications "ResourceType=natgateway, Tags=[{Key=Name, Value=nat-gateway-2}]" --connectivity-type public
```
Make changes to the route tables so that public subnets can connect to the internet through internet gateway and private subnets can do the same through the NAT gateway.
```
aws ec2 create-route --route-table-id [insert public web route table id] --destination-cidr-block 0.0.0.0/0 --gateway-id [insert internet gateway id]

aws ec2 create-route --route-table-id [insert private app route table 1 id] --destination-cidr-block 0.0.0.0/0 --nat-gateway-id [insert NAT gateway 1 id]

aws ec2 create-route --route-table-id [insert private app route table 2 id] --destination-cidr-block 0.0.0.0/0 --nat-gateway-id [insert NAT gateway 2 id]
```

# Security
Initialize a security group for a load balancer that interacts with the public subnets (web tier).
```
aws ec2 create-security-group --description "Web-tier load balancer SG" --group-name web-lb-sg --vpc-id [insert your vpc id]
```

Allow HTTP traffic from any IP address.
```
aws ec2 authorize-security-group-ingress --group-id [insert web tier lb security group id] --protocol tcp --port 80 --cidr 0.0.0.0/0
```

Configure the second security group for public subnets. The traffic rule allows anyone to access the public instances.
```
aws ec2 create-security-group --description "Web-tier SG" --group-name web-tier-sg --vpc-id [insert your vpc id]

aws ec2 authorize-security-group-ingress --group-id [insert web tier security group id] --protocol tcp --port 80 --cidr 0.0.0.0/0
```

Initialize and configure another security group for the app-tier load balancer. In this case, the HTTP traffic is only allowed from the web-tier security group.
```
aws ec2 create-security-group --description "App-tier load balancer SG" --group-name app-lb-sg --vpc-id [insert your vpc id]

Use the GUI (https://us-east-1.console.aws.amazon.com/vpc/home?region=us-east-1#SecurityGroups:) to set the inbound rule because there is an existing bug related to this action via aws cli. Choose the web-tier security group id for "source".
```

Initialize and configure another security group for the app-tier instances. In this case, the TCP traffic is only allowed from the app-tier load balancer.
```
aws ec2 create-security-group --description "App-tier SG" --group-name app-tier-sg --vpc-id [insert your vpc id]

Use the GUI (https://us-east-1.console.aws.amazon.com/vpc/home?region=us-east-1#SecurityGroups:) to set the inbound rule because there is an existing bug related to this action via aws cli. Choose the app-tier load balancer id for "source" and 4000 for "port range".
```

Finish by configuring a security group for database instances. The inbound TCP traffic is only allowed from app-tier instances.
```
aws ec2 create-security-group --description "Db-tier SG" --group-name db-tier-sg --vpc-id [insert your vpc id]

Use the GUI (https://us-east-1.console.aws.amazon.com/vpc/home?region=us-east-1#SecurityGroups:) to set the inbound rule because there is an existing bug related to this action via aws cli. Choose the app-tier security group id for "source", PostgreSQL for "type", and 5432 for "port range".
```

# Deployment of the App Components

Create a key pair for connecting to instances in subnets. Checkout the following resource for more information: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html

## Database tier
(I am not exactly sure what kind of data should be stored in a relational database like RDS in this scenario but I can always delete the instances later).


Create a database subnet group that associates created database instances with VPC. Mention ids of subnets located in database tier.
```
aws rds create-db-subnet-group --db-subnet-group-name db-subnet-group --db-subnet-group-description "DB layer subnet group" --subnet-ids '[insert private database subnet 1 id, insert private database subnet 2 id]'
```

Create a database for availability zone 1. We assume default parameters for the free-tier <b>db.t3.micro</b> instance class.
```
aws rds create-db-instance --db-instance-identifier psql-db-instance --allocated-storage 200 --db-instance-class db.t3.micro --engine postgres --master-username psqladmin --master-user-password [insert password]--availability-zone us-east-1a --db-subnet-group-name db-subnet-group
```

Depending on the database type, user needs, it is possible to create multiple database instances across different availability zones (as shown in the architecture diagram) to increase system fault tolerance. 


## App tier

Create an EC2 instance (Linux 2 AMI and t2.micro type). Connect the VPC, app private subnet 1 and app-tier security group.

```
aws ec2 run-instances --image-id ami-09d3b3274b6c5d4aa --count 1 --instance-type t2.micro --key-name MyKeyPair --subnet-id [insert app private subnet 1 id] --security-group-ids [insert app-tier security group id]
```

Make sure your key file (MyKeyPair.pem) is not publicly viewable.
```
chmod 400 MyKeyPair.pem
```

Locate private IP address of the instance (available in the previous command output). Connect to the app instance to ensure it possible to reach the internet through the NAT gateways.
```
ssh -i "MyKeyPair.pem" ec2-user@[insert your EC2 instance IP address]
```

Ping a public server to ensure the transmission of packets.
```
ping 1.1.1.1
```

I have not implemented scaling and load balancing for this tier. Given the amount of time spent for setting up all components through AWS cli, I would like to recreate my configurations in Terraform for the next assignment. I see how scalability of the system and even its current state already prevent me from making fast changes to the architecture given my current approach.


## Web tier

Create an EC2 instance (Linux 2 AMI and t2.micro type). Connect the VPC, app private subnet 1 and app-tier security group.
```
aws ec2 run-instances --image-id ami-09d3b3274b6c5d4aa --count 1 --instance-type t2.micro --key-name MyKeyPair --subnet-id [insert web public subnet 1 id] --security-group-ids [insert web-tier security group id]
```

Locate public IP address of the instance (available in the previous command output). Connect to the app instance to ensure it possible to reach the internet through the internet gateway.
```
ssh -i "MyKeyPair.pem" ec2-user@[insert your EC2 instance IP address]
```

Ping a public server to ensure the transmission of packets.
```
ping 1.1.1.1
```

I have not implemented scaling and load balancing for this tier. Given the amount of time spent for setting up all components through AWS cli, I would like to recreate my configurations in Terraform for the next assignment. I see how scalability of the system and even its current state already prevent me from making fast changes to the architecture given my current approach.
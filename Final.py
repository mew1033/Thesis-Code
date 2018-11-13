from troposphere import Base64, FindInMap, GetAtt, Join, Output, Select, GetAZs
from troposphere import Parameter, Ref, Tags, Template
from troposphere.autoscaling import Metadata
from troposphere.ec2 import PortRange, NetworkAcl, Route, \
    VPCGatewayAttachment, SubnetRouteTableAssociation, Subnet, RouteTable, \
    VPC, NetworkInterface, NetworkInterfaceProperty, NetworkAclEntry, \
    SubnetNetworkAclAssociation, EIP, EIPAssociation, Instance, InternetGateway, \
    SecurityGroupRule, SecurityGroup
from troposphere.policies import CreationPolicy, ResourceSignal
from troposphere.cloudformation import Init, InitFile, InitFiles, \
    InitConfig, InitService, InitServices

t = Template()

t.add_version('2010-09-09')

t.add_description("""Create the environment""")

t.add_mapping('RegionToInstanceToAMI', {
    'us-east-1': {'firewalld': 'ami-ae7bfdb8',
                  'oldJoomla': 'ami-856f02ec',
                  'domainctl': 'ami-4009963a',
                  'storage': 'ami-08910872',
                  'servercore': 'ami-595fdd23',
                  'freebsd': 'ami-6a4be710',
                  'debworkstation': 'ami-144f4d7c',
                  '2008workstation': 'ami-29049b53'},
    'us-west-1': {'firewalld': 'ami-7c280d1c',
                  'oldJoomla': 'ami-2928076c',
                  'domainctl': 'ami-ec8bb08c',
                  'storage': 'ami-406d5720',
                  'servercore': 'ami-adbf87cd',
                  'freebsd': 'ami-32ae9252',
                  'debworkstation': 'ami-0343ae47',
                  '2008workstation': 'ami-3695ae56'},
    'us-west-2': {'firewalld': 'ami-0c2aba6c',
                  'oldJoomla': 'ami-09e27439',
                  'domainctl': 'ami-c55089bd',
                  'storage': 'ami-f6d8008e',
                  'servercore': 'ami-11bd6169',
                  'freebsd': 'ami-00824a78',
                  'debworkstation': 'ami-0d5b6c3d',
                  '2008workstation': 'ami-a35c85db'},
    'eu-west-1': {'firewalld': 'ami-0d063c6b',
                  'oldJoomla': 'ami-35acbb41',
                  'domainctl': 'ami-30ef5249',
                  'storage': 'ami-e055e899',
                  'servercore': 'ami-d9e254a0',
                  'freebsd': 'ami-bdfc5ac4',
                  'debworkstation': 'ami-99f39eee',
                  '2008workstation': 'ami-a7ed50de'},
    't1.micro': {'Arch': 'PV64'},
    't2.micro': {'Arch': 'HVM64'},
    't2.small': {'Arch': 'HVM64'},
    't2.medium': {'Arch': 'HVM64'},
    'm1.small': {'Arch': 'PV64'},
    'm1.medium': {'Arch': 'PV64'},
    'm1.large': {'Arch': 'PV64'}
})


team_number_param = t.add_parameter(
    Parameter(
        'TeamNumber',
        ConstraintDescription='must be a single number indicating the team number.',
        Description='Team number',
        Type='Number',
    ))

team_number = Ref(team_number_param)

az = Select(0, GetAZs())

VPC = t.add_resource(
    VPC(
        'VPC',
        CidrBlock='10.0.0.0/16',
        Tags=Tags(
            Name=Join(" ", ["VPC For Team", team_number]))))

internetGateway = t.add_resource(
    InternetGateway(
        'InternetGateway',
        Tags=Tags(
            Name=Join(" ", ["Igw for team", team_number]),
            Team=team_number)))

gatewayAttachment = t.add_resource(
    VPCGatewayAttachment(
        'AttachGatewayToVPC',
        VpcId=Ref(VPC),
        InternetGatewayId=Ref(internetGateway)))

Public_DMZ_Subnet = t.add_resource(
    Subnet(
        'PublicDMZSubnet',
        AvailabilityZone=az,
        CidrBlock='10.0.1.0/24',
        VpcId=Ref(VPC),
        MapPublicIpOnLaunch=True,
        Tags=Tags(
            Name=Join(" ", ["Public Subnet for team", team_number]),
            Team=team_number)))

Private_Server_Subnet = t.add_resource(
    Subnet(
        'PrivateServerSubnet',
        AvailabilityZone=az,
        CidrBlock='10.0.2.0/24',
        VpcId=Ref(VPC),
        MapPublicIpOnLaunch=False,
        Tags=Tags(
            Name=Join(" ", ["Private Subnet for team", team_number]),
            Team=team_number)))

Workstation_Subnet = t.add_resource(
    Subnet(
        'WorkstationSubnet',
        AvailabilityZone=az,
        CidrBlock='10.0.3.0/24',
        VpcId=Ref(VPC),
        MapPublicIpOnLaunch=True,
        Tags=Tags(
            Name=Join(" ", ["Workstation Subnet for team", team_number]),
            Team=team_number)))

publicRouteTable = t.add_resource(
    RouteTable(
        'PublicRouteTable',
        VpcId=Ref(VPC),
        Tags=Tags(
            Name=Join(" ", ["Public Route Table for team", team_number]),
            Team=team_number)))

privateRouteTable = t.add_resource(
    RouteTable(
        'PrivateRouteTable',
        VpcId=Ref(VPC),
        Tags=Tags(
            Name=Join(" ", ["Private Route Table for team", team_number]),
            Team=team_number)))


igwRoute = t.add_resource(
    Route(
        'Route',
        DependsOn='AttachGatewayToVPC',
        GatewayId=Ref(internetGateway),
        DestinationCidrBlock='0.0.0.0/0',
        RouteTableId=Ref(publicRouteTable),
    ))


publicDMZSubnetRouteTableAssociation = t.add_resource(
    SubnetRouteTableAssociation(
        'PublicDMZSubnetRouteTableAssociation',
        SubnetId=Ref(Public_DMZ_Subnet),
        RouteTableId=Ref(publicRouteTable),
    ))

workstationSubnetRouteTableAssociation = t.add_resource(
    SubnetRouteTableAssociation(
        'WorkstationSubnetRouteTableAssociation',
        SubnetId=Ref(Workstation_Subnet),
        RouteTableId=Ref(publicRouteTable),
    ))


privateSubnetRouteTableAssociation = t.add_resource(
    SubnetRouteTableAssociation(
        'PrivateSubnetRouteTableAssociation',
        SubnetId=Ref(Private_Server_Subnet),
        RouteTableId=Ref(privateRouteTable),
    ))

globalAllowSecurityGroup = t.add_resource(
    SecurityGroup(
        'GlobalAllowSecurityGroup',
        GroupName='Allow all the things',
        GroupDescription='Allow access to everything, from everything',
        SecurityGroupIngress=[
            SecurityGroupRule(
                IpProtocol='-1',
                CidrIp="0.0.0.0/0"),
        ],
        VpcId=Ref(VPC),
    ))

firewalldPrivateSideInterface = t.add_resource(
    NetworkInterface(
        'firewalldPrivateSideInterface',
        Description=Join(" ", ["Firewalld private side interface for team", team_number]),
        GroupSet=[
            Ref(globalAllowSecurityGroup)],
        PrivateIpAddress="10.0.2.10",
        SourceDestCheck=False,
        SubnetId=Ref(Private_Server_Subnet),
        Tags=Tags(
            Name=Join(" ", ["Team", team_number, "Firewalld Private Side Interface"]),
            Team=team_number)
    ))

firewalldPublicWebInterface = t.add_resource(
    NetworkInterface(
        'firewalldPubliceWebInterface',
        Description=Join(" ", ["Firewalld public web interface for team", team_number]),
        GroupSet=[
            Ref(globalAllowSecurityGroup)],
        PrivateIpAddress="10.0.1.10",
        SourceDestCheck=False,
        SubnetId=Ref(Public_DMZ_Subnet),
        Tags=Tags(
            Name=Join(" ", ["Team", team_number, "Firewalld Public Web Interface"]),
            Team=team_number)
    ))

firewalldPublicNATInterface = t.add_resource(
    NetworkInterface(
        'firewalldPublicNATInterface',
        Description=Join(" ", ["Firewalld public NAT interface for team", team_number]),
        GroupSet=[
            Ref(globalAllowSecurityGroup)],
        PrivateIpAddress="10.0.1.11",
        SourceDestCheck=False,
        SubnetId=Ref(Public_DMZ_Subnet),
        Tags=Tags(
            Name=Join(" ", ["Team", team_number, "Firewalld Public NAT Interface"]),
            Team=team_number)
    ))

firewalldPublicWebEIP = t.add_resource(
    EIP(
        'firewalldPublicWebEIP',
        Domain='vpc',
        DependsOn='VPC'
    ))

firewalldPublicNATEIP = t.add_resource(
    EIP(
        'firewalldPublicNATEIP',
        Domain='vpc',
        DependsOn='VPC'
    ))

firewalldPublicWebEIPAttachment = t.add_resource(
    EIPAssociation(
        'firewalldPublicWebEIPAttachment',
        AllocationId=GetAtt(firewalldPublicWebEIP, "AllocationId"),
        NetworkInterfaceId=Ref(firewalldPublicWebInterface)
    ))

firewalldPublicNATEIPAttachment = t.add_resource(
    EIPAssociation(
        'firewalldPublicNATEIPAttachment',
        AllocationId=GetAtt(firewalldPublicNATEIP, "AllocationId"),
        NetworkInterfaceId=Ref(firewalldPublicNATInterface)
    ))

firewalldInstance = t.add_resource(
    Instance(
        'Firewalld',
        AvailabilityZone=az,
        ImageId=FindInMap(
            'RegionToInstanceToAMI',
            Ref('AWS::Region'),
            'firewalld'),
        InstanceType="t2.medium",
        KeyName="Default key 3-16-16",
        UserData="IyEvYmluL2Jhc2gKc2V0IC14CmV4ZWMgPiA+KHRlZSAvdmFyL2xvZy91c2VyLWRhdGEubG9nICkgMj4mMQplY2hvICJuZXQuaXB2NC5pcF9mb3J3YXJkID0gMSIgPj4gL2V0Yy9zeXNjdGwuY29uZgplY2hvICJuZXQuaXB2NC5jb25mLmFsbC5ycF9maWx0ZXIgPSAwIiA+PiAvZXRjL3N5c2N0bC5jb25mCmVjaG8gIm5ldC5pcHY0LmNvbmYuZGVmYXVsdC5ycF9maWx0ZXIgPSAwIiA+PiAvZXRjL3N5c2N0bC5jb25mCmVjaG8gIm5ldC5pcHY0LmNvbmYuZXRoMC5ycF9maWx0ZXIgPSAwIiA+PiAvZXRjL3N5c2N0bC5jb25mCmVjaG8gIm5ldC5pcHY0LmNvbmYuZXRoMS5ycF9maWx0ZXIgPSAwIiA+PiAvZXRjL3N5c2N0bC5jb25mCmVjaG8gIm5ldC5pcHY0LmNvbmYuZXRoMi5ycF9maWx0ZXIgPSAwIiA+PiAvZXRjL3N5c2N0bC5jb25mCmVjaG8gIm5ldC5pcHY0LmNvbmYubG8ucnBfZmlsdGVyID0gMCIgPj4gL2V0Yy9zeXNjdGwuY29uZgplY2hvIEdBVEVXQVk9MTAuMC4xLjEgPj4gL2V0Yy9zeXNjb25maWcvbmV0d29yawpzeXNjdGwgLXAKCmNwIC9ldGMvc3lzY29uZmlnL25ldHdvcmstc2NyaXB0cy9pZmNmZy1ldGgwIC9ldGMvc3lzY29uZmlnL25ldHdvcmstc2NyaXB0cy9pZmNmZy1ldGgxCnNlZCAtaSAncy8iZXRoMCIvImV0aDEiLycgL2V0Yy9zeXNjb25maWcvbmV0d29yay1zY3JpcHRzL2lmY2ZnLWV0aDEKZWNobyAiSFdBRERSPSQoY2F0IC9zeXMvY2xhc3MvbmV0L2V0aDEvYWRkcmVzcyB8IHRyIC1kICdcbicgfCB0ciAtZCAnICcpIiA+PiAvZXRjL3N5c2NvbmZpZy9uZXR3b3JrLXNjcmlwdHMvaWZjZmctZXRoMQpjcCAvZXRjL3N5c2NvbmZpZy9uZXR3b3JrLXNjcmlwdHMvaWZjZmctZXRoMCAvZXRjL3N5c2NvbmZpZy9uZXR3b3JrLXNjcmlwdHMvaWZjZmctZXRoMgpzZWQgLWkgJ3MvImV0aDAiLyJldGgyIi8nIC9ldGMvc3lzY29uZmlnL25ldHdvcmstc2NyaXB0cy9pZmNmZy1ldGgyCmVjaG8gIkhXQUREUj0kKGNhdCAvc3lzL2NsYXNzL25ldC9ldGgyL2FkZHJlc3MgfCB0ciAtZCAnXG4nIHwgdHIgLWQgJyAnKSIgPj4gL2V0Yy9zeXNjb25maWcvbmV0d29yay1zY3JpcHRzL2lmY2ZnLWV0aDIKZWNobyBaT05FPWludGVybmFsID4+IC9ldGMvc3lzY29uZmlnL25ldHdvcmstc2NyaXB0cy9pZmNmZy1ldGgwCmVjaG8gWk9ORT1leHRlcm5hbCA+PiAvZXRjL3N5c2NvbmZpZy9uZXR3b3JrLXNjcmlwdHMvaWZjZmctZXRoMQplY2hvIFpPTkU9cHVibGljID4+IC9ldGMvc3lzY29uZmlnL25ldHdvcmstc2NyaXB0cy9pZmNmZy1ldGgyCnNlcnZpY2UgbmV0d29yayByZXN0YXJ0Cnl1bSBpbnN0YWxsIC15IGZpcmV3YWxsZAoKIyBpcHRhYmxlcyAtdCBtYW5nbGUgLUkgUFJFUk9VVElORyAtaSBldGgwIC1wIHRjcCAtcyAxMC4wLjIuNTAgLWogTUFSSyAtLXNldC1tYXJrIDIKIyBpcHRhYmxlcyAtdCBuYXQgLUEgUE9TVFJPVVRJTkcgISAtcyAxMC4wLjIuNTAgLWogTUFTUVVFUkFERQojIGlwdGFibGVzIC10IG5hdCAtSSBQT1NUUk9VVElORyAtcyAxMC4wLjIuNTAgLWogU05BVCAtLXRvLXNvdXJjZSAxMC4wLjEuMTAgCiMgaXB0YWJsZXMgLXQgbmF0IC1JIFBSRVJPVVRJTkcgLWkgZXRoMSAtaiBETkFUIC0tdG8gMTAuMC4yLjUwCgpmaXJld2FsbC1vZmZsaW5lLWNtZCAtLXpvbmU9ZXh0ZXJuYWwgLS1hZGQtc2VydmljZT1kaGNwdjYtY2xpZW50CmZpcmV3YWxsLW9mZmxpbmUtY21kIC0tem9uZT1wdWJsaWMgLS1hZGQtbWFzcXVlcmFkZQpmaXJld2FsbC1vZmZsaW5lLWNtZCAtLXpvbmU9cHVibGljIC0tYWRkLWZvcndhcmQtcG9ydD1wb3J0PTIyMjI6cHJvdG89dGNwOnRvYWRkcj0xMC4wLjIuMjA6dG9wb3J0PTIyCmZpcmV3YWxsLW9mZmxpbmUtY21kIC0tZGlyZWN0IC0tYWRkLXJ1bGUgaXB2NCBuYXQgUFJFUk9VVElORyAwIC1pIGV0aDEgLWogRE5BVCAtLXRvLWRlc3RpbmF0aW9uIDEwLjAuMi41MApmaXJld2FsbC1vZmZsaW5lLWNtZCAtLWRpcmVjdCAtLWFkZC1ydWxlIGlwdjQgbmF0IFBPU1RST1VUSU5HIDAgLXMgMTAuMC4yLjUwIC1qIFNOQVQgLS10by1zb3VyY2UgMTAuMC4xLjEwCmZpcmV3YWxsLW9mZmxpbmUtY21kIC0tZGlyZWN0IC0tYWRkLXJ1bGUgaXB2NCBtYW5nbGUgUFJFUk9VVElORyAwIC1pIGV0aDAgLXMgMTAuMC4yLjUwIC1qIE1BUksgLS1zZXQtbWFyayAyCmZpcmV3YWxsLW9mZmxpbmUtY21kIC0tZGlyZWN0IC0tYWRkLXJ1bGUgaXB2NCBmaWx0ZXIgRk9SV0FSRCAwIC1pIGV0aDEgLW8gZXRoMCAtaiBBQ0NFUFQKZmlyZXdhbGwtb2ZmbGluZS1jbWQgLS1kaXJlY3QgLS1hZGQtcnVsZSBpcHY0IGZpbHRlciBGT1JXQVJEIDAgLWkgZXRoMCAtbyBldGgxIC1qIEFDQ0VQVApzeXN0ZW1jdGwgcmVzdGFydCBmaXJld2FsbGQuc2VydmljZQpzeXN0ZW1jdGwgcmVzdGFydCBuZXR3b3JrLnNlcnZpY2UKCmlwIHJ1bGUgYWRkIGZ3bWFyayAyIHRhYmxlIDMKaXAgcm91dGUgYWRkIGRlZmF1bHQgdmlhIDEwLjAuMS4xIGRldiBldGgxIHRhYmxlIDMKaXAgcm91dGUgZmx1c2ggY2FjaGUKc2VkIC1pICckaWlwIHJ1bGUgYWRkIGZ3bWFyayAyIHRhYmxlIDNcbmlwIHJvdXRlIGFkZCBkZWZhdWx0IHZpYSAxMC4wLjEuMSBkZXYgZXRoMSB0YWJsZSAzXG5pcCByb3V0ZSBmbHVzaCBjYWNoZScgL2V0Yy9yYy5kL3JjLmxvY2FsCmNobW9kICt4IC9ldGMvcmMuZC9yYy5sb2NhbApzZWQgLWkgJ3MvUGFzc3dvcmRBdXRoZW50aWNhdGlvbiBuby9QYXNzd29yZEF1dGhlbnRpY2F0aW9uIHllcy8nIC9ldGMvc3NoL3NzaGRfY29uZmlnCnNlZCAtaSAncy9yb290OlteOl0qL3Jvb3Q6JDEkWGxReUFsbnYkbVlhSjNIN0hsNXpqeFY5ZW5wWDJNMS8nIC9ldGMvc2hhZG93CnNlZCAtaSAncy9jZW50b3M6W146XSovY2VudG9zOiQxJFhsUXlBbG52JG1ZYUozSDdIbDV6anhWOWVucFgyTTEvJyAvZXRjL3NoYWRvdwpybSAtcmYgL2hvbWUvY2VudG9zLy5zc2gKcm0gLXJmIC9yb290Ly5zc2gKcm0gLXJmIC9ldGMvaG9zdG5hbWUKZWNobyBmaXJld2FsbCA+PiAvZXRjL2hvc3RuYW1lCnJlYm9vdA==",
        NetworkInterfaces=[
            NetworkInterfaceProperty(
                DeviceIndex='0',
                NetworkInterfaceId=Ref(firewalldPrivateSideInterface)),
            NetworkInterfaceProperty(
                DeviceIndex='1',
                NetworkInterfaceId=Ref(firewalldPublicWebInterface)),
            NetworkInterfaceProperty(
                DeviceIndex='2',
                NetworkInterfaceId=Ref(firewalldPublicNATInterface))],
        Tags=Tags(
            Name=Join(" ", ["Team", team_number, "Firewalld Instance"]),
            Team=team_number)
    ))

privateSubnetDefaultRoute = t.add_resource(
    Route(
        'PrivateSubnetDefaultRoute',
        NetworkInterfaceId=Ref(firewalldPrivateSideInterface),
        DestinationCidrBlock='0.0.0.0/0',
        RouteTableId=Ref(privateRouteTable),
    ))

oldJoomlaInstance = t.add_resource(
    Instance(
        'oldJoomla',
        AvailabilityZone=az,
        ImageId=FindInMap(
            'RegionToInstanceToAMI',
            Ref('AWS::Region'),
            'oldJoomla'),
        InstanceType="m3.medium",
        KeyName="Default key 3-16-16",
        UserData="IyEvYmluL2Jhc2gKc2V0IC14CmV4ZWMgPiA+KHRlZSAvdmFyL2xvZy91c2VyLWRhdGEubG9nICkgMj4mMQoKZXhwb3J0IERFQklBTl9GUk9OVEVORD0ibm9uaW50ZXJhY3RpdmUiCgp1bnRpbCAkKGN1cmwgLS1vdXRwdXQgL2Rldi9udWxsIC0tc2lsZW50IC0taGVhZCAtLWZhaWwgaHR0cDovL2ljYW5oYXppcC5jb20pOyBkbwogICAgc2xlZXAgNQpkb25lCgphcHQtZ2V0IHVwZGF0ZQphcHQtZ2V0IC15cSBpbnN0YWxsIGxhbXAtc2VydmVyXgphcHQtZ2V0IC15cSBpbnN0YWxsIHBocDUtbXlzcWwgcGhwNS1jdXJsCmFwdC1nZXQgLXlxIGluc3RhbGwgdGVsbmV0ZAp3Z2V0ICdodHRwczovL2NjZGMtaW4tdGhlLWNsb3VkLXN0dWZmcy5zMy5hbWF6b25hd3MuY29tL2pvb20udGFyLmd6P0FXU0FjY2Vzc0tleUlkPUFLSUFKSEtJVEFGSERDVVFOSUpRJkV4cGlyZXM9MTUxMzQ4MjM5MSZTaWduYXR1cmU9YzY3NW11bkhadElkbzRRUkdtc0ltaHdnTWZFJTNEJyAtTyAvdG1wL2pvb20udGFyLmd6CndnZXQgJ2h0dHBzOi8vY2NkYy1pbi10aGUtY2xvdWQtc3R1ZmZzLnMzLmFtYXpvbmF3cy5jb20vZGF0YWJhc2UuZG1wP0FXU0FjY2Vzc0tleUlkPUFLSUFKSEtJVEFGSERDVVFOSUpRJkV4cGlyZXM9MTUxMzQ4MjkzOCZTaWduYXR1cmU9NmVlVVNMeSUyRjVkNm9EQVIlMkJTemV4b2VBaTE2USUzRCcgLU8gL3RtcC9kYXRhYmFzZS5kbXAKd2dldCAnaHR0cHM6Ly9jY2RjLWluLXRoZS1jbG91ZC1zdHVmZnMuczMuYW1hem9uYXdzLmNvbS9jb25maWd1cmF0aW9uLnBocD9BV1NBY2Nlc3NLZXlJZD1BS0lBSkhLSVRBRkhEQ1VRTklKUSZFeHBpcmVzPTE1MTM0ODI3NDgmU2lnbmF0dXJlPXRsTE1aUlk5ZktqczE1dWxXcDglMkZuTU5INURNJTNEJyAtTyAvdmFyL3d3dy9jb25maWd1cmF0aW9uLnBocAp0YXIgeHpmIC90bXAvam9vbS50YXIuZ3ogLUMgL3Zhci93d3cKc3luYwpybSAtcmYgL3Zhci93d3cvaW5zdGFsbGF0aW9uCnN5bmMKY2hvd24gd3d3LWRhdGE6d3d3LWRhdGEgLVIgL3Zhci93d3cvKgpzeW5jCm15c3FsIDwgL3RtcC9kYXRhYmFzZS5kbXAKcm0gLWYgL3Zhci93d3cvaW5kZXguaHRtbApybSAtZiAvdG1wL2RhdGFiYXNlLmRtcApybSAtZiAvdG1wL2pvb20udGFyLmd6CgpzZWQgLUUgLWkgJ3MvYmluZC1hZGRyZXNzKFxzKik9KFxzKTEyN1wuMFwuMFwuMS9iaW5kLWFkZHJlc3NcMT1cMjBcLjBcLjBcLjAvJyAvZXRjL215c3FsL215LmNuZgpzZXJ2aWNlIG15c3FsIHJlc3RhcnQKCmFwdC1nZXQgLXlxIGluc3RhbGwgdnNmdHBkCnNlcnZpY2UgdnNmdHBkIHN0b3AKCm1rZGlyIC92YXIvZnRwCgpjaG93biAtaFIgZnRwOmZ0cCAvdmFyL2Z0cApjaG1vZCA1NTUgL3Zhci9mdHAKc3luYwoKbXYgL2V0Yy92c2Z0cGQuY29uZiAvZXRjL3ZzZnRwX2NvbmZfb3JpZ2luYWwKc3luYwoKY2F0IDw8IEVPRiA+IC9ldGMvdnNmdHBkLmNvbmYKIyBBbm9ueW1vdXMgRlRQIEFjY2VzcwpsaXN0ZW49WUVTCmFub255bW91c19lbmFibGU9WUVTCm5vX2Fub25fcGFzc3dvcmQ9WUVTCmFub25fcm9vdD0vdmFyL2Z0cApFT0YKCnRvdWNoIC92YXIvZnRwL1NDT1JFLnR4dApzZXJ2aWNlIHZzZnRwZCByZXN0YXJ0CgpzZWQgLWkgJ3MvUGFzc3dvcmRBdXRoZW50aWNhdGlvbiBuby9QYXNzd29yZEF1dGhlbnRpY2F0aW9uIHllcy8nIC9ldGMvc3NoL3NzaGRfY29uZmlnCnNlZCAtaSAncy9yb290OlteOl0qL3Jvb3Q6JDEkWGxReUFsbnYkbVlhSjNIN0hsNXpqeFY5ZW5wWDJNMS8nIC9ldGMvc2hhZG93CnNlZCAtaSAncy91YnVudHU6W146XSovdWJ1bnR1OiQxJDZPQnhIa3lTJEhubUtuNVYwUmNicVhVb3dGQW1HdDAvJyAvZXRjL3NoYWRvdwpzZXJ2aWNlIHNzaCByZXN0YXJ0CgpybSAtcmYgL2hvbWUvdWJ1bnR1Ly5zc2gKcm0gLXJmIC9yb290Ly5zc2gKcm0gLXJmIC9yb290Ly5iYXNoX2hpc3Rvcnk=",
        NetworkInterfaces=[
            NetworkInterfaceProperty(
                GroupSet=[
                    Ref(globalAllowSecurityGroup)],
                AssociatePublicIpAddress='false',
                DeviceIndex='0',
                DeleteOnTermination='true',
                SubnetId=Ref(Private_Server_Subnet),
                PrivateIpAddress="10.0.2.50")],
        DependsOn='PrivateSubnetDefaultRoute',
        Tags=Tags(
            Name=Join(" ", ["Team", team_number, "Old Joomla Instance"]),
            Team=team_number)
    ))

domainController = t.add_resource(
    Instance(
        'domainController',
        AvailabilityZone=az,
        ImageId=FindInMap(
            'RegionToInstanceToAMI',
            Ref('AWS::Region'),
            'domainctl'),
        InstanceType="t2.large",
        KeyName="Windows Passwords",
        UserData="PHBvd2Vyc2hlbGw+CmRvIHsKICBzbGVlcCAzICAgICAgCn0gdW50aWwoVGVzdC1OZXRDb25uZWN0aW9uIDguOC44LjggfCA/IHsgJF8uUGluZ1N1Y2NlZWRlZCB9ICkKJGJvb3RzdHJhcDJ1cmwgPSAiaHR0cHM6Ly9jY2RjLWluLXRoZS1jbG91ZC1zdHVmZnMuczMuYW1hem9uYXdzLmNvbS9ib290c3RyYXAyLnBzMT9BV1NBY2Nlc3NLZXlJZD1BS0lBSkhLSVRBRkhEQ1VRTklKUSZFeHBpcmVzPTE1MTM1NzgzOTEmU2lnbmF0dXJlPVp3ZXkyN21Dbm1tdjN4dkhvaUwzUHdTNVpxayUzRCIKJG91dHB1dCA9ICJDOlxXaW5kb3dzXFRlbXBcYm9vdHN0cmFwMi5wczEiCihOZXctT2JqZWN0IFN5c3RlbS5OZXQuV2ViQ2xpZW50KS5Eb3dubG9hZEZpbGUoJGJvb3RzdHJhcDJ1cmwsICRvdXRwdXQpCgokdXNlcnN1cmwgPSAiaHR0cHM6Ly9jY2RjLWluLXRoZS1jbG91ZC1zdHVmZnMuczMuYW1hem9uYXdzLmNvbS91c2Vycy5jc3Y/QVdTQWNjZXNzS2V5SWQ9QUtJQUpIS0lUQUZIRENVUU5JSlEmRXhwaXJlcz0xNTEzNTc0MDEzJlNpZ25hdHVyZT04UmJhcXhaMVNueEZaYUZiSDhLYVU1VlFLQXclM0QiCiRvdXRwdXQgPSAiQzpcVXNlcnNcdXNlcnMuY3N2IgooTmV3LU9iamVjdCBTeXN0ZW0uTmV0LldlYkNsaWVudCkuRG93bmxvYWRGaWxlKCR1c2Vyc3VybCwgJG91dHB1dCkKCiRhY3Rpb24gPSBOZXctU2NoZWR1bGVkVGFza0FjdGlvbiAtRXhlY3V0ZSAncG93ZXJzaGVsbC5leGUnIC1Bcmd1bWVudCAnQzpcV2luZG93c1xUZW1wXGJvb3RzdHJhcDIucHMxJwokdHJpZ2dlciA9IE5ldy1TY2hlZHVsZWRUYXNrVHJpZ2dlciAtQXRTdGFydHVwCiR0YXNrbmFtZSA9ICJCb290c3RyYXAyIgokc2V0dGluZ3MgPSBOZXctU2NoZWR1bGVkVGFza1NldHRpbmdzU2V0IC1FeGVjdXRpb25UaW1lTGltaXQgKE5ldy1UaW1lU3BhbiAtTWludXRlcyAyMCkgLVJlc3RhcnRDb3VudCAzIC1SZXN0YXJ0SW50ZXJ2YWwgKE5ldy1UaW1lU3BhbiAtTWludXRlcyAxKQpSZWdpc3Rlci1TY2hlZHVsZWRUYXNrIC1BY3Rpb24gJGFjdGlvbiAtVHJpZ2dlciAkdHJpZ2dlciAtVGFza05hbWUgJHRhc2tuYW1lIC1TZXR0aW5ncyAkc2V0dGluZ3MgLVVzZXIgIlN5c3RlbSIgLVJ1bkxldmVsIEhpZ2hlc3QKCkluc3RhbGwtd2luZG93c2ZlYXR1cmUgLW5hbWUgQUQtRG9tYWluLVNlcnZpY2VzIC1JbmNsdWRlTWFuYWdlbWVudFRvb2xzCgojIENyZWF0ZSBOZXcgRm9yZXN0LCBhZGQgRG9tYWluIENvbnRyb2xsZXIKJFBsYWluUGFzc3dvcmQgPSAibXlzdXBlcnNlY3VyZXBhc3N3b3JkMSEiCiRTZWN1cmVQYXNzd29yZCA9ICRQbGFpblBhc3N3b3JkIHwgQ29udmVydFRvLVNlY3VyZVN0cmluZyAtQXNQbGFpblRleHQgLUZvcmNlCiRkb21haW5uYW1lID0gImljYW5oYXoubG9jYWwiCiRuZXRiaW9zTmFtZSA9ICJJQ0FOSEFaIgoKSW1wb3J0LU1vZHVsZSBBRERTRGVwbG95bWVudApJbnN0YWxsLUFERFNGb3Jlc3QgLUNyZWF0ZURuc0RlbGVnYXRpb246JGZhbHNlIGAKIC1EYXRhYmFzZVBhdGggIkM6XFdpbmRvd3NcTlREUyIgYAogLURvbWFpbk1vZGUgIldpbjIwMTIiIGAKIC1Eb21haW5OYW1lICRkb21haW5uYW1lIGAKIC1Eb21haW5OZXRiaW9zTmFtZSAkbmV0Ymlvc05hbWUgYAogLUZvcmVzdE1vZGUgIldpbjIwMTIiIGAKIC1JbnN0YWxsRG5zOiR0cnVlIGAKIC1Mb2dQYXRoICJDOlxXaW5kb3dzXE5URFMiIGAKIC1Ob1JlYm9vdE9uQ29tcGxldGlvbjokZmFsc2UgYAogLVN5c3ZvbFBhdGggIkM6XFdpbmRvd3NcU1lTVk9MIiBgCiAtU2FmZU1vZGVBZG1pbmlzdHJhdG9yUGFzc3dvcmQgJFNlY3VyZVBhc3N3b3JkIGAKIC1Gb3JjZTokdHJ1ZSAKPC9wb3dlcnNoZWxsPg==",
        NetworkInterfaces=[
            NetworkInterfaceProperty(
                GroupSet=[
                    Ref(globalAllowSecurityGroup)],
                AssociatePublicIpAddress='false',
                DeviceIndex='0',
                DeleteOnTermination='true',
                SubnetId=Ref(Private_Server_Subnet),
                PrivateIpAddress="10.0.2.15")],
        DependsOn='PrivateSubnetDefaultRoute',
        Tags=Tags(
            Name=Join(" ", ["Team", team_number, "Domain Controller"]),
            Team=team_number)
    ))

storage = t.add_resource(
    Instance(
        'storage',
        AvailabilityZone=az,
        ImageId=FindInMap(
            'RegionToInstanceToAMI',
            Ref('AWS::Region'),
            'storage'),
        InstanceType="t2.large",
        KeyName="Windows Passwords",
        UserData="PHBvd2Vyc2hlbGw+ClN0YXJ0LVNsZWVwIC1zIDkwMAoKJGJvb3RzdHJhcDIgPSBAJwpkbyB7CiAgc2xlZXAgMyAgICAgIAp9IHVudGlsKFRlc3QtTmV0Q29ubmVjdGlvbiA4LjguOC44IHwgPyB7ICRfLlBpbmdTdWNjZWVkZWQgfSApCgpJbnN0YWxsLVdpbmRvd3NGZWF0dXJlIC1OYW1lIHdlYi1mdHAtc2VydmVyLCB3ZWItZnRwLXNlcnZpY2UKCiAjIyAgICBORUVERUQgRk9SIElJUyBDTURMRVRTCkltcG9ydC1Nb2R1bGUgV2ViQWRtaW5pc3RyYXRpb24KCiMjICAgIENSRUFURSBGVFAgU0lURSBBTkQgU0VUIEM6XGluZXRwdWJcZnRwcm9vdCBBUyBIT01FIERJUkVDVE9SWQpOZXctV2ViRnRwU2l0ZSAtTmFtZSAiaWNhbmhhemZpbGV6IiAtUG9ydCAiMjEiIC1Gb3JjZQpjbWQgL2MgXFdpbmRvd3NcU3lzdGVtMzJcaW5ldHNydlxhcHBjbWQgc2V0IFNJVEUgImljYW5oYXpmaWxleiIgIi12aXJ0dWFsRGlyZWN0b3J5RGVmYXVsdHMucGh5c2ljYWxQYXRoOkM6XGluZXRwdWJcZnRwcm9vdCIKCiMjICAgIFNFVCBQRVJNSVNTSU9OUwoKICAgICAjIyBBbGxvdyBTU0wgY29ubmVjdGlvbnMgClNldC1JdGVtUHJvcGVydHkgIklJUzpcU2l0ZXNcaWNhbmhhemZpbGV6IiAtTmFtZSBmdHBTZXJ2ZXIuc2VjdXJpdHkuc3NsLmNvbnRyb2xDaGFubmVsUG9saWN5IC1WYWx1ZSAwClNldC1JdGVtUHJvcGVydHkgIklJUzpcU2l0ZXNcaWNhbmhhemZpbGV6IiAtTmFtZSBmdHBTZXJ2ZXIuc2VjdXJpdHkuc3NsLmRhdGFDaGFubmVsUG9saWN5IC1WYWx1ZSAwCgogICAgICMjIEVuYWJsZSBCYXNpYyBBdXRoZW50aWNhdGlvbgpTZXQtSXRlbVByb3BlcnR5ICJJSVM6XFNpdGVzXGljYW5oYXpmaWxleiIgLU5hbWUgZnRwU2VydmVyLnNlY3VyaXR5LmF1dGhlbnRpY2F0aW9uLmJhc2ljQXV0aGVudGljYXRpb24uZW5hYmxlZCAtVmFsdWUgJHRydWUKIyMgU2V0IFVTZXIgSXNvbGF0aW9uCiBTZXQtSXRlbVByb3BlcnR5ICJJSVM6XFNpdGVzXGljYW5oYXpmaWxleiIgLU5hbWUgZnRwc2VydmVyLnVzZXJpc29sYXRpb24ubW9kZSAtVmFsdWUgMwoKI1NldC1JdGVtUHJvcGVydHkgIklJUzpcU2l0ZXNcaWNhbmhhemZpbGV6IiAtTmFtZSBmdHBTZXJ2ZXIuc2VjdXJpdHkudXNlcklzb2xhdGlvbi4gLVZhbHVlICR0cnVlCgogICAgICMjIEdpdmUgQXV0aG9yaXphdGlvbiB0byBBbGwgVXNlcnMgYW5kIGdyYW50ICJyZWFkIi8id3JpdGUiIHByaXZpbGVnZXMKQWRkLVdlYkNvbmZpZ3VyYXRpb24gIi9zeXN0ZW0uZnRwU2VydmVyL3NlY3VyaXR5L2F1dGhvcml6YXRpb24iIC12YWx1ZSBAe2FjY2Vzc1R5cGU9IkFsbG93Ijtyb2xlcz0iIjtwZXJtaXNzaW9ucz0iUmVhZCxXcml0ZSI7dXNlcnM9IioifSAtUFNQYXRoIElJUzpcIC1sb2NhdGlvbiAiaWNhbmhhemZpbGV6IgojIyBHaXZlIEF1dGhvcml6YXRpb24gdG8gQWxsIFVzZXJzIHVzaW5nIENNRAojYXBwY21kIHNldCBjb25maWcgJWZ0cHNpdGUlIC9zZWN0aW9uOnN5c3RlbS5mdHBzZXJ2ZXIvc2VjdXJpdHkvYXV0aG9yaXphdGlvbiAvK1thY2Nlc3NUeXBlPSdBbGxvdycscGVybWlzc2lvbnM9J1JlYWQsV3JpdGUnLHJvbGVzPScnLHVzZXJzPScqJ10gL2NvbW1pdDphcHBob3N0IAoKICAgICAjIyBSZXN0YXJ0IHRoZSBGVFAgc2l0ZSBmb3IgYWxsIGNoYW5nZXMgdG8gdGFrZSBlZmZlY3QKUmVzdGFydC1XZWJJdGVtICJJSVM6XFNpdGVzXGljYW5oYXpmaWxleiIKClVucmVnaXN0ZXItU2NoZWR1bGVkVGFzayAtVGFza05hbWUgQm9vdHN0cmFwMiAtQ29uZmlybTokZmFsc2UKUmVtb3ZlLUl0ZW0gLVBhdGggQzpcV2luZG93c1xUZW1wXGJvb3RzdHJhcDIucHMxCmNtZC5leGUgL2MgJ2RlbCBDOlxXaW5kb3dzXFRlbXBcYm9vdHN0cmFwMi5wczEnClJlc3RhcnQtQ29tcHV0ZXIgLUZvcmNlCgonQAoKJGJvb3RzdHJhcDIgfCBPdXQtRmlsZSBDOlxXaW5kb3dzXFRlbXBcYm9vdHN0cmFwMi5wczEKJGFjdGlvbiA9IE5ldy1TY2hlZHVsZWRUYXNrQWN0aW9uIC1FeGVjdXRlICdwb3dlcnNoZWxsLmV4ZScgLUFyZ3VtZW50ICdDOlxXaW5kb3dzXFRlbXBcYm9vdHN0cmFwMi5wczEnCiR0cmlnZ2VyID0gTmV3LVNjaGVkdWxlZFRhc2tUcmlnZ2VyIC1BdFN0YXJ0dXAKJHRhc2tuYW1lID0gIkJvb3RzdHJhcDIiCiRzZXR0aW5ncyA9IE5ldy1TY2hlZHVsZWRUYXNrU2V0dGluZ3NTZXQgLUV4ZWN1dGlvblRpbWVMaW1pdCAoTmV3LVRpbWVTcGFuIC1NaW51dGVzIDIwKSAtUmVzdGFydENvdW50IDMgLVJlc3RhcnRJbnRlcnZhbCAoTmV3LVRpbWVTcGFuIC1NaW51dGVzIDEpClJlZ2lzdGVyLVNjaGVkdWxlZFRhc2sgLUFjdGlvbiAkYWN0aW9uIC1UcmlnZ2VyICR0cmlnZ2VyIC1UYXNrTmFtZSAkdGFza25hbWUgLVNldHRpbmdzICRzZXR0aW5ncyAtVXNlciAiU3lzdGVtIiAtUnVuTGV2ZWwgSGlnaGVzdAoKCmRvIHsKICBzbGVlcCAzICAgICAgCn0gdW50aWwoVGVzdC1OZXRDb25uZWN0aW9uIDguOC44LjggfCA/IHsgJF8uUGluZ1N1Y2NlZWRlZCB9ICkKCiRuZXdjb21wdXRlcm5hbWUgPSAic3RvcmFnZSIKU2V0LUROU0NsaWVudFNlcnZlckFkZHJlc3Mg4oCTSW50ZXJmYWNlQWxpYXMgIkV0aGVybmV0IDIiIOKAk1NlcnZlckFkZHJlc3NlcyAoIjEwLjAuMi4xNSIsIjEwLjAuMi4xIikKJGRvbWFpbiA9ICJpY2FuaGF6LmxvY2FsIgokcGFzc3dvcmQgPSAibXlzdXBlcnNlY3VyZXBhc3N3b3JkMSEiIHwgQ29udmVydFRvLVNlY3VyZVN0cmluZyAtYXNQbGFpblRleHQgLUZvcmNlCiR1c2VybmFtZSA9ICIkZG9tYWluXEFkbWluaXN0cmF0b3IiIAokY3JlZGVudGlhbCA9IE5ldy1PYmplY3QgU3lzdGVtLk1hbmFnZW1lbnQuQXV0b21hdGlvbi5QU0NyZWRlbnRpYWwoJHVzZXJuYW1lLCRwYXNzd29yZCkKQWRkLUNvbXB1dGVyIC1Eb21haW5OYW1lICRkb21haW4gLUNyZWRlbnRpYWwgJGNyZWRlbnRpYWwKUmVuYW1lLUNvbXB1dGVyIC1OZXdOYW1lICRuZXdjb21wdXRlcm5hbWUgLURvbWFpbkNyZWRlbnRpYWwgJGNyZWRlbnRpYWwgLUZvcmNlCmNtZC5leGUgL2MgJ25ldCB1c2VyIGFkbWluaXN0cmF0b3IgIm15c3VwZXJzZWN1cmVwYXNzd29yZDEhIicKClJlc3RhcnQtQ29tcHV0ZXIKPC9wb3dlcnNoZWxsPgo=",
        NetworkInterfaces=[
            NetworkInterfaceProperty(
                GroupSet=[
                    Ref(globalAllowSecurityGroup)],
                AssociatePublicIpAddress='false',
                DeviceIndex='0',
                DeleteOnTermination='true',
                SubnetId=Ref(Private_Server_Subnet),
                PrivateIpAddress="10.0.2.45")],
        DependsOn='PrivateSubnetDefaultRoute',
        Tags=Tags(
            Name=Join(" ", ["Team", team_number, "New Storage Box"]),
            Team=team_number)
    ))

servercore = t.add_resource(
    Instance(
        'servercore',
        AvailabilityZone=az,
        ImageId=FindInMap(
            'RegionToInstanceToAMI',
            Ref('AWS::Region'),
            'servercore'),
        InstanceType="t2.large",
        KeyName="Windows Passwords",
        UserData="PHBvd2Vyc2hlbGw+ClN0YXJ0LVNsZWVwIC1zIDkwMAoKJG5ld2NvbXB1dGVybmFtZSA9ICJzZXJ2ZXJjb3JlIgpTZXQtRE5TQ2xpZW50U2VydmVyQWRkcmVzcyDigJNJbnRlcmZhY2VBbGlhcyAiRXRoZXJuZXQgMiIg4oCTU2VydmVyQWRkcmVzc2VzICgiMTAuMC4yLjE1IiwiMTAuMC4yLjEiKQokZG9tYWluID0gImljYW5oYXoubG9jYWwiCiRwYXNzd29yZCA9ICJteXN1cGVyc2VjdXJlcGFzc3dvcmQxISIgfCBDb252ZXJ0VG8tU2VjdXJlU3RyaW5nIC1hc1BsYWluVGV4dCAtRm9yY2UKJHVzZXJuYW1lID0gIiRkb21haW5cQWRtaW5pc3RyYXRvciIgCiRjcmVkZW50aWFsID0gTmV3LU9iamVjdCBTeXN0ZW0uTWFuYWdlbWVudC5BdXRvbWF0aW9uLlBTQ3JlZGVudGlhbCgkdXNlcm5hbWUsJHBhc3N3b3JkKQpBZGQtQ29tcHV0ZXIgLURvbWFpbk5hbWUgJGRvbWFpbiAtQ3JlZGVudGlhbCAkY3JlZGVudGlhbApSZW5hbWUtQ29tcHV0ZXIgLU5ld05hbWUgJG5ld2NvbXB1dGVybmFtZSAtRG9tYWluQ3JlZGVudGlhbCAkY3JlZGVudGlhbCAtRm9yY2UKY21kLmV4ZSAvYyAnbmV0IHVzZXIgYWRtaW5pc3RyYXRvciAibXlzdXBlcnNlY3VyZXBhc3N3b3JkMSEiJwoKUmVzdGFydC1Db21wdXRlcgo8L3Bvd2Vyc2hlbGw+",
        NetworkInterfaces=[
            NetworkInterfaceProperty(
                GroupSet=[
                    Ref(globalAllowSecurityGroup)],
                AssociatePublicIpAddress='false',
                DeviceIndex='0',
                DeleteOnTermination='true',
                SubnetId=Ref(Private_Server_Subnet),
                PrivateIpAddress="10.0.2.100")],
        DependsOn='PrivateSubnetDefaultRoute',
        Tags=Tags(
            Name=Join(" ", ["Team", team_number, "New Server Core (WebServer)"]),
            Team=team_number)
    ))

freebsd = t.add_resource(
    Instance(
        'freebsd',
        AvailabilityZone=az,
        ImageId=FindInMap(
            'RegionToInstanceToAMI',
            Ref('AWS::Region'),
            'freebsd'),
        InstanceType="t2.medium",
        KeyName="Default key 3-16-16",
        UserData="IyEvYmluL3NoCnB3IGdyb3VwYWRkIHNjb3JlCmVjaG8gInNjb3JpbmdwYXNzd29yZCIgfCBwdyB1c2VyYWRkIC1uIHNjb3JlIC1zIC9iaW4vY3NoIC1tIC1nIHNjb3JlIC1kIC9ob21lL3Njb3JlIC1oIDAKCnNlZCAtaSAnJyAncy8jUGFzc3dvcmRBdXRoZW50aWNhdGlvbiBuby9QYXNzd29yZEF1dGhlbnRpY2F0aW9uIHllcy8nIC9ldGMvc3NoL3NzaGRfY29uZmlnCnNlZCAtaSAnJyAncy8jUGVybWl0Um9vdExvZ2luIG5vL1Blcm1pdFJvb3RMb2dpbiB5ZXMvJyAvZXRjL3NzaC9zc2hkX2NvbmZpZwoKc2VydmljZSBzc2hkIHJlc3RhcnQKCnNlZCAtaSAnJyAncy9zY29yZTpbXjpdKi9zY29yZTokMSR6Y0tKWjkwMiRqQnI3MUlkZU5Mdzg2WW1UWGdQa3IxLycgL2V0Yy9tYXN0ZXIucGFzc3dkCnNlZCAtaSAnJyAncy9yb290Ojovcm9vdDokMSRYbFF5QWxudiRtWWFKM0g3SGw1emp4VjllbnBYMk0xLycgL2V0Yy9tYXN0ZXIucGFzc3dkCnNlZCAtaSAnJyAncy9lYzItdXNlcjpbXjpdKjovZWMyLXVzZXI6JDEkNk9CeEhreVMkSG5tS241VjBSY2JxWFVvd0ZBbUd0MC8nIC9ldGMvbWFzdGVyLnBhc3N3ZAojcm0gLXJmIC9ob21lL2VjMi11c2VyLy5zc2g=",
        NetworkInterfaces=[
            NetworkInterfaceProperty(
                GroupSet=[
                    Ref(globalAllowSecurityGroup)],
                AssociatePublicIpAddress='false',
                DeviceIndex='0',
                DeleteOnTermination='true',
                SubnetId=Ref(Private_Server_Subnet),
                PrivateIpAddress="10.0.2.20")],
        DependsOn='PrivateSubnetDefaultRoute',
        Tags=Tags(
            Name=Join(" ", ["Team", team_number, "freebsd"]),
            Team=team_number)
    ))

workstation1 = t.add_resource(
    Instance(
        'workstation1',
        AvailabilityZone=az,
        ImageId=FindInMap(
            'RegionToInstanceToAMI',
            Ref('AWS::Region'),
            '2008workstation'),
        InstanceType="t2.large",
        KeyName="Windows Passwords",
        UserData="PHBvd2Vyc2hlbGw+ClN0YXJ0LVNsZWVwIC1zIDkwMAoKZG8gewogIHNsZWVwIDMgICAgICAKfSB1bnRpbChUZXN0LU5ldENvbm5lY3Rpb24gOC44LjguOCB8ID8geyAkXy5QaW5nU3VjY2VlZGVkIH0gKQoKJE5JQ3MgPSBHZXQtV01JT2JqZWN0IFdpbjMyX05ldHdvcmtBZGFwdGVyQ29uZmlndXJhdGlvbiB8IHdoZXJleyRfLklQRW5hYmxlZCAtZXEgIlRSVUUifQogIEZvcmVhY2goJE5JQyBpbiAkTklDcykgewoKJEROU1NlcnZlcnMgPSAiMTAuMC4yLjE1IiwiMTAuMC4zLjEiCiAkTklDLlNldEROU1NlcnZlclNlYXJjaE9yZGVyKCRETlNTZXJ2ZXJzKQogJE5JQy5TZXREeW5hbWljRE5TUmVnaXN0cmF0aW9uKCJUUlVFIikKfQokZG9tYWluID0gImljYW5oYXoubG9jYWwiCiRwYXNzd29yZCA9ICJteXN1cGVyc2VjdXJlcGFzc3dvcmQxISIgfCBDb252ZXJ0VG8tU2VjdXJlU3RyaW5nIC1hc1BsYWluVGV4dCAtRm9yY2UKJHVzZXJuYW1lID0gIiRkb21haW5cQWRtaW5pc3RyYXRvciIgCiRjcmVkZW50aWFsID0gTmV3LU9iamVjdCBTeXN0ZW0uTWFuYWdlbWVudC5BdXRvbWF0aW9uLlBTQ3JlZGVudGlhbCgkdXNlcm5hbWUsJHBhc3N3b3JkKQpBZGQtQ29tcHV0ZXIgLURvbWFpbk5hbWUgJGRvbWFpbiAtQ3JlZGVudGlhbCAkY3JlZGVudGlhbApjbWQuZXhlIC9jICduZXQgdXNlciBhZG1pbmlzdHJhdG9yICJteXN1cGVyc2VjdXJlcGFzc3dvcmQxISInCgpSZXN0YXJ0LUNvbXB1dGVyCjwvcG93ZXJzaGVsbD4=",
        NetworkInterfaces=[
            NetworkInterfaceProperty(
                GroupSet=[
                    Ref(globalAllowSecurityGroup)],
                AssociatePublicIpAddress='true',
                DeviceIndex='0',
                DeleteOnTermination='true',
                SubnetId=Ref(Workstation_Subnet),
                PrivateIpAddress="10.0.3.200")],
        DependsOn='PrivateSubnetDefaultRoute',
        Tags=Tags(
            Name=Join(" ", ["Team", team_number, "Workstation 1"]),
            Team=team_number)
    ))

workstation2 = t.add_resource(
    Instance(
        'workstation2',
        AvailabilityZone=az,
        ImageId=FindInMap(
            'RegionToInstanceToAMI',
            Ref('AWS::Region'),
            '2008workstation'),
        InstanceType="t2.large",
        KeyName="Windows Passwords",
        UserData="PHBvd2Vyc2hlbGw+ClN0YXJ0LVNsZWVwIC1zIDkwMAoKZG8gewogIHNsZWVwIDMgICAgICAKfSB1bnRpbChUZXN0LU5ldENvbm5lY3Rpb24gOC44LjguOCB8ID8geyAkXy5QaW5nU3VjY2VlZGVkIH0gKQoKJE5JQ3MgPSBHZXQtV01JT2JqZWN0IFdpbjMyX05ldHdvcmtBZGFwdGVyQ29uZmlndXJhdGlvbiB8IHdoZXJleyRfLklQRW5hYmxlZCAtZXEgIlRSVUUifQogIEZvcmVhY2goJE5JQyBpbiAkTklDcykgewoKJEROU1NlcnZlcnMgPSAiMTAuMC4yLjE1IiwiMTAuMC4zLjEiCiAkTklDLlNldEROU1NlcnZlclNlYXJjaE9yZGVyKCRETlNTZXJ2ZXJzKQogJE5JQy5TZXREeW5hbWljRE5TUmVnaXN0cmF0aW9uKCJUUlVFIikKfQokZG9tYWluID0gImljYW5oYXoubG9jYWwiCiRwYXNzd29yZCA9ICJteXN1cGVyc2VjdXJlcGFzc3dvcmQxISIgfCBDb252ZXJ0VG8tU2VjdXJlU3RyaW5nIC1hc1BsYWluVGV4dCAtRm9yY2UKJHVzZXJuYW1lID0gIiRkb21haW5cQWRtaW5pc3RyYXRvciIgCiRjcmVkZW50aWFsID0gTmV3LU9iamVjdCBTeXN0ZW0uTWFuYWdlbWVudC5BdXRvbWF0aW9uLlBTQ3JlZGVudGlhbCgkdXNlcm5hbWUsJHBhc3N3b3JkKQpBZGQtQ29tcHV0ZXIgLURvbWFpbk5hbWUgJGRvbWFpbiAtQ3JlZGVudGlhbCAkY3JlZGVudGlhbApjbWQuZXhlIC9jICduZXQgdXNlciBhZG1pbmlzdHJhdG9yICJteXN1cGVyc2VjdXJlcGFzc3dvcmQxISInCgpSZXN0YXJ0LUNvbXB1dGVyCjwvcG93ZXJzaGVsbD4=",
        NetworkInterfaces=[
            NetworkInterfaceProperty(
                GroupSet=[
                    Ref(globalAllowSecurityGroup)],
                AssociatePublicIpAddress='true',
                DeviceIndex='0',
                DeleteOnTermination='true',
                SubnetId=Ref(Workstation_Subnet),
                PrivateIpAddress="10.0.3.205")],
        DependsOn='PrivateSubnetDefaultRoute',
        Tags=Tags(
            Name=Join(" ", ["Team", team_number, "Workstation 2"]),
            Team=team_number)
    ))

workstation3 = t.add_resource(
    Instance(
        'workstation3',
        AvailabilityZone=az,
        ImageId=FindInMap(
            'RegionToInstanceToAMI',
            Ref('AWS::Region'),
            'debworkstation'),
        InstanceType="t2.medium",
        KeyName="Default key 3-16-16",
        UserData="IyEvYmluL2Jhc2gKc2V0IC14CmV4ZWMgPiA+KHRlZSAvdmFyL2xvZy91c2VyLWRhdGEubG9nICkgMj4mMQoKdW50aWwgJChjdXJsIC0tb3V0cHV0IC9kZXYvbnVsbCAtLXNpbGVudCAtLWhlYWQgLS1mYWlsIGh0dHA6Ly9pY2FuaGF6aXAuY29tKTsgZG8KICAgIHNsZWVwIDUKZG9uZQoKZWNobyB3b3Jrc3RhdGlvbjMgPiAvZXRjL2hvc3RuYW1lCgpzZWQgLWkgJ3MvUGFzc3dvcmRBdXRoZW50aWNhdGlvbiBuby9QYXNzd29yZEF1dGhlbnRpY2F0aW9uIHllcy8nIC9ldGMvc3NoL3NzaGRfY29uZmlnCnNlZCAtaSAncy9QZXJtaXRSb290TG9naW4gd2l0aG91dC1wYXNzd29yZC9QZXJtaXRSb290TG9naW4geWVzLycgL2V0Yy9zc2gvc3NoZF9jb25maWcKc2VkIC1pICdzL3Jvb3Q6W146XSovcm9vdDokMSRYbFF5QWxudiRtWWFKM0g3SGw1emp4VjllbnBYMk0xLycgL2V0Yy9zaGFkb3cKc2VkIC1pICdzL2FkbWluOlteOl0qL2FkbWluOiQxJDZPQnhIa3lTJEhubUtuNVYwUmNicVhVb3dGQW1HdDAvJyAvZXRjL3NoYWRvdwpzZXJ2aWNlIHNzaCByZXN0YXJ0CgpybSAtcmYgL2hvbWUvYWRtaW4vLnNzaApybSAtcmYgL3Jvb3QvLnNzaApybSAtcmYgL3Jvb3QvLmJhc2hfaGlzdG9yeQoKcmVib290",
        NetworkInterfaces=[
            NetworkInterfaceProperty(
                GroupSet=[
                    Ref(globalAllowSecurityGroup)],
                AssociatePublicIpAddress='true',
                DeviceIndex='0',
                DeleteOnTermination='true',
                SubnetId=Ref(Workstation_Subnet),
                PrivateIpAddress="10.0.3.210")],
        DependsOn='PrivateSubnetDefaultRoute',
        Tags=Tags(
            Name=Join(" ", ["Team", team_number, "workstation 3"]),
            Team=team_number)
    ))

workstation4 = t.add_resource(
    Instance(
        'workstation4',
        AvailabilityZone=az,
        ImageId=FindInMap(
            'RegionToInstanceToAMI',
            Ref('AWS::Region'),
            'debworkstation'),
        InstanceType="t2.medium",
        KeyName="Default key 3-16-16",
        UserData="IyEvYmluL2Jhc2gKc2V0IC14CmV4ZWMgPiA+KHRlZSAvdmFyL2xvZy91c2VyLWRhdGEubG9nICkgMj4mMQoKdW50aWwgJChjdXJsIC0tb3V0cHV0IC9kZXYvbnVsbCAtLXNpbGVudCAtLWhlYWQgLS1mYWlsIGh0dHA6Ly9pY2FuaGF6aXAuY29tKTsgZG8KICAgIHNsZWVwIDUKZG9uZQoKZWNobyB3b3Jrc3RhdGlvbjQgPiAvZXRjL2hvc3RuYW1lCgpzZWQgLWkgJ3MvUGFzc3dvcmRBdXRoZW50aWNhdGlvbiBuby9QYXNzd29yZEF1dGhlbnRpY2F0aW9uIHllcy8nIC9ldGMvc3NoL3NzaGRfY29uZmlnCnNlZCAtaSAncy9QZXJtaXRSb290TG9naW4gd2l0aG91dC1wYXNzd29yZC9QZXJtaXRSb290TG9naW4geWVzLycgL2V0Yy9zc2gvc3NoZF9jb25maWcKc2VkIC1pICdzL3Jvb3Q6W146XSovcm9vdDokMSRYbFF5QWxudiRtWWFKM0g3SGw1emp4VjllbnBYMk0xLycgL2V0Yy9zaGFkb3cKc2VkIC1pICdzL2FkbWluOlteOl0qL2FkbWluOiQxJDZPQnhIa3lTJEhubUtuNVYwUmNicVhVb3dGQW1HdDAvJyAvZXRjL3NoYWRvdwpzZXJ2aWNlIHNzaCByZXN0YXJ0CgpybSAtcmYgL2hvbWUvYWRtaW4vLnNzaApybSAtcmYgL3Jvb3QvLnNzaApybSAtcmYgL3Jvb3QvLmJhc2hfaGlzdG9yeQoKcmVib290",
        NetworkInterfaces=[
            NetworkInterfaceProperty(
                GroupSet=[
                    Ref(globalAllowSecurityGroup)],
                AssociatePublicIpAddress='true',
                DeviceIndex='0',
                DeleteOnTermination='true',
                SubnetId=Ref(Workstation_Subnet),
                PrivateIpAddress="10.0.3.215")],
        DependsOn='PrivateSubnetDefaultRoute',
        Tags=Tags(
            Name=Join(" ", ["Team", team_number, "workstation 4"]),
            Team=team_number)
    ))


firewalldPublicNatEIPOutput = t.add_output(
    [Output('firewalldPublicNatEIPOutput',
            Description='Firewall NAT IP',
            Value=Ref(firewalldPublicNATEIP))])

firewalldPublicWebEIPOutput = t.add_output(
    [Output('firewalldPublicWebEIPOutput',
            Description='Firewall Web IP',
            Value=Ref(firewalldPublicWebEIP))])

for x in range(1, 5):

    t.add_output(
        [Output('workstation%dPublicIPOutput' % x,
                Description='Workstation %d Public IP' % x,
                Value=GetAtt('workstation%d' % x, 'PublicIp'))])


print(t.to_json())

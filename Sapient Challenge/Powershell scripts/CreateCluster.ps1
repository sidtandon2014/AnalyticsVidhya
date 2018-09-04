#Connect-AzureRmAccount -Subscription "Microsoft Azure Internal Consumption"

# Prompt for generic information
$resourceGroupName = "rgkafka" #Read-Host "What is the resource group name?"
$baseName = "sidkafkacluster" #Read-Host "What is the base name? It is used to create names for resources, such as 'net-basename' and 'kafka-basename':" 
$location = "East US 2" #Read-Host "What Azure Region do you want to create the resources in?"
$rootCert = "F:\Sid\Learnings\Data Scientist\Analytics Vidhya\Sapient Challenge\ConnectToKafkaCert.cer"    #Read-Host "What is the file path to the root certificate? It is used to secure the VPN gateway."

# Prompt for HDInsight credentials
$adminCreds = Get-Credential -Message "Enter the HTTPS user name and password for the HDInsight cluster" -UserName "admin"
$sshCreds = Get-Credential -Message "Enter the SSH user name and password for the HDInsight cluster" -UserName "sshuser"

# Names for Azure resources
$networkName = "net-$baseName"
$clusterName = "kafka-$baseName"
$sparkClusterName = "sidsparkcluster"
$storageName = "store$baseName" # Can't use dashes in storage names
$defaultContainerName = $clusterName
$defaultSubnetName = "default"
$gatewaySubnetName = "GatewaySubnet"
$gatewayPublicIpName = "GatewayIp"
$gatewayIpConfigName = "GatewayConfig"
$vpnRootCertName = "rootcert"
$vpnName = "VPNGateway"

# Network settings
$networkAddressPrefix = "10.0.0.0/16"
$defaultSubnetPrefix = "10.0.0.0/24"
$gatewaySubnetPrefix = "10.0.1.0/24"
$vpnClientAddressPool = "172.16.201.0/24"

# HDInsight settings for kafka
$HdiWorkerNodes = 3
$hdiVersion = "3.6"
$hdiType = "Kafka"

# HDInsight settings for spark
$HdiWorkerNodesSpark = 1
$hdiVersionSpark = "3.6"
$SparkVersion = "2.3"
$hdiTypeSpark = "Spark"
$defaultContainerNameSpark = "spark$clusterName"

#---------------------create resource group and virtual network

# Create the resource group that contains everything
New-AzureRmResourceGroup -Name $resourceGroupName -Location $location

# Create the subnet configuration
$defaultSubnetConfig = New-AzureRmVirtualNetworkSubnetConfig -Name $defaultSubnetName `
    -AddressPrefix $defaultSubnetPrefix
$gatewaySubnetConfig = New-AzureRmVirtualNetworkSubnetConfig -Name $gatewaySubnetName `
    -AddressPrefix $gatewaySubnetPrefix

# Create the subnet
New-AzureRmVirtualNetwork -Name $networkName `
    -ResourceGroupName $resourceGroupName `
    -Location $location `
    -AddressPrefix $networkAddressPrefix `
    -Subnet $defaultSubnetConfig, $gatewaySubnetConfig

# Get the network & subnet that were created
$network = Get-AzureRmVirtualNetwork -Name $networkName `
    -ResourceGroupName $resourceGroupName
$gatewaySubnet = Get-AzureRmVirtualNetworkSubnetConfig -Name $gatewaySubnetName `
    -VirtualNetwork $network
$defaultSubnet = Get-AzureRmVirtualNetworkSubnetConfig -Name $defaultSubnetName `
    -VirtualNetwork $network

# Set a dynamic public IP address for the gateway subnet
$gatewayPublicIp = New-AzureRmPublicIpAddress -Name $gatewayPublicIpName `
    -ResourceGroupName $resourceGroupName `
    -Location $location `
    -AllocationMethod Dynamic
$gatewayIpConfig = New-AzureRmVirtualNetworkGatewayIpConfig -Name $gatewayIpConfigName `
    -Subnet $gatewaySubnet `
    -PublicIpAddress $gatewayPublicIp

# Get the certificate info
# Get the full path in case a relative path was passed
$rootCertFile = Get-ChildItem $rootCert
$cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($rootCertFile)
$certBase64 = [System.Convert]::ToBase64String($cert.RawData)
$p2sRootCert = New-AzureRmVpnClientRootCertificate -Name $vpnRootCertName `
    -PublicCertData $certBase64

# Create the VPN gateway
New-AzureRmVirtualNetworkGateway -Name $vpnName `
    -ResourceGroupName $resourceGroupName `
    -Location $location `
    -IpConfigurations $gatewayIpConfig `
    -GatewayType Vpn `
    -VpnType RouteBased `
    -EnableBgp $false `
    -GatewaySku Standard `
    -VpnClientAddressPool $vpnClientAddressPool `
    -VpnClientRootCertificates $p2sRootCert

#----------------------------Create storage account and virtual network

# Create the storage account
New-AzureRmStorageAccount `
    -ResourceGroupName $resourceGroupName `
    -Name $storageName `
    -Type Standard_GRS `
    -Location $location

# Get the storage account keys and create a context
$defaultStorageKey = (Get-AzureRmStorageAccountKey -ResourceGroupName $resourceGroupName `
    -Name $storageName)[0].Value
$storageContext = New-AzureStorageContext -StorageAccountName $storageName `
    -StorageAccountKey $defaultStorageKey

# Create the default storage container
New-AzureStorageContainer -Name $defaultContainerName `
    -Context $storageContext

#--------------------------Create HDInsight cluster

# Create the HDInsight cluster
New-AzureRmHDInsightCluster `
    -ResourceGroupName $resourceGroupName `
    -ClusterName $clusterName `
    -Location $location `
    -ClusterSizeInNodes $hdiWorkerNodes `
    -ClusterType $hdiType `
    -OSType Linux `
    -Version $hdiVersion `
    -HttpCredential $adminCreds `
    -SshCredential $sshCreds `
    -DefaultStorageAccountName "$storageName.blob.core.windows.net" `
    -DefaultStorageAccountKey $defaultStorageKey `
    -DefaultStorageContainer $defaultContainerName `
    -DisksPerWorkerNode 2 `
    -VirtualNetworkId $network.Id `
    -SubnetName $defaultSubnet.Id

#--------------------------Create Spark cluster


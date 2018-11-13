<powershell>
Start-Sleep -s 900

$newcomputername = "servercore"
Set-DNSClientServerAddress –InterfaceAlias "Ethernet 2" –ServerAddresses ("10.0.2.15","10.0.2.1")
$domain = "icanhaz.local"
$password = "mysupersecurepassword1!" | ConvertTo-SecureString -asPlainText -Force
$username = "$domain\Administrator" 
$credential = New-Object System.Management.Automation.PSCredential($username,$password)
Add-Computer -DomainName $domain -Credential $credential
Rename-Computer -NewName $newcomputername -DomainCredential $credential -Force
cmd.exe /c 'net user administrator "mysupersecurepassword1!"'

Restart-Computer
</powershell>
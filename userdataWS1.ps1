<powershell>
Start-Sleep -s 900

do {
  sleep 3      
} until(Test-NetConnection 8.8.8.8 | ? { $_.PingSucceeded } )

$NICs = Get-WMIObject Win32_NetworkAdapterConfiguration | where{$_.IPEnabled -eq "TRUE"}
  Foreach($NIC in $NICs) {

$DNSServers = "10.0.2.15","10.0.3.1"
 $NIC.SetDNSServerSearchOrder($DNSServers)
 $NIC.SetDynamicDNSRegistration("TRUE")
}
$domain = "icanhaz.local"
$password = "mysupersecurepassword1!" | ConvertTo-SecureString -asPlainText -Force
$username = "$domain\Administrator" 
$credential = New-Object System.Management.Automation.PSCredential($username,$password)
Add-Computer -DomainName $domain -Credential $credential
cmd.exe /c 'net user administrator "mysupersecurepassword1!"'

Restart-Computer
</powershell>
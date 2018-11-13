<powershell>
Start-Sleep -s 900

$bootstrap2 = @'
do {
  sleep 3      
} until(Test-NetConnection 8.8.8.8 | ? { $_.PingSucceeded } )

Install-WindowsFeature -Name web-ftp-server, web-ftp-service

 ##    NEEDED FOR IIS CMDLETS
Import-Module WebAdministration

##    CREATE FTP SITE AND SET C:\inetpub\ftproot AS HOME DIRECTORY
New-WebFtpSite -Name "icanhazfilez" -Port "21" -Force
cmd /c \Windows\System32\inetsrv\appcmd set SITE "icanhazfilez" "-virtualDirectoryDefaults.physicalPath:C:\inetpub\ftproot"

##    SET PERMISSIONS

     ## Allow SSL connections 
Set-ItemProperty "IIS:\Sites\icanhazfilez" -Name ftpServer.security.ssl.controlChannelPolicy -Value 0
Set-ItemProperty "IIS:\Sites\icanhazfilez" -Name ftpServer.security.ssl.dataChannelPolicy -Value 0

     ## Enable Basic Authentication
Set-ItemProperty "IIS:\Sites\icanhazfilez" -Name ftpServer.security.authentication.basicAuthentication.enabled -Value $true
## Set USer Isolation
 Set-ItemProperty "IIS:\Sites\icanhazfilez" -Name ftpserver.userisolation.mode -Value 3

#Set-ItemProperty "IIS:\Sites\icanhazfilez" -Name ftpServer.security.userIsolation. -Value $true

     ## Give Authorization to All Users and grant "read"/"write" privileges
Add-WebConfiguration "/system.ftpServer/security/authorization" -value @{accessType="Allow";roles="";permissions="Read,Write";users="*"} -PSPath IIS:\ -location "icanhazfilez"
## Give Authorization to All Users using CMD
#appcmd set config %ftpsite% /section:system.ftpserver/security/authorization /+[accessType='Allow',permissions='Read,Write',roles='',users='*'] /commit:apphost 

     ## Restart the FTP site for all changes to take effect
Restart-WebItem "IIS:\Sites\icanhazfilez"

Unregister-ScheduledTask -TaskName Bootstrap2 -Confirm:$false
Remove-Item -Path C:\Windows\Temp\bootstrap2.ps1
cmd.exe /c 'del C:\Windows\Temp\bootstrap2.ps1'
Restart-Computer -Force

'@

$bootstrap2 | Out-File C:\Windows\Temp\bootstrap2.ps1
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument 'C:\Windows\Temp\bootstrap2.ps1'
$trigger = New-ScheduledTaskTrigger -AtStartup
$taskname = "Bootstrap2"
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 20) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName $taskname -Settings $settings -User "System" -RunLevel Highest


do {
  sleep 3      
} until(Test-NetConnection 8.8.8.8 | ? { $_.PingSucceeded } )

$newcomputername = "storage"
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

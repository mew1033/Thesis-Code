<powershell>
do {
  sleep 3
} until(Test-NetConnection 8.8.8.8 | ? { $_.PingSucceeded } )
$bootstrap2url = "https://ccdc-in-the-cloud-stuffs.s3.amazonaws.com/bootstrap2.ps1"
$output = "C:\Windows\Temp\bootstrap2.ps1"
(New-Object System.Net.WebClient).DownloadFile($bootstrap2url, $output)

$usersurl = "https://ccdc-in-the-cloud-stuffs.s3.amazonaws.com/users.csv"
$output = "C:\Users\users.csv"
(New-Object System.Net.WebClient).DownloadFile($usersurl, $output)

$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument 'C:\Windows\Temp\bootstrap2.ps1'
$trigger = New-ScheduledTaskTrigger -AtStartup
$taskname = "Bootstrap2"
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 20) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName $taskname -Settings $settings -User "System" -RunLevel Highest

Install-windowsfeature -name AD-Domain-Services -IncludeManagementTools

# Create New Forest, add Domain Controller
$PlainPassword = "mysupersecurepassword1!"
$SecurePassword = $PlainPassword | ConvertTo-SecureString -AsPlainText -Force
$domainname = "icanhaz.local"
$netbiosName = "ICANHAZ"

Import-Module ADDSDeployment
Install-ADDSForest -CreateDnsDelegation:$false `
 -DatabasePath "C:\Windows\NTDS" `
 -DomainMode "Win2012" `
 -DomainName $domainname `
 -DomainNetbiosName $netbiosName `
 -ForestMode "Win2012" `
 -InstallDns:$true `
 -LogPath "C:\Windows\NTDS" `
 -NoRebootOnCompletion:$false `
 -SysvolPath "C:\Windows\SYSVOL" `
 -SafeModeAdministratorPassword $SecurePassword `
 -Force:$true
</powershell>

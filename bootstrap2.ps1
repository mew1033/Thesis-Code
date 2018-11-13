Start-Transcript -path C:\Windows\Temp\bootstrap2.log -append

function Import-LabADUser
{
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true,
                   Position=0,
                   ValueFromPipeline=$true,
                   ValueFromPipelineByPropertyName=$true,
                   HelpMessage="Path to one or more locations.")]
        [Alias("PSPath")]
        [ValidateNotNullOrEmpty()]
        [string[]]
        $Path,

        [Parameter(Mandatory=$true,
                   position=1,
                   ValueFromPipeline=$true,
                   ValueFromPipelineByPropertyName=$true,
                   HelpMessage="Organizational Unit to save users.")]
        [String]
        [Alias('OU')]
        $OrganizationalUnit
    )
    
    begin {
        if (-not (Get-Module -Name 'ActiveDirectory')) {
            Write-Error -Message 'ActiveDirectory module is not present'
            return
        }
    }
    
    process {
        Import-Module ActiveDirectory
        $DomDN = (Get-ADDomain).DistinguishedName
        $forest = (Get-ADDomain).Forest
        $ou = Get-ADOrganizationalUnit -Filter "name -eq '$($OrganizationalUnit)'"
        if($ou -eq $null) {
            New-ADOrganizationalUnit -Name "$($OrganizationalUnit)" -Path $DomDN
            $ou = Get-ADOrganizationalUnit -Filter "name -eq '$($OrganizationalUnit)'"
        }
        $data = 

        Import-Csv -Path $Path | select  @{Name="Name";Expression={$_.Surname + ", " + $_.GivenName}},
                @{Name="SamAccountName"; Expression={$_.Username}},
                @{Name="UserPrincipalName"; Expression={$_.Username +"@" + $forest}},
                @{Name="GivenName"; Expression={$_.GivenName}},
                @{Name="Surname"; Expression={$_.Surname}},
                @{Name="DisplayName"; Expression={$_.Surname + ", " + $_.GivenName}},
                @{Name="City"; Expression={$_.City}},
                @{Name="StreetAddress"; Expression={$_.StreetAddress}},
                @{Name="State"; Expression={$_.State}},
                @{Name="Country"; Expression={$_.Country}},
                @{Name="PostalCode"; Expression={$_.ZipCode}},
                @{Name="EmailAddress"; Expression={$_.Username +"@" + $forest}},
                @{Name="AccountPassword"; Expression={ (Convertto-SecureString -Force -AsPlainText $_.password)}},
                @{Name="OfficePhone"; Expression={$_.TelephoneNumber}},
                @{Name="Title"; Expression={$_.Occupation}},
                @{Name="Enabled"; Expression={$true}},
                @{Name="PasswordNeverExpires"; Expression={$true}} | ForEach-Object -Process {
             
                    $subou = Get-ADOrganizationalUnit -Filter "name -eq ""$($_.Country)""" -SearchBase $ou.DistinguishedName        
                    if($subou -eq $null) {
                        New-ADOrganizationalUnit -Name $_.Country -Path $ou.DistinguishedName
                        $subou = Get-ADOrganizationalUnit -Filter "name -eq ""$($_.Country)""" -SearchBase $ou.DistinguishedName        
                    }
                    $_ | Select @{Name="Path"; Expression={$subou.DistinguishedName}},* | New-ADUser  
                }
    }    
    end {}
}

Start-Sleep -s 120
do {
  sleep 3      
} until(Test-NetConnection 8.8.8.8 | ? { $_.PingSucceeded } )

cmd.exe /c 'net user administrator "mysupersecurepassword1!"'
Import-LabADUser -Path C:\Users\users.csv -OrganizationalUnit WorldwideUsers
Unregister-ScheduledTask -TaskName Bootstrap2 -Confirm:$false
Remove-Item -Path C:\Windows\Temp\bootstrap2.ps1
cmd.exe /c 'del C:\Windows\Temp\bootstrap2.ps1'
Rename-Computer -NewName im-the-boss -Force
Stop-Transcript
Restart-Computer -Force
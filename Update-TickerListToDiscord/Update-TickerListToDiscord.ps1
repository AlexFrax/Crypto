###
### Variables. May be changed.
###

# Create a webhook integration in Discord and put the link below.
$DiscordWebhook = ''

# Get URLs from edgesforledges.com or sandwich.finance and put them below. If you need more than what is provided here, copy a row and edit accordingly.
# Download the list initially. The script does not do this for you, they have to exist already in the same folder as the script.
$Inputs = @(
	[PSCustomObject]@{URL = "https://sandwichfinance.blob.core.windows.net/files/ftx_perpetual_futures.txt"; List = "$(Join-Path $PSScriptRoot ftx_perpetual_futures.txt)"}
    [PSCustomObject]@{URL = "https://sandwichfinance.blob.core.windows.net/files/ftx_spot_markets.txt"; List = "$(Join-Path $PSScriptRoot ftx_spot_markets.txt)"}
    [PSCustomObject]@{URL = "https://sandwichfinance.blob.core.windows.net/files/kucoin_usdt_markets.txt"; List = "$(Join-Path $PSScriptRoot kucoin_usdt_markets.txt)"}
	[PSCustomObject]@{URL = "https://sandwichfinance.blob.core.windows.net/files/binance_usdt_markets.txt"; List = "$(Join-Path $PSScriptRoot binance_usdt_markets.txt.txt)"}
)

###
### Main script. Do not change!
###

$Windows = $false

If ([System.Environment]::OSVersion.Platform -eq "Win32NT")
{
    $Windows = $True
}

Foreach ($Input in $Inputs)
{
    If ($Windows -eq $true)
    {
        $ListName = $Input.List.split('\\').split('.')[-2]
    }
    else {
        $ListName = $Input.List.split('/').split('.')[-2]
    }
    

    If (-not (Test-Path $Input.List))
    {
        Throw "Can't find $ListName at `"$($Input.List)`". Please download manually initially."
    }

    $OldList = Get-Content $Input.List

    $outfile = new-item -path $PSScriptRoot -name "$(Get-Random).csv" -force
    Invoke-WebRequest -Uri $Input.URL -OutFile $outfile

    $NewList = Get-Content $outfile

    $Compare = Compare-Object $OldList $NewList 

    If ($Compare)
    {
        foreach ($item in $Compare)
        {
            Switch ($item.SideIndicator)
            {
                '=>' {$content = "$ListName`: new ticker found: $($item.InputObject)"}
                '<=' {$content = "$ListName`: ticker in old but not in new list: $($item.InputObject)"}
                default {$content = "$ListName`: cannot handle $($item.InputObject) and $($item.SideIndicator)"}
            }

            $payload = [PSCustomObject]@{content = $content}

            Invoke-RestMethod -Uri $DiscordWebhook -Method Post -Body ($payload | ConvertTo-Json) -ContentType 'Application/Json'

        }
    }
    Else
    {
        $content = "$ListName`: no new tickers today"

        $payload = [PSCustomObject]@{content = $content}

        Invoke-RestMethod -Uri $DiscordWebhook -Method Post -Body ($payload | ConvertTo-Json) -ContentType 'Application/Json'
    }
    Copy-Item $outfile $Input.List -force
    Remove-Item $outfile -force

}




###
### Variables. May be changed.
###

# Create a webhook integration in Discord and put the link below.
$DiscordWebhook = ''

# Get URLs from edgesforledges.com or sandwich.finance and put them below. If you need more than what is provided here, copy a row and edit accordingly.
# Download the list initially. The script does not do this for you, they have to exist already in the same folder as the script.
$Inputs = @(
    [PSCustomObject]@{URL = "http://edgesforledges.com/watchlists/download/binance/fiat/usdt/all";  List = "$(Join-Path $PSScriptRoot binance-fiat-usdt.txt)"}
    [PSCustomObject]@{URL = "https://sandwichfinance.blob.core.windows.net/files/binancefuturesf_usdt_perpetual_futures.txt";  List = "$(Join-Path $PSScriptRoot binance-futures-usd-m.txt)"}
    [PSCustomObject]@{URL = "http://edgesforledges.com/watchlists/download/binance/fiat/eur/all";  List = "$(Join-Path $PSScriptRoot binance-fiat-eur.txt)"}
)

###
### Main script. Do not change!
###

Foreach ($Input in $Inputs)
{
    $ListName = $Input.List.split('\\').split('.')[-2]

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




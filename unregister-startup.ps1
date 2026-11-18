Stop-ScheduledTask -TaskName 'GitHubTrendingPersonalAgent' -ErrorAction SilentlyContinue
Unregister-ScheduledTask -TaskName 'GitHubTrendingPersonalAgent' -Confirm:$false -ErrorAction SilentlyContinue

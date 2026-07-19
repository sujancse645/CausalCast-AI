param(
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$args
)
python scripts/release_audit.py $args

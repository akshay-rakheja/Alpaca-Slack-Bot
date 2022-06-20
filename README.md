# Alpaca for Slack

## TODO:

 - Get orders command

## Working Commands:

### any of the following commands can use /alpaca-paper instead for paper account

`/alpaca-live `

Gives list of commands and helpful info 

`/alpaca-live connect`

Generates link to initiate OAuth process

`/alpaca-live disconnect`

Disconnects user and prompts to reconnect

`/alpaca-live (side) (qty) (symbol) `

 - Side: buy, sell
 - QTY: just notational for now, ie 1, 2, 3 ...
 - Symbol: upper or lower case both work - ie ETHUSD

 - example: /alpaca-live buy 1 ethusd

`/alpaca-live positions`

 Returns the following properties:
    - symbol, qty, unrealized p/l


`/alpaca-live account`

Returns the following account properties:
- Account number, equity, long market value, short market value, change today, buying power

`/alpaca-live status`

Returns whether the account is connected

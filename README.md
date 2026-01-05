# Simsar MCP

Give your AI the eyes of a trader.

MCP server that provides cryptocurrency market data and technical indicators to AI assistants like Claude.

## Installation

### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "simsar": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/miratcan/simsar-mcp", "simsar-mcp"]
    }
  }
}
```

### Claude Code

```bash
claude mcp add simsar -- uvx --from git+https://github.com/miratcan/simsar-mcp simsar-mcp
```

## Website

https://simsar.trade

## Features

- **48 tools** for market analysis
- Real-time price and candle data
- 35+ technical indicators (RSI, MACD, Bollinger Bands, etc.)
- Market sentiment (Fear & Greed, funding rates)
- Futures data (open interest, long/short ratios)
- News (crypto, forex, general)
- Economic calendar (FOMC, CPI, NFP)

## Example Prompts

- "What's the RSI for Bitcoin on 4h timeframe?"
- "Show me ETH funding rate"
- "When is the next FOMC meeting?"
- "Get latest crypto news"
- "What are top traders doing on BTC?"
- "Is the market fearful or greedy right now?"

## Tools

### Price & Candles
- `get_price` - Current price
- `get_candles` - OHLCV candlestick data

### Technical Indicators
- Moving Averages: `get_sma`, `get_ema`, `get_wma`, `get_dema`, `get_tema`, `get_kama`, `get_t3`, `get_trima`
- Momentum: `get_rsi`, `get_macd`, `get_stochastic`, `get_mom`, `get_roc`, `get_cci`, `get_willr`, `get_ultosc`, `get_trix`, `get_ppo`, `get_apo`, `get_cmo`
- Trend: `get_adx`, `get_dx`, `get_plus_di`, `get_minus_di`, `get_adxr`, `get_aroon`, `get_aroonosc`, `get_sar`
- Volume: `get_obv`, `get_mfi`, `get_ad`, `get_adosc`
- Volatility: `get_atr`, `get_natr`, `get_trange`, `get_bollinger_bands`
- Other: `get_stochrsi`, `get_bop`

### Sentiment
- `get_fear_greed` - Crypto Fear & Greed Index
- `get_funding_rates` - Binance Futures funding rates

### Futures
- `get_open_interest` - Open interest
- `get_long_short_ratio` - Long/short account ratio
- `get_top_trader_ratio` - Top trader positions

### News & Calendar
- `get_news` - Market news
- `get_economic_calendar` - Upcoming FOMC, CPI, NFP
- `get_next_events` - Next economic events

## License

MIT

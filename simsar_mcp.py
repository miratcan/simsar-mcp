"""Simsar MCP Server - Market data tools for AI assistants.

This MCP server provides tools to fetch cryptocurrency market data
and technical indicators from the Simsar API.
"""

import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

# Configuration
API_BASE_URL = os.getenv("SIMSAR_API_URL", "https://mirat.dev/projects/simsar/api")

# Initialize MCP server
mcp = FastMCP(
    "Simsar",
    instructions="Market data and technical indicators for cryptocurrency trading analysis. Use these tools to analyze crypto markets.",
)


def _api_get(endpoint: str, params: dict[str, Any] | None = None, max_retries: int = 5) -> dict[str, Any]:
    """Make GET request to Simsar API with retry support.

    Handles 202 Accepted responses by waiting and retrying.
    """
    import time

    url = f"{API_BASE_URL}{endpoint}"
    with httpx.Client(timeout=60.0) as client:
        for attempt in range(max_retries):
            response = client.get(url, params=params)

            if response.status_code == 200:
                return response.json()

            if response.status_code == 202:
                # Server is fetching data, wait and retry
                retry_after = int(response.headers.get("Retry-After", 5))
                time.sleep(retry_after)
                continue

            # 4xx, 5xx - raise error, don't loop
            response.raise_for_status()

        raise Exception(f"Max retries ({max_retries}) exceeded for {endpoint}")


@mcp.tool()
def get_price(symbol: str) -> str:
    """Get the current price of a cryptocurrency.

    Args:
        symbol: Trading pair symbol (e.g., BTCUSDT, ETHUSDT)

    Returns:
        Current price information
    """
    data = _api_get(f"/price/{symbol.upper()}")
    return f"{data['symbol']}: ${data['price']:,.2f} (as of {data['time']})"


def _fmt_vol(v: float) -> str:
    """Format volume compactly."""
    if v >= 1_000_000:
        return f"{v/1_000_000:.1f}M"
    if v >= 1_000:
        return f"{v/1_000:.0f}K"
    return f"{v:.0f}"


@mcp.tool()
def get_candles(
    symbol: str,
    interval: str = "1h",
    limit: int = 20,
    start_time: str | None = None,
    end_time: str | None = None,
) -> str:
    """Get OHLCV candlestick data for a cryptocurrency.

    Args:
        symbol: Trading pair symbol (e.g., BTCUSDT, ETHUSDT)
        interval: Candle interval - 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w
        limit: Number of candles to return (1-100, default 20)
        start_time: Start time in ISO format (e.g., 2024-01-01 or 2024-01-01T00:00:00)
        end_time: End time in ISO format (e.g., 2024-01-15 or 2024-01-15T00:00:00)

    Returns:
        Candlestick data with open, high, low, close, volume
    """
    limit = min(max(1, limit), 100)  # Clamp to reasonable range for display
    params: dict[str, Any] = {"interval": interval, "limit": limit}
    if start_time:
        params["start_time"] = start_time
    if end_time:
        params["end_time"] = end_time
    data = _api_get(f"/candles/{symbol.upper()}", params)

    lines = [f"{data['symbol']} {data['interval']}"]
    for c in data["candles"]:
        t = c["open_time"][5:16]
        lines.append(f"{t}: O:{c['open']:.2f} H:{c['high']:.2f} L:{c['low']:.2f} C:{c['close']:.2f} V:{_fmt_vol(c['volume'])}")

    return "\n".join(lines)


def _format_indicator(data: dict, precision: int = 2) -> str:
    """Format indicator response compactly."""
    params_str = ",".join(f"{v}" for v in data["params"].values()) if data["params"] else ""
    header = f"{data['symbol']} {data['indicator']}({params_str}) {data['interval']}: {data['current']:.{precision}f}" if params_str else f"{data['symbol']} {data['indicator']} {data['interval']}: {data['current']:.{precision}f}"
    lines = [header]
    for v in data["values"]:
        lines.append(f"{v['time'][5:16]}: {v['value']:.{precision}f}")
    return "\n".join(lines)


# === Moving Averages ===


@mcp.tool()
def get_sma(symbol: str, interval: str = "1h", period: int = 20, limit: int = 10) -> str:
    """Simple Moving Average - smooths price data to identify trend direction."""
    data = _api_get(f"/indicators/sma/{symbol.upper()}", {"interval": interval, "period": period, "limit": limit})
    return _format_indicator(data)


@mcp.tool()
def get_ema(symbol: str, interval: str = "1h", period: int = 20, limit: int = 10) -> str:
    """Exponential Moving Average - more weight to recent prices, faster response than SMA."""
    data = _api_get(f"/indicators/ema/{symbol.upper()}", {"interval": interval, "period": period, "limit": limit})
    return _format_indicator(data)


@mcp.tool()
def get_wma(symbol: str, interval: str = "1h", period: int = 20, limit: int = 10) -> str:
    """Weighted Moving Average - linearly weighted, emphasizes recent prices."""
    data = _api_get(f"/indicators/wma/{symbol.upper()}", {"interval": interval, "period": period, "limit": limit})
    return _format_indicator(data)


@mcp.tool()
def get_dema(symbol: str, interval: str = "1h", period: int = 20, limit: int = 10) -> str:
    """Double Exponential Moving Average - reduces lag of traditional EMA."""
    data = _api_get(f"/indicators/dema/{symbol.upper()}", {"interval": interval, "period": period, "limit": limit})
    return _format_indicator(data)


@mcp.tool()
def get_tema(symbol: str, interval: str = "1h", period: int = 20, limit: int = 10) -> str:
    """Triple Exponential Moving Average - even less lag than DEMA."""
    data = _api_get(f"/indicators/tema/{symbol.upper()}", {"interval": interval, "period": period, "limit": limit})
    return _format_indicator(data)


@mcp.tool()
def get_kama(symbol: str, interval: str = "1h", period: int = 30, limit: int = 10) -> str:
    """Kaufman Adaptive Moving Average - adapts to market volatility."""
    data = _api_get(f"/indicators/kama/{symbol.upper()}", {"interval": interval, "period": period, "limit": limit})
    return _format_indicator(data)


@mcp.tool()
def get_t3(symbol: str, interval: str = "1h", period: int = 5, limit: int = 10) -> str:
    """T3 Moving Average - very smooth with minimal lag."""
    data = _api_get(f"/indicators/t3/{symbol.upper()}", {"interval": interval, "period": period, "limit": limit})
    return _format_indicator(data)


@mcp.tool()
def get_trima(symbol: str, interval: str = "1h", period: int = 20, limit: int = 10) -> str:
    """Triangular Moving Average - double-smoothed SMA."""
    data = _api_get(f"/indicators/trima/{symbol.upper()}", {"interval": interval, "period": period, "limit": limit})
    return _format_indicator(data)


# === Momentum Indicators ===


@mcp.tool()
def get_mom(symbol: str, interval: str = "1h", period: int = 10, limit: int = 10) -> str:
    """Momentum - measures price change over period. Positive=uptrend, negative=downtrend."""
    data = _api_get(f"/indicators/mom/{symbol.upper()}", {"interval": interval, "period": period, "limit": limit})
    return _format_indicator(data)


@mcp.tool()
def get_roc(symbol: str, interval: str = "1h", period: int = 10, limit: int = 10) -> str:
    """Rate of Change - percentage price change over period."""
    data = _api_get(f"/indicators/roc/{symbol.upper()}", {"interval": interval, "period": period, "limit": limit})
    return _format_indicator(data, 4)


@mcp.tool()
def get_cmo(symbol: str, interval: str = "1h", period: int = 14, limit: int = 10) -> str:
    """Chande Momentum Oscillator - oscillates between -100 and +100."""
    data = _api_get(f"/indicators/cmo/{symbol.upper()}", {"interval": interval, "period": period, "limit": limit})
    return _format_indicator(data)


@mcp.tool()
def get_cci(symbol: str, interval: str = "1h", period: int = 20, limit: int = 10) -> str:
    """Commodity Channel Index - measures price deviation. >100 overbought, <-100 oversold."""
    data = _api_get(f"/indicators/cci/{symbol.upper()}", {"interval": interval, "period": period, "limit": limit})
    return _format_indicator(data)


@mcp.tool()
def get_willr(symbol: str, interval: str = "1h", period: int = 14, limit: int = 10) -> str:
    """Williams %R - momentum oscillator. >-20 overbought, <-80 oversold."""
    data = _api_get(f"/indicators/willr/{symbol.upper()}", {"interval": interval, "period": period, "limit": limit})
    return _format_indicator(data)


@mcp.tool()
def get_ultosc(symbol: str, interval: str = "1h", period1: int = 7, period2: int = 14, period3: int = 28, limit: int = 10) -> str:
    """Ultimate Oscillator - combines short, medium, long-term momentum."""
    data = _api_get(f"/indicators/ultosc/{symbol.upper()}", {"interval": interval, "period1": period1, "period2": period2, "period3": period3, "limit": limit})
    return _format_indicator(data)


@mcp.tool()
def get_trix(symbol: str, interval: str = "1h", period: int = 30, limit: int = 10) -> str:
    """TRIX - triple-smoothed EMA rate of change. Filters noise, shows momentum."""
    data = _api_get(f"/indicators/trix/{symbol.upper()}", {"interval": interval, "period": period, "limit": limit})
    return _format_indicator(data, 4)


@mcp.tool()
def get_ppo(symbol: str, interval: str = "1h", fast: int = 12, slow: int = 26, limit: int = 10) -> str:
    """Percentage Price Oscillator - similar to MACD but as percentage."""
    data = _api_get(f"/indicators/ppo/{symbol.upper()}", {"interval": interval, "fast": fast, "slow": slow, "limit": limit})
    return _format_indicator(data, 4)


@mcp.tool()
def get_apo(symbol: str, interval: str = "1h", fast: int = 12, slow: int = 26, limit: int = 10) -> str:
    """Absolute Price Oscillator - difference between fast and slow EMA."""
    data = _api_get(f"/indicators/apo/{symbol.upper()}", {"interval": interval, "fast": fast, "slow": slow, "limit": limit})
    return _format_indicator(data)


@mcp.tool()
def get_dx(symbol: str, interval: str = "1h", period: int = 14, limit: int = 10) -> str:
    """Directional Movement Index - measures trend strength."""
    data = _api_get(f"/indicators/dx/{symbol.upper()}", {"interval": interval, "period": period, "limit": limit})
    return _format_indicator(data)


@mcp.tool()
def get_plus_di(symbol: str, interval: str = "1h", period: int = 14, limit: int = 10) -> str:
    """Plus Directional Indicator - measures upward trend strength."""
    data = _api_get(f"/indicators/plus_di/{symbol.upper()}", {"interval": interval, "period": period, "limit": limit})
    return _format_indicator(data)


@mcp.tool()
def get_minus_di(symbol: str, interval: str = "1h", period: int = 14, limit: int = 10) -> str:
    """Minus Directional Indicator - measures downward trend strength."""
    data = _api_get(f"/indicators/minus_di/{symbol.upper()}", {"interval": interval, "period": period, "limit": limit})
    return _format_indicator(data)


@mcp.tool()
def get_adxr(symbol: str, interval: str = "1h", period: int = 14, limit: int = 10) -> str:
    """Average Directional Movement Index Rating - smoothed ADX."""
    data = _api_get(f"/indicators/adxr/{symbol.upper()}", {"interval": interval, "period": period, "limit": limit})
    return _format_indicator(data)


# === Volume Indicators ===


@mcp.tool()
def get_obv(symbol: str, interval: str = "1h", limit: int = 10) -> str:
    """On Balance Volume - cumulative volume, confirms price trends."""
    data = _api_get(f"/indicators/obv/{symbol.upper()}", {"interval": interval, "limit": limit})
    return _format_indicator(data, 0)


@mcp.tool()
def get_mfi(symbol: str, interval: str = "1h", period: int = 14, limit: int = 10) -> str:
    """Money Flow Index - volume-weighted RSI. >80 overbought, <20 oversold."""
    data = _api_get(f"/indicators/mfi/{symbol.upper()}", {"interval": interval, "period": period, "limit": limit})
    return _format_indicator(data)


@mcp.tool()
def get_ad(symbol: str, interval: str = "1h", limit: int = 10) -> str:
    """Accumulation/Distribution Line - measures money flow into/out of asset."""
    data = _api_get(f"/indicators/ad/{symbol.upper()}", {"interval": interval, "limit": limit})
    return _format_indicator(data, 0)


@mcp.tool()
def get_adosc(symbol: str, interval: str = "1h", fast: int = 3, slow: int = 10, limit: int = 10) -> str:
    """Chaikin A/D Oscillator - momentum of A/D line."""
    data = _api_get(f"/indicators/adosc/{symbol.upper()}", {"interval": interval, "fast": fast, "slow": slow, "limit": limit})
    return _format_indicator(data, 0)


# === Volatility Indicators ===


@mcp.tool()
def get_natr(symbol: str, interval: str = "1h", period: int = 14, limit: int = 10) -> str:
    """Normalized Average True Range - ATR as percentage of close price."""
    data = _api_get(f"/indicators/natr/{symbol.upper()}", {"interval": interval, "period": period, "limit": limit})
    return _format_indicator(data, 4)


@mcp.tool()
def get_trange(symbol: str, interval: str = "1h", limit: int = 10) -> str:
    """True Range - max of (high-low, |high-prevclose|, |low-prevclose|)."""
    data = _api_get(f"/indicators/trange/{symbol.upper()}", {"interval": interval, "limit": limit})
    return _format_indicator(data)


# === Other Indicators ===


@mcp.tool()
def get_sar(symbol: str, interval: str = "1h", acceleration: float = 0.02, maximum: float = 0.2, limit: int = 10) -> str:
    """Parabolic SAR - trailing stop and trend indicator. Price above SAR=bullish."""
    data = _api_get(f"/indicators/sar/{symbol.upper()}", {"interval": interval, "acceleration": acceleration, "maximum": maximum, "limit": limit})
    return _format_indicator(data)


@mcp.tool()
def get_bop(symbol: str, interval: str = "1h", limit: int = 10) -> str:
    """Balance of Power - measures buying vs selling pressure. Range -1 to +1."""
    data = _api_get(f"/indicators/bop/{symbol.upper()}", {"interval": interval, "limit": limit})
    return _format_indicator(data, 4)


@mcp.tool()
def get_aroon(symbol: str, interval: str = "1h", period: int = 14, limit: int = 10) -> str:
    """Aroon - identifies trend and trend strength. AroonUp>AroonDown=bullish."""
    data = _api_get(f"/indicators/aroon/{symbol.upper()}", {"interval": interval, "period": period, "limit": limit})
    current = data["current"]
    lines = [f"{data['symbol']} AROON({period}) {data['interval']}: Up={current['aroon_up']:.1f} Down={current['aroon_down']:.1f}"]
    for v in data["values"]:
        lines.append(f"{v['time'][5:16]}: Up={v['aroon_up']:.1f} Down={v['aroon_down']:.1f}")
    return "\n".join(lines)


@mcp.tool()
def get_aroonosc(symbol: str, interval: str = "1h", period: int = 14, limit: int = 10) -> str:
    """Aroon Oscillator - difference between AroonUp and AroonDown. >0 bullish."""
    data = _api_get(f"/indicators/aroonosc/{symbol.upper()}", {"interval": interval, "period": period, "limit": limit})
    return _format_indicator(data)


@mcp.tool()
def get_stochrsi(symbol: str, interval: str = "1h", period: int = 14, fastk: int = 5, fastd: int = 3, limit: int = 10) -> str:
    """Stochastic RSI - applies stochastic to RSI. More sensitive than RSI."""
    data = _api_get(f"/indicators/stochrsi/{symbol.upper()}", {"interval": interval, "period": period, "fastk": fastk, "fastd": fastd, "limit": limit})
    current = data["current"]
    lines = [f"{data['symbol']} STOCHRSI({period},{fastk},{fastd}) {data['interval']}: K={current['fastk']:.1f} D={current['fastd']:.1f}"]
    for v in data["values"]:
        lines.append(f"{v['time'][5:16]}: K={v['fastk']:.1f} D={v['fastd']:.1f}")
    return "\n".join(lines)


@mcp.tool()
def get_rsi(
    symbol: str,
    interval: str = "1h",
    period: int = 14,
    limit: int = 10,
    start_time: str | None = None,
    end_time: str | None = None,
) -> str:
    """Get RSI (Relative Strength Index) for a cryptocurrency.

    RSI measures momentum on a scale of 0-100:
    - Below 30: Oversold (potential buy signal)
    - Above 70: Overbought (potential sell signal)

    Args:
        symbol: Trading pair symbol (e.g., BTCUSDT, ETHUSDT)
        interval: Candle interval - 1m, 5m, 15m, 30m, 1h, 4h, 1d
        period: RSI calculation period (default 14)
        limit: Number of values to return (default 10)
        start_time: Start time in ISO format (e.g., 2024-01-01)
        end_time: End time in ISO format (e.g., 2024-02-01)

    Returns:
        RSI values with interpretation
    """
    params: dict[str, Any] = {"interval": interval, "period": period, "limit": limit}
    if start_time:
        params["start_time"] = start_time
    if end_time:
        params["end_time"] = end_time
    data = _api_get(f"/indicators/rsi/{symbol.upper()}", params)

    current = data["current"]
    if current < 30:
        signal = "OVERSOLD"
    elif current > 70:
        signal = "OVERBOUGHT"
    else:
        signal = "NEUTRAL"

    lines = [f"{data['symbol']} RSI({period}) {data['interval']}: {current:.1f} [{signal}]"]
    for v in data["values"]:
        lines.append(f"{v['time'][5:16]}: {v['value']:.1f}")

    return "\n".join(lines)


@mcp.tool()
def get_macd(
    symbol: str,
    interval: str = "1h",
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
    limit: int = 10,
    start_time: str | None = None,
    end_time: str | None = None,
) -> str:
    """Get MACD (Moving Average Convergence Divergence) for a cryptocurrency.

    MACD shows trend direction and momentum:
    - MACD > 0: Bullish momentum
    - MACD < 0: Bearish momentum
    - MACD crossing above signal line: Buy signal
    - MACD crossing below signal line: Sell signal

    Args:
        symbol: Trading pair symbol (e.g., BTCUSDT, ETHUSDT)
        interval: Candle interval - 1m, 5m, 15m, 30m, 1h, 4h, 1d
        fast: Fast EMA period (default 12)
        slow: Slow EMA period (default 26)
        signal: Signal line period (default 9)
        limit: Number of values to return (default 10)
        start_time: Start time in ISO format (e.g., 2024-01-01)
        end_time: End time in ISO format (e.g., 2024-02-01)

    Returns:
        MACD values with trend interpretation
    """
    params: dict[str, Any] = {"interval": interval, "fast": fast, "slow": slow, "signal": signal, "limit": limit}
    if start_time:
        params["start_time"] = start_time
    if end_time:
        params["end_time"] = end_time
    data = _api_get(f"/indicators/macd/{symbol.upper()}", params)

    current = data["current"]
    trend = "BULLISH" if current > 0 else "BEARISH"

    lines = [f"{data['symbol']} MACD({fast},{slow},{signal}) {data['interval']}: {current:.2f} [{trend}]"]
    for v in data["values"]:
        lines.append(f"{v['time'][5:16]}: {v['value']:.2f}")

    return "\n".join(lines)


@mcp.tool()
def get_bollinger_bands(
    symbol: str,
    interval: str = "1h",
    period: int = 20,
    std_dev: float = 2.0,
    limit: int = 10,
    start_time: str | None = None,
    end_time: str | None = None,
) -> str:
    """Get Bollinger Bands for a cryptocurrency.

    Bollinger Bands show volatility and potential reversal points:
    - %B > 1: Price above upper band (overbought)
    - %B < 0: Price below lower band (oversold)
    - %B = 0.5: Price at middle band

    Args:
        symbol: Trading pair symbol (e.g., BTCUSDT, ETHUSDT)
        interval: Candle interval - 1m, 5m, 15m, 30m, 1h, 4h, 1d
        period: SMA period (default 20)
        std_dev: Standard deviation multiplier (default 2.0)
        limit: Number of values to return (default 10)
        start_time: Start time in ISO format (e.g., 2024-01-01)
        end_time: End time in ISO format (e.g., 2024-02-01)

    Returns:
        Bollinger Bands with %B position indicator
    """
    params: dict[str, Any] = {"interval": interval, "period": period, "std_dev": std_dev, "limit": limit}
    if start_time:
        params["start_time"] = start_time
    if end_time:
        params["end_time"] = end_time
    data = _api_get(f"/indicators/bbands/{symbol.upper()}", params)

    current = data["current"]
    pct_b = current["percent_b"]

    if pct_b > 1:
        signal = "OVERBOUGHT"
    elif pct_b < 0:
        signal = "OVERSOLD"
    else:
        signal = "NEUTRAL"

    lines = [f"{data['symbol']} BB({period}) {data['interval']}: %B={pct_b:.2f} [{signal}]"]
    lines.append(f"Current: U:{current['upper']:.2f} M:{current['middle']:.2f} L:{current['lower']:.2f}")
    for v in data["values"]:
        lines.append(f"{v['time'][5:16]}: U:{v['upper']:.2f} M:{v['middle']:.2f} L:{v['lower']:.2f} %B:{v['percent_b']:.2f}")

    return "\n".join(lines)


@mcp.tool()
def get_stochastic(
    symbol: str,
    interval: str = "1h",
    fastk_period: int = 14,
    slowk_period: int = 3,
    limit: int = 10,
    start_time: str | None = None,
    end_time: str | None = None,
) -> str:
    """Get Stochastic Oscillator for a cryptocurrency.

    Stochastic measures momentum on a scale of 0-100:
    - Below 20: Oversold (potential buy signal)
    - Above 80: Overbought (potential sell signal)

    Args:
        symbol: Trading pair symbol (e.g., BTCUSDT, ETHUSDT)
        interval: Candle interval - 1m, 5m, 15m, 30m, 1h, 4h, 1d
        fastk_period: Fast %K period (default 14)
        slowk_period: Slow %K period (default 3)
        limit: Number of values to return (default 10)
        start_time: Start time in ISO format (e.g., 2024-01-01)
        end_time: End time in ISO format (e.g., 2024-02-01)

    Returns:
        Stochastic values with interpretation
    """
    params: dict[str, Any] = {"interval": interval, "fastk_period": fastk_period, "slowk_period": slowk_period, "limit": limit}
    if start_time:
        params["start_time"] = start_time
    if end_time:
        params["end_time"] = end_time
    data = _api_get(f"/indicators/stoch/{symbol.upper()}", params)

    current = data["current"]
    if current < 20:
        signal = "OVERSOLD"
    elif current > 80:
        signal = "OVERBOUGHT"
    else:
        signal = "NEUTRAL"

    lines = [f"{data['symbol']} STOCH({fastk_period},{slowk_period}) {data['interval']}: {current:.1f} [{signal}]"]
    for v in data["values"]:
        lines.append(f"{v['time'][5:16]}: {v['value']:.1f}")

    return "\n".join(lines)


@mcp.tool()
def get_adx(
    symbol: str,
    interval: str = "1h",
    period: int = 14,
    limit: int = 10,
    start_time: str | None = None,
    end_time: str | None = None,
) -> str:
    """Get ADX (Average Directional Index) for a cryptocurrency.

    ADX measures trend strength (not direction) on a scale of 0-100:
    - Below 20: Weak or no trend
    - 20-40: Developing trend
    - 40-60: Strong trend
    - Above 60: Very strong trend

    Args:
        symbol: Trading pair symbol (e.g., BTCUSDT, ETHUSDT)
        interval: Candle interval - 1m, 5m, 15m, 30m, 1h, 4h, 1d
        period: ADX period (default 14)
        limit: Number of values to return (default 10)
        start_time: Start time in ISO format (e.g., 2024-01-01)
        end_time: End time in ISO format (e.g., 2024-02-01)

    Returns:
        ADX values with trend strength interpretation
    """
    params: dict[str, Any] = {"interval": interval, "period": period, "limit": limit}
    if start_time:
        params["start_time"] = start_time
    if end_time:
        params["end_time"] = end_time
    data = _api_get(f"/indicators/adx/{symbol.upper()}", params)

    current = data["current"]
    if current < 20:
        signal = "WEAK"
    elif current < 40:
        signal = "DEVELOPING"
    elif current < 60:
        signal = "STRONG"
    else:
        signal = "VERY_STRONG"

    lines = [f"{data['symbol']} ADX({period}) {data['interval']}: {current:.1f} [{signal}]"]
    for v in data["values"]:
        lines.append(f"{v['time'][5:16]}: {v['value']:.1f}")

    return "\n".join(lines)


@mcp.tool()
def get_atr(
    symbol: str,
    interval: str = "1h",
    period: int = 14,
    limit: int = 10,
    start_time: str | None = None,
    end_time: str | None = None,
) -> str:
    """Get ATR (Average True Range) for a cryptocurrency.

    ATR measures volatility - higher values mean more volatility.
    Useful for setting stop-losses and position sizing.

    Args:
        symbol: Trading pair symbol (e.g., BTCUSDT, ETHUSDT)
        interval: Candle interval - 1m, 5m, 15m, 30m, 1h, 4h, 1d
        period: ATR period (default 14)
        limit: Number of values to return (default 10)
        start_time: Start time in ISO format (e.g., 2024-01-01)
        end_time: End time in ISO format (e.g., 2024-02-01)

    Returns:
        ATR values showing volatility
    """
    params: dict[str, Any] = {"interval": interval, "period": period, "limit": limit}
    if start_time:
        params["start_time"] = start_time
    if end_time:
        params["end_time"] = end_time
    data = _api_get(f"/indicators/atr/{symbol.upper()}", params)

    current = data["current"]

    lines = [f"{data['symbol']} ATR({period}) {data['interval']}: {current:.2f}"]
    for v in data["values"]:
        lines.append(f"{v['time'][5:16]}: {v['value']:.2f}")

    return "\n".join(lines)


# === Economic Calendar ===


@mcp.tool()
def get_economic_calendar(days: int = 7, event_type: str | None = None) -> str:
    """Get upcoming high-impact economic events.

    These events move markets significantly:
    - FOMC: Federal Reserve rate decisions (8 per year)
    - CPI: Consumer Price Index / inflation (monthly)
    - NFP: Non-Farm Payrolls / employment (monthly)

    Args:
        days: Number of days to look ahead (default 7)
        event_type: Filter by type - FOMC, CPI, or NFP (optional)

    Returns:
        List of upcoming economic events with dates and times
    """
    params = {"days": days}
    if event_type:
        params["event_type"] = event_type
    data = _api_get("/calendar/events", params)

    if not data["events"]:
        return f"No {event_type or 'economic'} events in next {days} days"

    lines = [f"Economic Calendar (next {days} days)"]
    for e in data["events"]:
        lines.append(f"{e['date']} {e['time']} ET: {e['event']} - {e['name']}")

    return "\n".join(lines)


@mcp.tool()
def get_next_events(limit: int = 5) -> str:
    """Get the next upcoming economic events.

    Quick way to see what's coming up that could move markets.

    Args:
        limit: Number of events to return (default 5)

    Returns:
        Next upcoming economic events
    """
    data = _api_get("/calendar/next", {"limit": limit})

    lines = ["Upcoming Events"]
    for e in data["events"]:
        lines.append(f"{e['date']} {e['time']} ET: {e['event']} - {e['name']}")

    return "\n".join(lines)


@mcp.tool()
def get_news(
    category: str = "general",
    limit: int = 10,
) -> str:
    """Get latest market news.

    Use this to understand what's happening in the markets right now.
    News can explain price movements and help predict future trends.

    Args:
        category: News category - general, forex, crypto, merger
        limit: Number of news items to return (default 10)

    Returns:
        Latest news headlines with sources and links
    """
    data = _api_get(f"/news/{category}", {"limit": limit})

    lines = [f"{data['category'].upper()} NEWS ({data['count']})"]
    for item in data["news"]:
        t = item["datetime"][5:16]
        lines.append(f"[{t}] {item['headline']} ({item['source']}) {item['url']}")

    return "\n".join(lines)


@mcp.tool()
def get_fear_greed() -> str:
    """Get Crypto Fear & Greed Index.

    Measures overall market sentiment. Useful for timing entries/exits.
    - 0-24: Extreme Fear (potential buy opportunity - "be greedy when others are fearful")
    - 25-49: Fear
    - 50-74: Greed
    - 75-100: Extreme Greed (potential sell signal - "be fearful when others are greedy")

    Returns:
        Current Fear & Greed Index value and classification
    """
    data = _api_get("/sentiment/fear-greed")
    return f"Fear & Greed: {data['value']} [{data['classification']}]"


@mcp.tool()
def get_funding_rates(symbols: str = "BTCUSDT,ETHUSDT") -> str:
    """Get funding rates from Binance Futures.

    Funding rates show long/short sentiment in the derivatives market:
    - Positive rate: More longs than shorts (bullish sentiment, but potential reversal down)
    - Negative rate: More shorts than longs (bearish sentiment, but potential reversal up)
    - High absolute rate (>0.1%): Extreme sentiment, reversal more likely

    Args:
        symbols: Comma-separated trading pair symbols (e.g., BTCUSDT,ETHUSDT,SOLUSDT)

    Returns:
        Current funding rates for the requested symbols
    """
    data = _api_get("/sentiment/funding-rates", {"symbols": symbols})

    lines = ["Funding Rates"]
    for item in data["rates"]:
        lines.append(f"{item['symbol']}: {item['funding_rate_percent']:.4f}%")

    return "\n".join(lines)


@mcp.tool()
def get_open_interest(symbol: str) -> str:
    """Get open interest for a futures symbol.

    Open interest = total outstanding contracts. Shows market participation.
    Rising OI + rising price = strong bullish trend
    Rising OI + falling price = strong bearish trend
    Falling OI = trend weakening, positions closing

    Args:
        symbol: Trading pair symbol (e.g., BTCUSDT, ETHUSDT)

    Returns:
        Open interest in contracts and USD value
    """
    data = _api_get(f"/futures/open-interest/{symbol.upper()}")
    oi = data["open_interest"]
    val = data["open_interest_value"]

    if val >= 1_000_000_000:
        val_str = f"${val/1_000_000_000:.2f}B"
    else:
        val_str = f"${val/1_000_000:.1f}M"

    return f"{data['symbol']} OI: {oi:,.0f} contracts ({val_str})"


@mcp.tool()
def get_long_short_ratio(symbol: str) -> str:
    """Get long/short account ratio for a futures symbol.

    Shows percentage of accounts that are long vs short.
    Ratio > 1: More accounts are long (bullish sentiment)
    Ratio < 1: More accounts are short (bearish sentiment)
    Extreme ratios often precede reversals (contrarian signal).

    Args:
        symbol: Trading pair symbol (e.g., BTCUSDT, ETHUSDT)

    Returns:
        Long/short ratio and percentages
    """
    data = _api_get(f"/futures/long-short-ratio/{symbol.upper()}")
    ratio = data["long_short_ratio"]
    long_pct = data["long_account"] * 100
    short_pct = data["short_account"] * 100

    return f"{data['symbol']} L/S: {ratio:.2f} (Long:{long_pct:.1f}% Short:{short_pct:.1f}%)"


@mcp.tool()
def get_top_trader_ratio(symbol: str) -> str:
    """Get top trader long/short ratio.

    Shows what the top traders (whales) are doing.
    More reliable signal than overall ratio - follow the smart money.

    Args:
        symbol: Trading pair symbol (e.g., BTCUSDT, ETHUSDT)

    Returns:
        Top trader long/short ratio and percentages
    """
    data = _api_get(f"/futures/top-trader-ratio/{symbol.upper()}")
    ratio = data["long_short_ratio"]
    long_pct = data["long_account"] * 100
    short_pct = data["short_account"] * 100

    return f"{data['symbol']} Top Traders L/S: {ratio:.2f} (Long:{long_pct:.1f}% Short:{short_pct:.1f}%)"


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()

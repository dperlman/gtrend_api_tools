# API Implementations

The package supports multiple API implementations for accessing Google Trends data. Each implementation has its own advantages and limitations.

## Available APIs

### AppleScript Safari (Free)
- Uses AppleScript to automate Safari browser
- No API key required
- Limited to macOS systems
- Slower but reliable

### SerpAPI (Paid)
- Uses SerpAPI service
- Requires API key
- Fast and reliable
- Rate limits apply

### TrendsPy (Free)
- Uses pytrends library
- No API key required
- Good for basic use cases
- May have rate limits

### Windows UIAutomation Edge (Free)
- Uses Windows UI Automation
- Limited to Windows systems
- No API key required
- Browser automation based

## API Selection

When initializing the Trends class, you can specify which API to use:

```python
from gtrend_api_tools import Trends

# Use AppleScript Safari
trends = Trends(api="applescript_safari")

# Use SerpAPI
trends = Trends(api="serpapi")

# Use TrendsPy
trends = Trends(api="trendspy")
```

## API Information

You can get information about available APIs:

```python
from gtrend_api_tools import load_config

# Load config and get available APIs
config = load_config()
all_apis = config.get('available_apis', {})
free_apis = {name: info for name, info in all_apis.items() if info['type'] == 'free'}
paid_apis = {name: info for name, info in all_apis.items() if info['type'] == 'paid'}
```

## API Configuration

Each API implementation may require specific configuration. See the configuration section for details on how to set up each API. 
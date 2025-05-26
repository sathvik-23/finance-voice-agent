# API Key Rotation Guide for Finance Voice Agent

This guide explains how to set up multiple OpenAI API keys for your Finance Voice Agent application to increase reliability and avoid quota limitations.

## Why Use Multiple API Keys?

Using multiple API keys provides several benefits:

1. **Redundancy**: If one key reaches its quota limit, the app automatically tries the next key
2. **Higher Availability**: You can continue using the app even if some keys have issues
3. **Load Distribution**: Requests can be spread across multiple keys, reducing the chance of hitting rate limits
4. **Graceful Degradation**: The app falls back to mock responses only when all keys are exhausted

## How to Set Up Multiple API Keys

### 1. Obtain OpenAI API Keys

First, you need to obtain multiple OpenAI API keys:

1. Create one or more OpenAI accounts (or use keys from different team members)
2. Generate API keys from the [OpenAI platform](https://platform.openai.com/api-keys)
3. Note down each API key (they start with "sk-")

### 2. Add Keys to the Application

Open the `multi_key_app.py` file and locate the `API_KEYS` list near the top of the file:

```python
# API Key Management
API_KEYS = [
    # Primary key from .env file
    os.getenv("OPENAI_API_KEY", ""),
    
    # Add your additional API keys here
    # "sk-abc123...",
    # "sk-def456...",
    # etc.
]
```

Add your API keys to this list by uncommenting and replacing the placeholder values:

```python
API_KEYS = [
    # Primary key from .env file
    os.getenv("OPENAI_API_KEY", ""),
    
    # Add your additional API keys here
    "sk-yourfirstkey...",
    "sk-yoursecondkey...",
    "sk-yourthirdkey...",
]
```

### 3. Security Considerations

**Important**: In a production environment, you should never hardcode API keys in your source code. Instead:

1. Use environment variables or a secure key management service
2. For a more secure approach, modify the app to load keys from a secure file or database
3. Implement proper access controls to prevent unauthorized access to your keys

### 4. Testing the Key Rotation

To test if your key rotation is working:

1. Run the application: `streamlit run multi_key_app.py`
2. Make several queries until one of your keys hits its quota limit
3. Check the sidebar to see the API Key Status, which shows:
   - Total keys available
   - Number of working keys
   - Number of failed keys
4. If all keys fail, the app will automatically switch to mock mode

### 5. Resetting Failed Keys

If you want to retry keys that previously failed (e.g., after waiting for quota to reset):

1. Click the "Reset Failed Keys" button in the sidebar
2. All keys will be marked as available again
3. The app will attempt to use them in the original order

## Advanced Configuration

For advanced users, you can modify the key rotation strategy in the `get_next_api_key()` function:

- Change the order of key selection (e.g., random instead of sequential)
- Implement more sophisticated fallback logic
- Add automatic retry with exponential backoff for rate-limited keys

## Troubleshooting

If you encounter issues with API key rotation:

1. **Check Key Validity**: Ensure all keys are valid and have not expired
2. **Verify Quota**: Check your usage on the OpenAI dashboard
3. **API Changes**: Make sure your code is compatible with the latest OpenAI API
4. **Connectivity**: Ensure your application can connect to the OpenAI API

## Mock Mode Fallback

When all API keys fail, the application automatically switches to mock mode, which:

1. Uses predefined responses based on query keywords
2. Simulates the application's behavior without making API calls
3. Clearly indicates when a response is a mock (not from the actual API)

This ensures the application remains functional even when no valid API keys are available.

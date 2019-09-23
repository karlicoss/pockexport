Export your personal Pocket data, including highlights as JSON.

# Setting up
1. `pip3 install -r requirements.txt`
2. To use the API you need a `consumer_key`. You've got two alternatives here:
   * Lawful good way: register an app [here](https://getpocket.com/developer/apps/new) with 'Retrieve' permissions and type 'Desktop (other)'.
     Open app in the list and take note of `consumer_key`.
   * Chaotic way: get API key directly from web app. 
     The benefit of doing this is that API gives away more data, **including highlights**.
     
     To do that, go to [Pocket web app](https://app.getpocket.com), open Network Monitor from your browser dev tools 
     (e.g. [firefox](https://developer.mozilla.org/en-US/docs/Tools/Network_Monitor#UI_overview)), and refresh the page.
     
     You can find `consumer_key` in 'Request URL' for any of `json` requests.
     
     This is sort of hacky, but only way I know of extracting highlights. I tried registering apps targeting other platforms (e.g. web/extension), but still nothing, seems that Pocket's consumer key is hardcoded in backend code or something.
3. Follow [these](https://github.com/tapanpandita/pocket#oauth) instructions to retrieve an API token using `consumer_key` you got on the previous step. You can use anything as `redirect_uri`, e.g. `https://example.com`. You should get `access_token` after that.
4. It might be convenient to dump these in a file, e.g. `secrets.py`
```
consumer_key = ...
access_token = ...
```

# Using
**Recommended**: `./export --secrets /path/to/secrets.py`. That way you have to type less and have control over where you're keeping your plaintext tokens/passwords.

Alternatively, you can pass auth arguments directly, e.g. `./export --consumer_key <key> --access_token <token>`.
However, this is prone to leaking your keys in shell history.

You can also import script and call `get_json` function directory to get raw json.

# Limitations
I'm not aware of any limits on number of old entries you can retrieve through API; it doesn't even have pagination. If you know of them, please let me know or open PR!

It's **highly** recommended to back up regularly and keep old versions. Easy way to achieve it is command like this: `./export --secrets secrets.py >"export-$(date -I).json"`.


# Example output
See [./example-output.json](example-output.json), it's got some example data you might find in your data export.

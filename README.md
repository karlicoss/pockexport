See [pocket#oauth](https://github.com/tapanpandita/pocket#oauth) for instructions on retreiving `access_token`.

 
# Using `consumer_key` from app.getpocket.com to get highlights
By default API doesn't give away your highlights. If you look at [`get` documentation](https://getpocket.com/developer/docs/v3/retrieve), closest to what you want would be `detailType='complete'`, however I tried it and while it does add 'authors', 'image', 'images' and 'tags', highlights are still missing. 

However, if you play with pocket website and Chrome inspector, you'll see highlights in JSON responses. So it looks like highlights are sent by the backend to some consumer keys and aren't sent to other.
I've tried other app types like 'web' and 'extension' and that didn't seem to make a difference, so I just took the one web uses and it works!

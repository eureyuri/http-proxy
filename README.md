The IP address for my proxy is localhost and the port number I used was 8080.

To implement caching, I used the OS file system to store the received files.
Each time I get a 200 or 301 response for the first time, I would retrieve this
data before sending it back to the client and store it in the specified
directory + file. In the case of a 301, I first requested the new location to
get a 200 and stored this file in the cache. (For 404 I did not cache anything)
When the client requests, I first check if the directory and file exists in my
local file system and if it exists, without connecting to the server, I directly
sent back this cached file.

I did not attempt the extra credit questions.

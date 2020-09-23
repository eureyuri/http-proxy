# HTTP Proxy Server
Written in Python using the Socket API
<br>
The proxy will receive a GET request and communicate with the server. The proxy is able to receive files from the server, cache it, and forward it to the client. 
It handles 404 and 301 errors. 

## How to run
0. Clone this repo

1. Run the server with 
`python3 server.py`

2. Establish a connection with a client with 
`python3 proxy.py <Listen-Port>`
- Replace `Listen-Port` with for example 8080.

3. Make a get request such as: 
`http://​localhost:8080​/​www.columbia.edu/~ge2211/4119/test2/www.hats.com/`

## Implementation details
The IP address for my proxy is localhost and the port number I used was 8080.

To implement caching, I used the OS file system to store the received files.
Each time I get a 200 or 301 response for the first time, I would retrieve this
data before sending it back to the client and store it in the specified
directory + file. In the case of a 301, I first requested the new location to
get a 200 and stored this file in the cache. (For 404 I did not cache anything)
When the client requests, I first check if the directory and file exists in my
local file system and if it exists, without connecting to the server, I directly
sent back this cached file.

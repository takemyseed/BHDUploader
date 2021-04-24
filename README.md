
  *TODO

* ADD Clients
* ADD Disk
* Improving Naming
* ADD Template System

# Install
A Virtual environment is recommended. \
Please Make sure you are on python3 and NOT python2 \
Specifically python3.6 or higher 

## Windows

### Clone the repository
git clone https://github.com/excludedBittern8/bhd-Uploader
cd bhd-Uploader
###  Installing Virtualenv
py -m pip install --user virtualenv
### Creating virtualenv
python3 -m venv venv  or  py -m venv venv
### Installing Modules
venv\Scripts\pip3.exe install -r requirements.txt
### Running Python
venv\Scripts\python

## Linux

###  Installing Virtualenv
python3 -m pip install --user virtualenv
### Creating Virtualenv
python3 -m venv venv
### Installing Modules
./venv/bin/pip3 install -r requirements.txt
### Running Pyhon
/venv/bin/python3

# Parameters

## [general]  
`--media:Can be a path or directory to upload torrents from. ` 



### optional 
`--batchmode: Start batchmode` 
> If a directory batchmode will start. Which will **non-recursively** scan the drive \
> and output the result as menu. Where you can select the file/folder to upload. \
> **Non-recursive** meaning what you see if you click the directory once. 

For example: \
`bhd_uploader --batchmode False`
> If you want to upload an entire folder as one upload, even if it has subfolders 

`--config:Pass arguments via a file instead of command-line. 
> example.config is provided` 

`--log:set log level ` \
**This does not take a path.**  This controls how much information is written to a log file. \
From highest to lowest \
DEBUG,INFO,WARN (case-insensitive). 
Default is WARN \
logs are written within the bhdupload folder in a subfolder called **LOGS** If your having issues \
--log debug  \
it will provide information about the process which will tell what an issue might be. 

## [Client]

`--client:name of client`
 >    rtorrent \
 >    qbit \
 >    transmission \
 >    deluge \
 >    watchdir:send torrent to dir

`--clientpass:For clients that need passwords for auth` \
`--clientuser:For clients that need usernames for auth` \
`--clientcat:grouping of torrents` 
>Naming my differ depending on client, this is the label,category,   etc   that your torrent will be  >added as in the client 

`--clienturl:url for the client `


## [bhd Auth]
 These are all required to upload, auto retrieve upload link  

`--bhdapi:apikey from security` \
`--tmdbpapi:apikey provided by tmdb` \
`--imbgg:For uploading to imgbb, you can make an anon account` 

## [Torrent]
    
> These parameters control the final upload \ 
> Other then imdb,screenshots. They are all optional \
`--numscreens:optional argument to change how many screens shots, default is 9` \
`--live:optional upoad live torrent rather then send to drafts` 

 These upcoming parameters should not be changed at the moment in batchmode \
 As they will not reset after the first upload. 
  
> --imdb \
> --tmdb \
> --mediatype \
> --type 

 ## [Programs]  
> These control the paths to the required programs. Only change if you want to use your own binaries
On windows please enter the fullpath. You can usually find that by 
1. Enter python 
2. from sys import which
3. which(program)

There is some combability issues with using path and windows, that causes issues with other commands in the program. So full paths are required on that plaform
    
`--wget:optional argument to change path to wget, programs comes with binary` \
`--dottorrent : optional argument to change path to dottorent, programs comes with binary` \
`--oxipng:optional argument to change path to oxipng, programs comes with binary` \
`--mtn:optional argument to change path to mtn, programs comes with binary` \
`--font:optional argument to change the ttf font file. Program comes with it own. Used for screenshots`

# Examples
    *Anything in brackets is to replace by user value
## Rtorrent
`bhd_uploader.py  --client rtorrent --clienturl  <url> --media <path> --bhdapi <api> -- tmdbpapi <tmdbapi> --imgbb <apikey>`
    
> optional:
> --clientcat

## Watchdir
`bhd_uploader.py  --media <path> --bhdapi <api> -- tmdbpapi <tmdbapi> --imgbb <apikey>`
## Config
`bhd_uploader.py --config <configpath>`
> Make sure your config is filled with all required info,for example rtorrent needs all the > \ paramters from the rtorrent example. For Parameter Usage Please Go to the Parameter section \
> commandline options will replace any option in the config
  
Anything in brackets is to replace by user value
## Rtorrent
`bhd_uploader.py  --client rtorrent --clienturl  <url> --media <path> --bhdapi <api> -- tmdbpapi <tmdbapi> --imgbb <apikey>`
    
> optional:
> --clientcat

## Watchdir
`bhd_uploader.py  --media <path> --bhdapi <api> -- tmdbpapi <tmdbapi> --imgbb <apikey>`
## Config
`bhd_uploader.py --config <configpath>`
> Make sure your config is filled with all required info,for example rtorrent needs all the > \ paramters from the rtorrent example. For Parameter Usage Please Go to the Parameter section \
> commandline options will replace any option in the config






 
    

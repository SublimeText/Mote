# Info

Sublime Text plugin to browse and edit files over sftp/ssh2

- Uses the power of the quick panel completions to browse around files
- Automatically hooks into file saves and uploads after saving
- Optionally, continues to spider the file tree populating the quick panel list

# Installation

1. Download this package and save and extract to your packages folder.

2. Download and install PuTTY, preferably the whole package.

   - (PuTTYgen is needed to create keys)
   
   - (PuTTY is needed to save sessions, (host,username,key information)
   
   - (Pageant to manage those sessions)
   
   - http://www.chiark.greenend.org.uk/~sgtatham/putty/download.html

3. Make psftp accessible to the plugin
   
   - Copy `psftp.exe` to `Mote\`

#Usage

## Add Servers

edit the `Mote\serves.json` file



connection_string
  connection string that's going to be passed to psftp
  See http://the.earth.li/~sgtatham/putty/0.61/htmldoc/Chapter6.html#psftp-pubkey

idle_recursive
  whether or not Mote should spider your sftp in the background

default_path
  default path to `cd` into
  
password
  password for sftp. Use this option if your PuTTY session name or password contains a space
  
private_key
  path to private key. Remember to escape the `\` into `\\`

NOTE: if you wish to place your password here, it cannot contain a '!'
Due to limitations of psftp
See http://the.earth.li/~sgtatham/putty/0.61/htmldoc/Chapter6.html#psftp-cmd-pling

### servers.json

Make sure you have a valid json object here.
http://jsonlint.com/

```json
{
    "SERVER_NICKNAME":{
        "connection_string": "saved_putty_session_name",
        "idle_recursive": true
    },
    "SERVER_NICKNAME2":{
        "connection_string": "USERNAME@HOSTNAME_OR_IP",
        "password":"MYPASSWORD",
        "idle_recursive": false,
        "default_path": "iniital/path/to/open/to"
    },
    "SERVER_NICKNAME3":{
        "connection_string": "USERNAME@HOSTNAME_OR_IP",
        "password":"MYPASSWORD",
        "private_key":"C:\\PATH\\TO\\PRIVATE\\KEY.ppk",
        "idle_recursive": false,
        "default_path": "iniital/path/to/open/to"
    }
}
```

## Then Invoke Mote

### Run through the command palette

    Ctrl+Shift+P
    Mote
    Enter
    
### Or, Add to your keybinds

```json
{ "keys": ["ctrl+m"], "command": "mote" }
```
    
Then

   `Ctrl+m`

## Then browse around and edit

- Browse around. The file list populates as you delve deeper into the file tree.
- Click on a file to download to a temp folder and open it
- Any saves on that file will automatically upload it. 

# sync-glacier
Provides simple command line interface for Amazon Glacier. Now supports creation and deletion of vaults + uploading folders. Script creates .zip archive from folder and upload it to vault.
##Configuration
First of all you should set parameters of vault and backup. Standart config file looks like that.
```
AKIAIOSFODNN7EXAMPLE
wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
vault-name|eu-central-1
push_to_folder_for_backup1 | push_to_folder_for_backup2
```
First two rows id Amazon access key ID and secret key.
Then write name of vault and region. Divide them by '|'.
After that write paths to folders, that you want to backup. You can write as many paths, as you wish.

After retrieving inventory all subsequent raws will store inventory in format:
```
name | id | size
```

Сonfiguration file must always named "config.f"
##Installation
At first downlod all files to one folder. If you want to setup auto-backup every week, then run setup_backup.sh.
This script requires [`boto`](https://github.com/boto/boto), so setup_backup.sh will be automatically installed, if it was not previously installed.
Also it will write itself to cron.
Then script will start for first time and create vault. Logs will be written to backup.log file.

##Usage
```
python sync-glacier.py [-h | -c | -dv | -b]
```
* **-h, --help** - man
* **-c, --create** - create vault
* **-dv, --delete** - delete vault
* **-b, --backup** - backup folders

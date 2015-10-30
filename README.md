# glacier-cli
Simple and lightweight script, that provides command line interface for Amazon Glacier. Now supports creation and deletion of vaults, uploading and downloading folders, . Script creates .zip archive from folder and upload it to vault.
##Configuration
First of all you should set parameters of vault and backup. Standart config file on first start looks like that:
```
AKIAIOSFODNN7EXAMPLE
wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
vault-name|eu-central-1
path_to_folder_for_backup1 | path_to_folder_for_backup2
```
First two lines are Amazon access key ID and secret key.
Then write name of vault and region. Divide them by '|'.
After that write paths to folders, that you want to backup. You can write as many paths, as you wish.  Divide them by '|'.
Next line stores inventory retrieval job id (if it was started).

Next data block is inventory block. 
After retrieving inventory it stores inventory size and all archives descriptions in format:
```
name | id | size
```

Next data block stores retrieveng jobs descriptions, if you initialize downloading from inventory.
All subsequent lines are job descriptions in format:
```
retrieved archive name | job id
```

Сonfiguration file must always has name "config.f"
##Installation
At first downlad all files to one folder. If you want to setup auto-backup every week, then run setup_backup.sh.
This script requires [`boto`](https://github.com/boto/boto), so setup_backup.sh will automatically install it, if it was not previously installed.
Also it will write itself to [`cron`](https://wikipedia.org/wiki/Cron).
Then script will start for first time and create vault. Logs will be written to backup.log file.

##Usage
```
python sync-glacier.py [-h | -c | -dv | -b | -i | -g | -lv | -lj]
```
* **-h,  --help**         - manual
* **-c,  --create**       - Create new vault
* **-dv, --delete**       - Delete vault
* **-b,  --backup**       - Immediately backup data
* **-i,  --inventory**    - Initialize invertory retrieving job
* **-g,  --get**          - Get all archives in vault
* **-lv, --list_vaults**  - List all vaults
* **-lj, --list_jobs**    - List all running jobs

**Notice** that you might have problems with downloading from vault, if you use "Free Tier" data retrieval policy


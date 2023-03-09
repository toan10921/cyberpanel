import argparse
import json
import os
import sys
import time
import requests

sys.path.append('/usr/local/CyberCP')
import django
import plogical.CyberCPLogFileWriter as logging
import plogical.mysqlUtilities as mysqlUtilities

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "CyberCP.settings")
try:
    django.setup()
except:
    pass

from plogical.processUtilities import ProcessUtilities


class CPBackupsV2:
    PENDING_START = 0
    RUNNING = 1
    COMPLETED = 2
    FAILED = 3

    ### RCLONE BACKEND TYPES
    SFTP = 1
    LOCAL = 2

    RUSTIC_PATH = '/usr/bin/rustic'
    RCLONE_CONFIG = '/root/.config/rclone/rclone.conf'
    command = 'rclone obscure hosting'

    def __init__(self, data):
        self.data = data

        ### set self.website as it is needed in many functions
        from websiteFunctions.models import Websites
        self.website = Websites.objects.get(domain=self.data['domain'])

        ## Set up the repo name to be used

        self.repo = f"rclone:{self.data['BackendName']}:{self.data['domain']}"
        self.snapshots = []


    def FetchSnapShots(self):
        try:
            command = f'rustic -r {self.repo} snapshots --password "" --json 2>/dev/null'
            result = json.loads(
                ProcessUtilities.outputExecutioner(command, self.website.externalApp, True).rstrip('\n'))
            return 1, result
        except BaseException as msg:
            return 0, str(msg)

    def SetupRcloneBackend(self, type, config):
        self.LocalRclonePath = f'/home/{self.website.domain}/.config/rclone'
        self.ConfigFilePath = f'{self.LocalRclonePath}/rclone.conf'

        command = f'mkdir -p {self.LocalRclonePath}'
        ProcessUtilities.executioner(command, self.website.externalApp)

        if type == CPBackupsV2.SFTP:
            ## config = {"name":, "host":, "user":, "port":, "path":, "password":,}
            command = f'rclone obscure {config["password"]}'
            ObsecurePassword = ProcessUtilities.outputExecutioner(command).rstrip('\n')

            content = f'''[{config["name"]}]
type = sftp
host = {config["host"]}
user = {config["user"]}
pass = {ObsecurePassword}
'''

            command = f"echo '{content}' > {self.ConfigFilePath}"
            ProcessUtilities.executioner(command, self.website.externalApp, True)

            command = f"chmod 600 {self.ConfigFilePath}"
            ProcessUtilities.executioner(command, self.website.externalApp)

    @staticmethod
    def FetchCurrentTimeStamp():
        import time
        return str(time.time())

    def UpdateStatus(self, message, status):

        from websiteFunctions.models import Backupsv2, BackupsLogsv2
        self.buv2 = Backupsv2.objects.get(fileName=self.buv2.fileName)
        self.buv2.status = status
        self.buv2.save()

        BackupsLogsv2(message=message, owner=self.buv2).save()

        if status == CPBackupsV2.FAILED:
            self.buv2.website.BackupLock = 0
            self.buv2.website.save()

            ### delete leftover dbs if backup fails

            command = f'rm -f {self.FinalPathRuctic}/*.sql'
            ProcessUtilities.executioner(command, None, True)

        elif status == CPBackupsV2.COMPLETED:
            self.buv2.website.BackupLock = 0
            self.buv2.website.save()

    ## parent is used to link this snapshot with master snapshot
    def BackupConfig(self):
        ### Backup config file to rustic

        command = f'chown {self.website.externalApp}:{self.website.externalApp} {self.FinalPathRuctic}'
        ProcessUtilities.executioner(command)

        command = f'rustic init -r {self.repo} --password ""'
        ProcessUtilities.executioner(command, self.website.externalApp)

        #command = f'chown cyberpanel:cyberpanel {self.FinalPathRuctic}'
        #ProcessUtilities.executioner(command)

        command = f'chown {self.website.externalApp}:{self.website.externalApp} {self.FinalPathRuctic}/config.json'
        ProcessUtilities.executioner(command)

        command = f'rustic -r {self.repo} backup {self.FinalPathRuctic}/config.json --json --password "" 2>/dev/null'
        result = json.loads(ProcessUtilities.outputExecutioner(command, self.website.externalApp, True).rstrip('\n'))

        try:
            SnapShotID = result['id']  ## snapshot id that we need to store in db
            files_new = result['summary']['files_new']  ## basically new files in backup
            total_duration = result['summary']['total_duration']  ## time taken

            self.snapshots.append(SnapShotID)

        except BaseException as msg:
            self.UpdateStatus(f'Backup failed as no snapshot id found, error: {str(msg)}', CPBackupsV2.FAILED)
            return 0

        command = f'chown cyberpanel:cyberpanel {self.FinalPathRuctic}/config.json'
        ProcessUtilities.executioner(command)


    def MergeSnapshots(self):
        snapshots = ''
        for snapshot in self.snapshots:
            snapshots= f'{snapshots} {snapshot}'


        command = f'rustic -r {self.repo} merge {snapshots}  --password "" --json 2>/dev/null'
        result = json.loads(ProcessUtilities.outputExecutioner(command, self.website.externalApp, True).rstrip('\n'))

        command = f'rustic -r {self.repo} forget {snapshots}  --password ""'
        result = ProcessUtilities.outputExecutioner(command, self.website.externalApp, True)


    def InitiateBackup(self):

        from websiteFunctions.models import Websites, Backupsv2
        from django.forms.models import model_to_dict
        from plogical.mysqlUtilities import mysqlUtilities
        self.website = Websites.objects.get(domain=self.data['domain'])

        ## Base path is basically the path set by user where all the backups will be housed

        if not os.path.exists(self.data['BasePath']):
            command = f"mkdir -p {self.data['BasePath']}"
            ProcessUtilities.executioner(command)

            command = f"chmod 711 {self.data['BasePath']}"
            ProcessUtilities.executioner(command)

        self.StartingTimeStamp = CPBackupsV2.FetchCurrentTimeStamp()

        ### Init rustic repo in main func so dont need to do again and again

        while(1):

            self.website = Websites.objects.get(domain=self.data['domain'])

            if self.website.BackupLock == 0:

                Disk1 = f"du -sm /home/{self.website.domain}/"
                Disk2 = "2>/dev/null | awk '{print $1}'"


                self.WebsiteDiskUsage = int(ProcessUtilities.outputExecutioner(f"{Disk1} {Disk2}", 'root', True).rstrip('\n'))

                self.CurrentFreeSpaceOnDisk = int(ProcessUtilities.outputExecutioner("df -m / | awk 'NR==2 {print $4}'", 'root', True).rstrip('\n'))

                if self.WebsiteDiskUsage > self.CurrentFreeSpaceOnDisk:
                    self.UpdateStatus(f'Not enough disk space on the server to backup this website.', CPBackupsV2.FAILED)
                    return 0

                ### Before doing anything install rustic

                statusRes, message = self.InstallRustic()

                if statusRes == 0:
                    self.UpdateStatus(f'Failed to install Rustic, error: {message}',
                                      CPBackupsV2.FAILED)
                    return 0


                self.buv2 = Backupsv2(website=self.website, fileName='backup-' + self.data['domain'] + "-" + time.strftime("%m.%d.%Y_%H-%M-%S"), status=CPBackupsV2.RUNNING, BasePath=self.data['BasePath'])
                self.buv2.save()

                self.FinalPath = f"{self.data['BasePath']}/{self.buv2.fileName}"

                ### Rustic backup final path

                self.FinalPathRuctic = f"{self.data['BasePath']}/{self.website.domain}"


                command = f"mkdir -p {self.FinalPath}"
                ProcessUtilities.executioner(command)

                command = f"mkdir -p {self.FinalPathRuctic}"
                ProcessUtilities.executioner(command)

                #command = f"chown {website.externalApp}:{website.externalApp} {self.FinalPath}"
                #ProcessUtilities.executioner(command)

                command = f'chown cyberpanel:cyberpanel {self.FinalPath}'
                ProcessUtilities.executioner(command)

                command = f'chown cyberpanel:cyberpanel {self.FinalPathRuctic}'
                ProcessUtilities.executioner(command)

                command = f"chmod 711 {self.FinalPath}"
                ProcessUtilities.executioner(command)

                command = f"chmod 711 {self.FinalPathRuctic}"
                ProcessUtilities.executioner(command)

                try:

                    self.UpdateStatus('Creating backup config,0', CPBackupsV2.RUNNING)

                    Config = {'MainWebsite': model_to_dict(self.website, fields=['domain', 'adminEmail', 'phpSelection', 'state', 'config'])}
                    Config['admin'] = model_to_dict(self.website.admin, fields=['userName', 'password', 'firstName', 'lastName',
                                                                           'email', 'type', 'owner', 'token', 'api', 'securityLevel',
                                                                           'state', 'initself.websitesLimit', 'twoFA', 'secretKey', 'config'])
                    Config['acl'] = model_to_dict(self.website.admin.acl)

                    ### Child domains to config

                    ChildsList = []

                    for childDomains in self.website.childdomains_set.all():
                        print(childDomains.domain)
                        ChildsList.append(model_to_dict(childDomains))

                    Config['ChildDomains'] = ChildsList

                    #print(str(Config))

                    ### Databases

                    connection, cursor = mysqlUtilities.setupConnection()

                    if connection == 0:
                        return 0

                    dataBases = self.website.databases_set.all()
                    DBSList = []

                    for db in dataBases:

                        query = f"SELECT host,user FROM mysql.db WHERE db='{db.dbName}';"
                        cursor.execute(query)
                        DBUsers = cursor.fetchall()

                        UserList = []

                        for databaseUser in DBUsers:
                            query = f"SELECT password FROM `mysql`.`user` WHERE `Host`='{databaseUser[0]}' AND `User`='{databaseUser[1]}';"
                            cursor.execute(query)
                            resp = cursor.fetchall()
                            print(resp)
                            UserList.append({'user': databaseUser[1], 'host': databaseUser[0], 'password': resp[0][0]})

                        DBSList.append({db.dbName: UserList})

                    Config['databases'] = DBSList

                    WPSitesList = []

                    for wpsite in self.website.wpsites_set.all():
                        WPSitesList.append(model_to_dict(wpsite,fields=['title', 'path', 'FinalURL', 'AutoUpdates', 'PluginUpdates', 'ThemeUpdates', 'WPLockState']))

                    Config['WPSites'] = WPSitesList
                    self.config = Config

                    ### DNS Records

                    from dns.models import Domains

                    self.dnsDomain = Domains.objects.get(name=self.website.domain)

                    DNSRecords = []

                    for record in self.dnsDomain.records_set.all():
                        DNSRecords.append(model_to_dict(record))

                    Config['MainDNSDomain'] = model_to_dict(self.dnsDomain)
                    Config['DNSRecords'] = DNSRecords

                    ### Email accounts

                    try:
                        from mailServer.models import Domains

                        self.emailDomain = Domains.objects.get(domain=self.website.domain)

                        EmailAddrList = []

                        for record in self.emailDomain.eusers_set.all():
                            EmailAddrList.append(model_to_dict(record))

                        Config['MainEmailDomain'] = model_to_dict(self.emailDomain)
                        Config['EmailAddresses'] = EmailAddrList
                    except:
                        pass

                    #command = f"echo '{json.dumps(Config)}' > {self.FinalPath}/config.json"
                    #ProcessUtilities.executioner(command, self.website.externalApp, True)

                    command = f'chown cyberpanel:cyberpanel {self.FinalPathRuctic}/config.json'
                    ProcessUtilities.executioner(command)

                    WriteToFile = open(f'{self.FinalPathRuctic}/config.json', 'w')
                    WriteToFile.write(json.dumps(Config))
                    WriteToFile.close()

                    command = f"chmod 600 {self.FinalPathRuctic}/config.json"
                    ProcessUtilities.executioner(command)

                    self.BackupConfig()


                    self.UpdateStatus('Backup config created,5', CPBackupsV2.RUNNING)
                except BaseException as msg:
                    self.UpdateStatus(f'Failed during config generation, Error: {str(msg)}', CPBackupsV2.FAILED)
                    return 0

                try:
                    if self.data['BackupDatabase']:
                        self.UpdateStatus('Backing up databases..,10', CPBackupsV2.RUNNING)
                        if self.BackupDataBasesRustic() == 0:
                            self.UpdateStatus(f'Failed to create backup for databases.', CPBackupsV2.FAILED)
                            return 0

                        self.UpdateStatus('Database backups completed successfully..,25', CPBackupsV2.RUNNING)

                    if self.data['BackupData']:
                        self.UpdateStatus('Backing up website data..,30', CPBackupsV2.RUNNING)
                        if self.BackupRustic() == 0:
                            return 0
                        self.UpdateStatus('Website data backup completed successfully..,70', CPBackupsV2.RUNNING)

                    # if self.data['BackupEmails']:
                    #     self.UpdateStatus('Backing up emails..,75', CPBackupsV2.RUNNING)
                    #     if self.BackupEmailsRustic() == 0:
                    #         return 0
                    #     self.UpdateStatus('Emails backup completed successfully..,85', CPBackupsV2.RUNNING)

                    ### Finally change the backup rustic folder to the website user owner

                    command = f'chown {self.website.externalApp}:{self.website.externalApp} {self.FinalPathRuctic}'
                    ProcessUtilities.executioner(command)

                    self.MergeSnapshots()

                    self.UpdateStatus('Completed', CPBackupsV2.COMPLETED)

                    print(self.FinalPath)

                    break
                except BaseException as msg:
                    self.UpdateStatus(f'Failed, Error: {str(msg)}', CPBackupsV2.FAILED)
                    return 0
            else:
                time.sleep(5)

                ### If website lock is there for more then 20 minutes it means old backup is stucked or backup job failed, thus continue backup

                if float(CPBackupsV2.FetchCurrentTimeStamp()) > (float(self.StartingTimeStamp) + 1200):
                    self.website = Websites.objects.get(domain=self.data['domain'])
                    self.website.BackupLock = 0
                    self.website.save()

    # def BackupDataBases(self):
    #
    #     ### This function will backup databases of the website, also need to take care of database that we need to exclude
    #     ### excluded databases are in a list self.data['ExcludedDatabases'] only backup databases if backupdatabase check is on
    #     ## For example if self.data['BackupDatabase'] is one then only run this function otherwise not
    #
    #     command = f'chown {self.website.externalApp}:{self.website.externalApp} {self.FinalPathRuctic}'
    #     ProcessUtilities.executioner(command)
    #
    #     command = f'rustic init -r {self.FinalPathRuctic} --password ""'
    #     ProcessUtilities.executioner(command, self.website.externalApp)
    #
    #     command = f'chown cyberpanel:cyberpanel {self.FinalPathRuctic}'
    #     ProcessUtilities.executioner(command)
    #
    #     from plogical.mysqlUtilities import mysqlUtilities
    #
    #     for dbs in self.config['databases']:
    #
    #         ### Pending: Need to only backup database present in the list of databases that need backing up
    #
    #         for key, value in dbs.items():
    #             print(f'DB {key}')
    #
    #             if mysqlUtilities.createDatabaseBackup(key, self.FinalPath) == 0:
    #                 self.UpdateStatus(f'Failed to create backup for database {key}.', CPBackupsV2.RUNNING)
    #                 return 0
    #
    #             for dbUsers in value:
    #                 print(f'User: {dbUsers["user"]}, Host: {dbUsers["host"]}, Pass: {dbUsers["password"]}')
    #
    #
    #
    #     return 1

    def BackupDataBasesRustic(self):

        ### This function will backup databases of the website, also need to take care of database that we need to exclude
        ### excluded databases are in a list self.data['ExcludedDatabases'] only backup databases if backupdatabase check is on
        ## For example if self.data['BackupDatabase'] is one then only run this function otherwise not

        #command = f'chown {self.website.externalApp}:{self.website.externalApp} {self.FinalPathRuctic}'
        #ProcessUtilities.executioner(command)

        command = f'rustic init -r {self.repo} --password ""'
        ProcessUtilities.executioner(command, self.website.externalApp)

        command = f'chown cyberpanel:cyberpanel {self.FinalPathRuctic}'
        ProcessUtilities.executioner(command)

        from plogical.mysqlUtilities import mysqlUtilities

        for dbs in self.config['databases']:

            ### Pending: Need to only backup database present in the list of databases that need backing up

            for key, value in dbs.items():
                print(f'DB {key}')

                CurrentDBPath = f"{self.FinalPathRuctic}/{key}.sql"

                DBResult, SnapID = mysqlUtilities.createDatabaseBackup(key, self.FinalPathRuctic, 1, self.repo, self.website.externalApp)


                if DBResult == 1:
                    self.snapshots.append(SnapID)

                    #command = f'chown {self.website.externalApp}:{self.website.externalApp} {CurrentDBPath}'
                    #ProcessUtilities.executioner(command)

                    ## Now pack config into same thing

                    #command = f'chown {self.website.externalApp}:{self.website.externalApp} {self.FinalPathRuctic}/config.json'
                    #ProcessUtilities.executioner(command)

                    # command = f'rustic -r {self.repo} backup {CurrentDBPath} --password "" --json 2>/dev/null'
                    # print(f'db command rustic: {command}')
                    # result = json.loads(
                    #     ProcessUtilities.outputExecutioner(command, self.website.externalApp, True).rstrip('\n'))
                    #
                    # try:
                    #     SnapShotID = result['id']  ## snapshot id that we need to store in db
                    #     files_new = result['summary']['files_new']  ## basically new files in backup
                    #     total_duration = result['summary']['total_duration']  ## time taken
                    #
                    #     self.snapshots.append(SnapShotID)
                    #
                    #     ### Config is saved with each database, snapshot of config is attached to db snapshot with parent
                    #
                    #     #self.BackupConfig(SnapShotID)
                    #
                    #     command = f'chown cyberpanel:cyberpanel {self.FinalPathRuctic}'
                    #     ProcessUtilities.executioner(command)
                    #
                    # except BaseException as msg:
                    #     self.UpdateStatus(f'Backup failed as no snapshot id found, error: {str(msg)}',
                    #                       CPBackupsV2.FAILED)
                    #     return 0
                    #
                    #
                    # for dbUsers in value:
                    #     print(f'User: {dbUsers["user"]}, Host: {dbUsers["host"]}, Pass: {dbUsers["password"]}')
                    #
                    # command = f'rm -f {CurrentDBPath}'
                    # ProcessUtilities.executioner(command)

                else:
                    command = f'rm -f {CurrentDBPath}'
                    ProcessUtilities.executioner(command)
                    self.UpdateStatus(f'Failed to create backup for database {key}.', CPBackupsV2.FAILED)
                    return 0


        return 1

    # def BackupData(self):
    #
    #     ### This function will backup data of the website, also need to take care of directories that we need to exclude
    #     ### excluded directories are in a list self.data['ExcludedDirectories'] only backup data if backupdata check is on
    #     ## For example if self.data['BackupData'] is one then only run this function otherwise not
    #
    #     destination = f'{self.FinalPath}/data'
    #     source = f'/home/{self.website.domain}'
    #
    #     ## Pending add user provided folders in the exclude list
    #
    #     exclude = f'--exclude=.cache --exclude=.cache --exclude=.cache --exclude=.wp-cli ' \
    #               f'--exclude=backup --exclude=incbackup --exclude=incbackup --exclude=logs --exclude=lscache'
    #
    #     command = f'mkdir -p {destination}'
    #     ProcessUtilities.executioner(command, 'cyberpanel')
    #
    #     command = f'chown {self.website.externalApp}:{self.website.externalApp} {destination}'
    #     ProcessUtilities.executioner(command)
    #
    #     command = f'rsync -av {exclude}  {source}/ {destination}/'
    #     ProcessUtilities.executioner(command, self.website.externalApp)
    #
    #     return 1

    def BackupRustic(self):

        ### This function will backup data of the website, also need to take care of directories that we need to exclude
        ### excluded directories are in a list self.data['ExcludedDirectories'] only backup data if backupdata check is on
        ## For example if self.data['BackupData'] is one then only run this function otherwise not

        #command = f'chown {self.website.externalApp}:{self.website.externalApp} {self.FinalPathRuctic}'
        #ProcessUtilities.executioner(command)

        command = f'rustic init -r {self.repo} --password ""'
        ProcessUtilities.executioner(command, self.website.externalApp)

        source = f'/home/{self.website.domain}'

        #command = f'chown {self.website.externalApp}:{self.website.externalApp} {self.FinalPathRuctic}/config.json'
        #ProcessUtilities.executioner(command)

        ## Pending add user provided folders in the exclude list

        exclude = f' --exclude-if-present rusticbackup  --exclude-if-present logs '

        command = f'rustic -r {self.repo} backup {source} --password "" {exclude} --json 2>/dev/null'
        result = json.loads(ProcessUtilities.outputExecutioner(command, self.website.externalApp, True).rstrip('\n'))


        try:
            SnapShotID = result['id'] ## snapshot id that we need to store in db
            files_new = result['summary']['files_new'] ## basically new files in backup
            total_duration = result['summary']['total_duration'] ## time taken

            self.snapshots.append(SnapShotID)

            ### Config is saved with each backup, snapshot of config is attached to data snapshot with parent

            #self.BackupConfig(SnapShotID)

        except BaseException as msg:
            self.UpdateStatus(f'Backup failed as no snapshot id found, error: {str(msg)}', CPBackupsV2.FAILED)
            return 0

        #self.UpdateStatus(f'Rustic command result id: {SnapShotID}, files new {files_new}, total_duration {total_duration}', CPBackupsV2.RUNNING)

        return 1

    def BackupEmailsRustic(self):

        ### This function will backup emails of the website, also need to take care of emails that we need to exclude
        ### excluded emails are in a list self.data['ExcludedEmails'] only backup data if backupemail check is on
        ## For example if self.data['BackupEmails'] is one then only run this function otherwise not

        #command = f'chown {self.website.externalApp}:{self.website.externalApp} {self.FinalPathRuctic}'
        #ProcessUtilities.executioner(command)

        command = f'rustic init -r {self.repo} --password ""'
        ProcessUtilities.executioner(command, self.website.externalApp)

        #command = f'chown {self.website.externalApp}:{self.website.externalApp} {self.FinalPathRuctic}/config.json'
        #ProcessUtilities.executioner(command)


        source = f'/home/vmail/{self.website.domain}'

        ## Pending add user provided folders in the exclude list

        exclude = f' --exclude-if-present rusticbackup  --exclude-if-present logs '

        command = f'rustic -r {self.repo} backup {source} --password "" {exclude} --json 2>/dev/null'

        result = json.loads(ProcessUtilities.outputExecutioner(command, self.website.externalApp, True).rstrip('\n'))

        try:
            SnapShotID = result['id']  ## snapshot id that we need to store in db
            files_new = result['summary']['files_new']  ## basically new files in backup
            total_duration = result['summary']['total_duration']  ## time taken

            self.snapshots.append(SnapShotID)

            ### Config is saved with each email backup, snapshot of config is attached to email snapshot with parent

            #self.BackupConfig(SnapShotID)

        except BaseException as msg:
            self.UpdateStatus(f'Backup failed as no snapshot id found, error: {str(msg)}', CPBackupsV2.FAILED)
            return 0

        return 1

    # def BackupEmails(self):
    #
    #     ### This function will backup emails of the website, also need to take care of emails that we need to exclude
    #     ### excluded emails are in a list self.data['ExcludedEmails'] only backup data if backupemail check is on
    #     ## For example if self.data['BackupEmails'] is one then only run this function otherwise not
    #
    #     destination = f'{self.FinalPath}/emails'
    #     source = f'/home/vmail/{self.website.domain}'
    #
    #     ## Pending add user provided folders in the exclude list
    #
    #     exclude = f'--exclude=.cache --exclude=.cache --exclude=.cache --exclude=.wp-cli ' \
    #               f'--exclude=backup --exclude=incbackup --exclude=incbackup --exclude=logs --exclude=lscache'
    #
    #     command = f'mkdir -p {destination}'
    #     ProcessUtilities.executioner(command, 'cyberpanel')
    #
    #     command = f'chown vmail:vmail {destination}'
    #     ProcessUtilities.executioner(command)
    #
    #     command = f'rsync -av  {source}/ {destination}/'
    #     ProcessUtilities.executioner(command, 'vmail')
    #
    #     return 1

    def InstallRustic(self):
        try:

            if not os.path.exists(CPBackupsV2.RUSTIC_PATH):

                url = "https://api.github.com/repos/rustic-rs/rustic/releases/latest"
                response = requests.get(url)

                if response.status_code == 200:
                    data = response.json()
                    version =  data['tag_name']
                    name =  data['name']
                else:
                    return 0, str(response.content)

                #sudo mv filename /usr/bin/
                command = 'wget -P /home/rustic https://github.com/rustic-rs/rustic/releases/download/%s/rustic-%s-x86_64-unknown-linux-musl.tar.gz' %(version, version)
                ProcessUtilities.executioner(command)

                command = 'tar xzf /home/rustic/rustic-%s-x86_64-unknown-linux-musl.tar.gz -C /home/rustic//'%(version)
                ProcessUtilities.executioner(command)

                command = 'sudo mv /home/rustic/rustic /usr/bin/'
                ProcessUtilities.executioner(command)

                command = 'rm -rf /home/rustic'
                ProcessUtilities.executioner(command)

            return 1, None



        except BaseException as msg:
            print('Error: %s'%msg)
            return 0, str(msg)

if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(description='CyberPanel Backup Generator')
        parser.add_argument('function', help='Specify a function to call!')
        parser.add_argument('--path', help='')

        args = parser.parse_args()

        if args.function == "BackupDataBases":
            cpbuv2 = CPBackupsV2({'finalPath': args.path})
            #cpbuv2.BackupDataBases()

    except:
        cpbuv2 = CPBackupsV2({'domain': 'cyberpanel.net', 'BasePath': '/home/backup', 'BackupDatabase': 1, 'BackupData': 1, 'BackupEmails': 1} )
        cpbuv2.InitiateBackup()
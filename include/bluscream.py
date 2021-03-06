from datetime import datetime
from PythonQt import BoolResult
from PythonQt.QtGui import QInputDialog, QMessageBox, QDialog
from PythonQt.QtCore import Qt, QFile, QByteArray, QIODevice, QDataStream
from PythonQt.QtSql import QSqlQuery
from PythonQt.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from ts3plugin import PluginHost
# from configparser import ConfigParser
from urllib.parse import quote_plus
import ts3lib, ts3defines, os.path, string, random, ts3client, time

# GENERAL FUNCTIONS #
def timestamp(): return '[{:%Y-%m-%d %H:%M:%S}] '.format(datetime.now())
def date(): return '{:%Y-%m-%d}'.format(datetime.now())
def Time(): return '{:%H:%M:%S}'.format(datetime.now())

def varname(obj, callingLocals=locals()):
    for k, v in list(callingLocals.items()):
         if v is obj: return k

def random_string(size=1, chars=string.ascii_uppercase + string.ascii_lowercase + string.digits):
    return ''.join(random.SystemRandom().choice(chars) for _ in range(size))

def percentage(part, whole):
    return round(100 * float(part)/float(whole))

def getItems(object):
    return [(a, getattr(object, a)) for a in dir(object)
            if not a.startswith('__') and not callable(getattr(object, a)) and not "ENDMARKER" in a and not "DUMMY" in a]

def getItemTime(lst):
    if lst in [ts3defines.VirtualServerProperties, ts3defines.VirtualServerPropertiesRare]:
        return ts3defines.PluginItemType.PLUGIN_SERVER, "Server"
    elif lst in [ts3defines.ChannelProperties, ts3defines.ChannelPropertiesRare]:
        return ts3defines.PluginItemType.PLUGIN_CHANNEL, "Channel"
    elif lst in [ts3defines.ConnectionProperties, ts3defines.ConnectionPropertiesRare, ts3defines.ClientProperties, ts3defines.ClientPropertiesRare]:
        return ts3defines.PluginItemType.PLUGIN_CLIENT, "Client"
    else: return None

def find_between(s, first, last):
    try:
        start = s.index( first ) + len( first )
        end = s.index( last, start )
        return s[start:end]
    except ValueError:
        return ""

def find_between_r(s, first, last):
    try:
        start = s.rindex( first ) + len( first )
        end = s.rindex( last, start )
        return s[start:end]
    except ValueError:
        return ""

# PARSING #
def channelURL(schid=None, cid=0, name=None):
    if schid is None:
        try: schid = ts3lib.getCurrentServerConnectionHandlerID()
        except: pass
    if name is None:
        try: (error, name) = ts3lib.getChannelVariable(schid, cid, ts3defines.ChannelProperties.CHANNEL_NAME)
        except: name = cid
    return '[b][url=channelid://{0}]"{1}"[/url][/b]'.format(cid, name)

def clientURL(schid=0, clid=0, uid="", nickname="", nickname_encoded=""):
    if not schid:
        try: schid = ts3lib.getCurrentServerConnectionHandlerID()
        except: pass
    if not uid:
        try: (error, uid) = ts3lib.getClientVariable(schid, clid, ts3defines.ClientProperties.CLIENT_UNIQUE_IDENTIFIER)
        except: pass
    if not nickname:
        try: (error, nickname) = ts3lib.getClientVariable(schid, clid, ts3defines.ClientProperties.CLIENT_NICKNAME)
        except: nickname = uid
    if not nickname_encoded:
        try: nickname_encoded = quote_plus(nickname)
        except: nickname_encoded = uid
    return '[url=client://{0}/{1}~{2}]"{3}"[/url]'.format(clid, uid, nickname_encoded, nickname)

# I/O #
def loadCfg(path, cfg):
    if not os.path.isfile(path) or os.path.getsize(path) < 1:
        saveCfg(path, cfg)
    cfg = cfg.read(path)

def saveCfg(path, cfg):
    with open(path, 'w') as cfgfile:
        cfg.write(cfgfile)
# GUI #
def inputBox(title, text):
    x = QDialog()
    x.setAttribute(Qt.WA_DeleteOnClose)
    (text, ok) = QInputDialog.getText(x, title, text)
    if ok: return text
    else: return False

def inputInt(title="", label="", val=0, min=-2147483647, max=2147483647, step=1):
    x = QDialog()
    x.setAttribute(Qt.WA_DeleteOnClose)
    ok = BoolResult()
    i = QInputDialog.getInt(x, title, label, val, min, max, step, ok)
    if ok: return i
    else: return False

def msgBox(text, icon=QMessageBox.Information, title=""):
    x = QMessageBox()
    if title: x.setWindowTitle(title)
    x.setText(text)
    x.setIcon(icon)
    x.exec()

def confirm(title, message):
    x = QDialog()
    x.setAttribute(Qt.WA_DeleteOnClose)
    _x = QMessageBox.question(x, title, message, QMessageBox.Yes, QMessageBox.No)
    if _x == QMessageBox.Yes: return True if _x == QMessageBox.Yes else False

# AntiFlood
def getAntiFloodSettings(schid):
    (err, cmdblock) = ts3lib.getServerVariable(schid, ts3defines.VirtualServerPropertiesRare.VIRTUALSERVER_ANTIFLOOD_POINTS_NEEDED_COMMAND_BLOCK)
    (err, ipblock) = ts3lib.getServerVariable(schid, ts3defines.VirtualServerPropertiesRare.VIRTUALSERVER_ANTIFLOOD_POINTS_NEEDED_IP_BLOCK)
    (err, afreduce) = ts3lib.getServerVariable(schid, ts3defines.VirtualServerPropertiesRare.VIRTUALSERVER_ANTIFLOOD_POINTS_TICK_REDUCE)
    return (err, cmdblock, ipblock, afreduce)

def calculateInterval(schid, command, name="pyTSon"):
    # ts3lib.requestServerVariables(schid)
    (err, cmdblock, ipblock, afreduce) = getAntiFloodSettings(schid)
    # strange = False
    # for var in [cmdblock, ipblock, afreduce]:
        # if not var or var < 0 or var == "": strange = True
    # if err != ts3defines.ERROR_ok or strange:
        # ts3lib.requestServerVariables(schid)
        # (err, cmdblock, ipblock, afreduce) = getAntiFloodSettings(schid)
    interval = round(1000/((afreduce/command)))
    ts3lib.logMessage("{}: schid = {} | err = {} | afreduce = {} | cmdblock = {} | ipblock = {} | points_per_{} = {} |interval = {}".format(name, schid, err, afreduce, cmdblock, ipblock, varname(command), command, interval), ts3defines.LogLevel.LogLevel_INFO, "pyTSon", 0)
    return interval

# Network #
def getFile(url):
    nwmc = QNetworkAccessManager()
    nwmc.connect("finished(QNetworkReply*)", getFile)
    nwmc.get(QNetworkRequest(QUrl(url)))
def getFileReply(reply):
    del nwmc


def downloadFile(url, path):
    nwmc = QNetworkAccessManager()
    nwmc.connect("finished(QNetworkReply*)", downloadFileReply)
    dlpath = path
    nwmc.get(QNetworkRequest(QUrl(url)))
def downloadFileReply(reply):
    del nwmc
    """
    QByteArray b = reply->readAll();
    fil = QFile(dlpath);
    fil.open(QIODevice.WriteOnly);
    out QDataStream(fil);
    out << b;
    """

# Stuff #
def hasAddon():
    pass

# Database #
def getAddons():
    db = ts3client.Config()
    q = db.query("SELECT * FROM addons")
    ret = {}
    while q.next():
        try:
            key = q.value("key")
            ret[key] = {"timestamp": q.value("timestamp")}
            val = q.value("value")
            for l in val.split('\n'):
                l = l.split('=', 1)
                ret[key][l[0]] = l[1]
        except: from traceback import format_exc;ts3lib.logMessage(format_exc(), ts3defines.LogLevel.LogLevel_ERROR, "pyTSon", 0);continue
    return ret

def getContacts():
    db = ts3client.Config()
    ret = []
    q = db.query("SELECT * FROM contacts")
    while q.next():
        try:
            cur = {"Key": int(q.value("key")), "Timestamp": q.value("timestamp")}
            val = q.value("value")
            for l in val.split('\n'):
                try:
                    l = l.split('=', 1)
                    if len(l) != 2: continue
                    if l[0] in ["Nickname","PhoneticNickname","LastSeenServerName"]: cur[l[0]] = l[1].encode('ascii', 'ignore')
                    elif l[0] in ["LastSeenServerAddress","IDS","VolumeModifier", "LastSeen"]: cur[l[0]] = l[1]
                    elif l[0] in ["Friend","NickShowType"]: cur[l[0]] = int(l[1])
                    elif l[0] in ["Automute","IgnorePublicMessages","IgnorePrivateMessages","IgnorePokes","IgnoreAvatar","IgnoreAwayMessage","HaveVolumeModifier","WhisperAllow"]:
                        if l[1] == "false": cur[l[0]] = False
                        elif l[1] == "true": cur[l[0]] = True
                    if l[0] == "LastSeen" and l[1]: cur["LastSeenEpoch"] = int(time.mktime(time.strptime(l[1], '%Y-%m-%dT%H:%M:%S')))
                except: continue
            ret.append(cur)
        except: continue
    del db
    return ret

def getContactStatus(uid):
    db = ts3client.Config()
    q = db.query("SELECT * FROM contacts WHERE value LIKE '%%IDS=%s%%'" % uid)
    ret = 2
    if q.next():
        val = q.value("value")
        for l in val.split('\n'):
            if l.startswith('Friend='):
                ret = int(l[-1])
    del db
    return ret

class ContactStatus(object):
    FRIEND = 0
    BLOCKED = 1
    NEUTRAL = 2

# TS3Hook #
def parseCommand(cmd):
    pass

def buildCommand(cmd, parameters):
    for key, value in parameters:
        if key.startswith('-') or not value:
            cmd += " {}".format(key)
        else: cmd += " {}={}".format(key[0], key[1])
    return cmd


def loadBadges():
    db = ts3client.Config()
    q = db.query("SELECT * FROM Badges") #  WHERE key = BadgesListData
    timestamp = 0
    ret = {}
    badges = b''
    while q.next():
        key = q.value("key")
        if key == "BadgesListTimestamp":
            timestamp = q.value("value")
        elif key == "BadgesListData":
            badges = q.value("value")
            next = 12
            guid_len = 0;guid = ""
            name_len = 0;name = ""
            url_len = 0;url = ""
            filename = ""
            desc_len = 0;desc = ""
            try:
                for i in range(0, badges.size()):
                    if i == next: #guid_len
                        guid_len = int(badges.at(i))
                        guid = str(badges.mid(i+1, guid_len))
                    elif i == (next + 1 + guid_len + 1):
                        name_len = int(badges.at(i))
                        name = str(badges.mid(i+1, name_len))
                    elif i == (next + 1 + guid_len + 1 + name_len + 2):
                        url_len = int(badges.at(i))
                        url = str(badges.mid(i+1, url_len))
                        filename = url.rsplit('/', 1)[1]
                    elif i == (next + 1 + guid_len + 1 + name_len + 2 + url_len + 2):
                        desc_len = int(badges.at(i))
                        desc = str(badges.mid(i+1, desc_len))
                        ret[guid] = {"name": name, "url": url, "filename": filename, "description": desc}
                        next = (next + guid_len + 2 + name_len + 2 + url_len + 2 + desc_len + 13)
                delimiter = badges.mid(0, 12)
            except: from traceback import format_exc; ts3lib.logMessage(format_exc(), ts3defines.LogLevel.LogLevel_ERROR, "pyTSon", 0)
    del db
    return timestamp, ret, badges

def parseBadges(client_badges):
    overwolf = None
    badges = []
    if "verwolf=" in client_badges and "badges=" in client_badges:
        client_badges = client_badges.split(":",1)
        overwolf = bool(int(client_badges[0].split("=",1)[1]))
        badges = client_badges[1].split("=",1)[1].replace(":badges=", ",").split(",")
    elif "verwolf=" in client_badges:
        overwolf = bool(int(client_badges.split("=")[1]))
    elif "badges=" in client_badges:
        badges = client_badges.split("=",1)[1].replace(":badges=", ",").split(",")
    return (overwolf, badges)

def buildBadges(badges=[], overwolf=False):
    blocks = [",".join(badges[i:i+3]) for i in range(0, len(badges), 3)]
    return "clientupdate client_badges=overwolf={}:badges={}".format(1 if overwolf else 0, ":badges=".join(blocks))

def sendCommand(name, cmd, schid=0):
    if PluginHost.cfg.getboolean("general", "verbose"):
        ts3lib.printMessage(ts3lib.getCurrentServerConnectionHandlerID(), '{timestamp} [color=orange]{name}[/color]:[color=white] {message}'.format(timestamp=timestamp(), name=name, message=cmd), ts3defines.PluginMessageTarget.PLUGIN_MESSAGE_TARGET_SERVER)
    cmd = cmd.replace(" ", "~s")
    if schid == 0: schid = ts3lib.getCurrentServerConnectionHandlerID()
    ts3lib.requestSendServerTextMsg(schid, "~cmd{}".format(cmd))

# DEFINES #

dlpath = ""

class AntiFloodPoints(object):
    AUTH = 0
    BANADD = 25
    BANCLIENT = 25
    BANDEL = 5
    BANDELALL = 5
    BANLIST = 25
    BINDINGLIST = 0
    CHANNELADDPERM = 5
    CHANNELCLIENTADDPERM = 5
    CHANNELCLIENTDELPERM = 5
    CHANNELCLIENTLIST = 0
    CHANNELCLIENTPERMLIST = 5
    CHANNELCONNECTINFO = 0
    CHANNELCREATE = 25
    CHANNELCREATEPRIVATE = 25
    CHANNELDELETE = 25
    CHANNELDELPERM = 5
    CHANNELEDIT = 25
    CHANNELFIND = 0
    CHANNELGETDESCRIPTION = 0
    CHANNELGROUPADD = 5
    CHANNELGROUPADDPERM = 5
    CHANNELGROUPCLIENTLIST = 5
    CHANNELGROUPCOPY = 5
    CHANNELGROUPDEL = 5
    CHANNELGROUPDELPERM = 5
    CHANNELGROUPLIST = 5
    CHANNELGROUPPERMLIST = 5
    CHANNELGROUPRENAME = 5
    CHANNELINFO = 0
    CHANNELLIST = 0
    CHANNELMOVE = 25
    CHANNELPERMLIST = 5
    CHANNELSUBSCRIBE = 15
    CHANNELSUBSCRIBEALL = 20
    CHANNELUNSUBSCRIBE = 5
    CHANNELUNSUBSCRIBEALL = 25
    CHANNELVARIABLE = 0
    CLIENTADDPERM = 5
    CLIENTCHATCLOSED = 5
    CLIENTCHATCOMPOSING = 0
    CLIENTDBDELETE = 25
    CLIENTDBEDIT = 25
    CLIENTDBFIND = 50
    CLIENTDBINFO = 0
    CLIENTDBLIST = 25
    CLIENTDELPERM = 5
    CLIENTDISCONNECT = 0
    CLIENTEDIT = 25
    CLIENTFIND = 0
    CLIENTGETDBIDFROMUID = 5
    CLIENTGETIDS = 5
    CLIENTGETNAMEFROMDBID = 5
    CLIENTGETNAMEFROMUID = 5
    CLIENTGETUIDFROMCLID = 5
    CLIENTGETVARIABLES = 0
    CLIENTINFO = 0
    CLIENTINIT = 0
    CLIENTINITIV = 0
    CLIENTKICK = 25
    CLIENTLIST = 0
    CLIENTMOVE = 10
    CLIENTMUTE = 10
    CLIENTNOTIFYREGISTER = 0
    CLIENTNOTIFYUNREGISTER = 0
    CLIENTPERMLIST = 5
    CLIENTPOKE = 25
    CLIENTSETSERVERQUERYLOGIN = 25
    CLIENTSITEREPORT = 0
    CLIENTUNMUTE = 10
    CLIENTUPDATE = 15
    CLIENTVARIABLE = 0
    COMPLAINADD = 25
    COMPLAINDEL = 5
    COMPLAINDELALL = 25
    COMPLAINLIST = 25
    CONNECTIONINFOAUTOUPDATE = 0
    CURRENTSCHANDLERID = 0
    CUSTOMINFO = 0
    CUSTOMSEARCH = 50
    DUMMY_CONNECTFAILED = 0
    DUMMY_CONNECTIONLOST = 0
    DUMMY_NEWIP = 0
    FTCREATEDIR = 5
    FTDELETEFILE = 5
    FTGETFILEINFO = 5
    FTGETFILELIST = 0
    FTINITDOWNLOAD = 0
    FTINITUPLOAD = 0
    FTLIST = 5
    FTRENAMEFILE = 5
    FTSTOP = 5
    GETCONNECTIONINFO = 0
    GM = 50
    HASHPASSWORD = 0
    HELP = 0
    INSTANCEEDIT = 25
    INSTANCEINFO = 0
    LOGADD = 0
    LOGIN = 0
    LOGOUT = 0
    LOGVIEW = 50
    MESSAGEADD = 25
    MESSAGEDEL = 5
    MESSAGEGET = 20
    MESSAGELIST = 25
    MESSAGEUPDATEFLAG = 5
    PERMFIND = 0
    PERMGET = 0
    PERMIDGETBYNAME = 0
    PERMISSIONLIST = 5
    PERMOVERVIEW = 5
    PERMRESET = 0
    PLUGINCMD = 5
    PRIVILEGEKEYADD = 0
    PRIVILEGEKEYDELETE = 0
    PRIVILEGEKEYLIST = 0
    PRIVILEGEKEYUSE = 0
    QUIT = 0
    SERVERCONNECTINFO = 0
    SERVERCONNECTIONHANDLERLIST = 0
    SERVERCREATE = 0
    SERVERDELETE = 0
    SERVEREDIT = 5
    SERVERGETVARIABLES = 0
    SERVERGROUPADD = 5
    SERVERGROUPADDCLIENT = 25
    SERVERGROUPADDPERM = 5
    SERVERGROUPAUTOADDPERM = 0
    SERVERGROUPAUTODELPERM = 0
    SERVERGROUPCLIENTLIST = 5
    SERVERGROUPCOPY = 5
    SERVERGROUPDEL = 5
    SERVERGROUPDELCLIENT = 25
    SERVERGROUPDELPERM = 5
    SERVERGROUPLIST = 5
    SERVERGROUPPERMLIST = 5
    SERVERGROUPRENAME = 5
    SERVERGROUPSBYCLIENTID = 5
    SERVERIDGETBYPORT = 0
    SERVERINFO = 0
    SERVERLIST = 0
    SERVERNOTIFYREGISTER = 0
    SERVERNOTIFYUNREGISTER = 0
    SERVERPROCESSSTOP = 0
    SERVERQUERYCMD = 5
    SERVERREQUESTCONNECTIONINFO  = 0
    SERVERSNAPSHOTCREATE = 0
    SERVERSNAPSHOTDEPLOY = 0
    SERVERSTART = 0
    SERVERSTOP = 0
    SERVERTEMPPASSWORDADD = 5
    SERVERTEMPPASSWORDDEL = 5
    SERVERTEMPPASSWORDLIST = 5
    SERVERVARIABLE = 0
    SETCLIENTCHANNELGROUP = 25
    SETCONNECTIONINFO = 0
    SETWHISPERLIST = 0
    TEXTMESSAGESEND = 15
    TOKENADD = 5
    TOKENDELETE = 5
    TOKENLIST = 5
    TOKENUSE = 5
    USE = 0
    VERIFYCHANNELPASSWORD = 5
    VERIFYSERVERPASSWORD = 5
    VERSION = 0
    WHOAMI = 0

class GroupType(object):
    TEMPLATE = 0
    REGULAR = 1


"""
    def log(self, logLevel, message, schid=0):
        ts3lib.logMessage(message, logLevel, self.name, schid)
        if logLevel in [ts3defines.LogLevel.LogLevel_DEBUG, ts3defines.LogLevel.LogLevel_DEVEL] and self.debug:
            ts3lib.printMessage(schid if schid else ts3lib.getCurrentServerConnectionHandlerID(), '{timestamp} [color=orange]{name}[/color]: {message}'.format(timestamp=self.timestamp(), name=self.name, message=message), ts3defines.PluginMessageTarget.PLUGIN_MESSAGE_TARGET_SERVER)

"""
import glob, json, struct, datetime as dt
from os.path import join, dirname, isdir
from pathlib import Path

class CRDBException(Exception):
    message = ""
    fmt = ""
    data = {}

    def __init__(self, message, format, data):
        self.message = message
        self.fmt = format
        self.data = data

    def getMessage(self):
        return self.message

    def getFormat(self):
        return self.fmt

    def getData(self):
        return self.data

    def printDebug(self):
        print("Error:", self.message)
        print(" ======== DEBUG ======== ")
        print(" + Format: ", self.fmt)
        print(" + Data:", self.data)
        print(" ======================= ")

def resize(ba, size):
    if len(ba) > size:
        del ba[size:]
    else:
        ba += b'\0' * (size - len(ba))

def isnumber(i):
    return isinstance(i, (int, float, complex)) and not isinstance(i, bool)

def makeEntry(fieldMap, data):
    packedData = []

    for field, ftype in fieldMap.items():
        if ftype == "string":
            if field not in data:
                packedData.append(bytes("", "ascii")) # Default: ""
            else:
                packedData.append(bytes(data[field], "ascii"))
        elif ftype == "int":
            if field not in data:
                packedData.append(0) # Default: 0
            elif (isnumber(data[field])):
                packedData.append(data[field]) # Number
            else:
                packedData.append(int(data[field], 16)) # Strings in int fields are expected to be hex
        elif ftype.startswith("bin:"):
            binlen = ftype[4:]
            bytelen = int(binlen)
            if field not in data:
                for x in range(bytelen):
                    packedData.append(bytes([0])) # Default: 0
            else:
                if isinstance(data[field], str):
                    bytedata = bytes.fromhex(data[field]) # Strings in bin fields are expected to be hex
                elif isinstance(data[field], list):
                    bytedata = bytes(data[field])
                else:
                    raise TypeError

                for i in range(bytelen):
                    if i < len(bytedata):
                        if (isnumber(bytedata[i])):
                            packedData.append(bytedata[i])
                        else:
                            packedData.append(int(bytedata[i], 16)) # Strings in bin fields are expected to be hex
                    else:
                        packedData.append(bytes([0])) # Default: 0
        else:
            raise KeyError("Error [Field: ", field, "]: Unknown type `", ftype, "`.")

    return packedData

class CRDBCore:
    __file = ""
    __crdb = {}
    __entry_size = 100

    def __init__(self, crdb, filePath):
        self.__file = filePath
        self.__crdb = crdb

        with open(self.__file) as f:
            data = json.load(f)
            self.__outfile = data['outfile']
            self.__system = data['system']
            self.__confkey = data['pio']
            self.__type = data['type']
            self.__format = data['formats']['python']
            self.__format_string = data['formats']['crdb']
            self.__fields = data['order']
            self.__records = data['records']
            self.__header_format = self.__crdb.headerFormat
            self.__version = self.__crdb.version
            self.__date = self.__crdb.date

            del data

        self.__format_size = struct.calcsize(self.__format)

        if self.__format_size < 100:
            self.__entry_size = 100
        else:
            self.__entry_size = self.__format_size

    @property
    def system(self):
        return self.__system

    @property
    def records(self):
        return self.__records

    @property
    def count(self):
        return len(self.__records)

    def getRecord(self, i):
        return self.__records[i]

    @property
    def identifier(self):
        return self.__type + "/" + self.__system

    @property
    def identBytes(self):
        return bytes(self.identifier, "ascii")

    @property
    def entryStruct(self):
        return self.__format

    @property
    def entrySize(self):
        return self.__entry_size

    @property
    def headerStruct(self):
        return self.__header_format

    @property
    def formatString(self):
        return self.__format_string

    @property
    def formatBytes(self):
        return bytes(self.__format_string, "ascii")

    @property
    def outfile(self):
        return self.__outfile + ".crdb"

    @property
    def confKey(self):
        return self.__confkey

    def build(self):
        buff = bytearray()

        resize(buff, self.entrySize)
        struct.pack_into(self.__header_format, buff, 0, 0xDA705C12, self.__version, self.identBytes, self.__date, self.entrySize, self.formatBytes)

        position = self.entrySize

        for entry in self.__records:
            resize(buff, position + self.__entry_size)

            data = makeEntry(self.__fields, entry)

            try:
                struct.pack_into(self.entryStruct, buff, position, *data)
            except Exception as exc:
                raise CRDBException("[{system}:{entry}] {message}".format(entry = int(position/self.__entry_size) - 1, system = self.__system, position=position, message=exc), format=self.entryStruct, data=data) from exc

            position = position + self.__entry_size

        return buff


class CRDB:
    __dir = ""
    __manifest_file = ""
    __manifest = {}
    __coreKeys = []
    __coreFiles = {}
    __cores = {}
    __version = 0
    __date = int(dt.datetime.now().strftime("%Y%m%d"), 16)

    def __init__(self, crdb_dir):
        self.__dir = crdb_dir
        self.__manifest_file = join(self.__dir, ".crdb.json")

        with open(self.__manifest_file) as f:
            self.__manifest = json.load(f)
            self.__header_format = self.__manifest['header']['python']
            self.__version = self.__manifest['version']
            self.__make_index()

    def __make_index(self):
        if not isdir(self.__dir):
            return False

        coreFiles = glob.glob(join(self.__dir, "*.json"))

        for coreFile in coreFiles:
            baseName = Path(coreFile).stem
            self.__coreKeys.append(baseName)
            self.__coreFiles[baseName] = coreFile

        return True

    @property
    def src(self):
        return self.__manifest_file

    @property
    def manifest(self):
        return self.__manifest

    @property
    def path(self):
        return self.__dir

    @property
    def headerFormat(self):
        return self.__header_format;

    @property
    def cores(self):
        return self.__coreKeys

    @property
    def version(self):
        return self.__version

    @property
    def date(self):
        return self.__date

    def getCore(self, coreName):
        if coreName in self.__cores:
            return self.__cores[coreName]

        if coreName not in self.__coreFiles:
            return False

        self.__cores[coreName] = CRDBCore(self, self.__coreFiles[coreName])

        return self.__cores[coreName]

    def getCoreKey(self, coreName):
        return self.__cores[coreName].key

    def getCoreFile(self, coreName):
        return join(self.__data_dir, coreName)

    def BuildCRDB(self, coreName, target):
        buff = self.getCore(coreName).build()

        Path(dirname(target)).mkdir(parents=True, exist_ok=True)

        with open(target, 'wb') as fw:
            fw.write(buff)

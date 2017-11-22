#! python3
"""library for data mining in AGC files for Protect RCS"""

import functools
import re
import unittest

import jeep # custom library

class AgcException(Exception):
  pass

class AgcObjException(Exception):
  """Exception raised when an object name is not found in dictionary"""
  pass

class AgcAttrException(Exception):
  """Exception raised when an object attribute name is not found in dictionary"""
  pass

# regular expression catching a gCAU configuration line in an .agc file
#  captures: object, attribute, value
RE_COMPILED_CFG_ITEM = re.compile(r"^([A-Z][A-Z0-9_]*)\.(!?\w+)\s*=\s*\"(.*)\"\s*$")
RE_COMPILED_CFG_START = re.compile(r"^\$GCAUConfigurationData\s*=\s*\"Start\"\s*$")
RE_COMPILED_CFG_END = re.compile(r"^\$GCAUConfigurationData\s*=\s*\"End\"\s*$")

def makeGcauCfgDictFromAgc(lineList):
  """extraction of the gCAU configuration part of an .agc file
make dictionary of dictionaries based on 'lineList'
from file.readlines() of an .agc
 structure of dictionay:
  {objectName:{attributeName: value, ...}, ...}"""  
  diction = {}
  withinCfgData = False
  for eachString in lineList:
    if re.match(RE_COMPILED_CFG_START, eachString):
      withinCfgData = True
    elif re.match(RE_COMPILED_CFG_END, eachString):
      withinCfgData = False
    elif withinCfgData:
      p = re.match(RE_COMPILED_CFG_ITEM, eachString)
      if p:
        obj = p.groups()[0]
        attr = p.groups()[1]
        val = p.groups()[2]
        if obj not in diction:
          diction[obj] = {}
        diction[obj][attr] = val
  return diction

def makeGcauCfgStructureListFromAgc(lineList):
  """extraction of the gCAU configuration part of an .agc file
make structural list of configuration based on 'lineList'
from file.readlines() of an .agc
 structure: [(objectName, [attributeName, ...]), ...]"""
  structuralList = []
  currentObj = "!!!none!!!"
  withinCfgData = False
  for eachString in lineList:
    if re.match(RE_COMPILED_CFG_START, eachString):
      withinCfgData = True
    elif re.match(RE_COMPILED_CFG_END, eachString):
      withinCfgData = False
    elif withinCfgData:
      p = re.match(RE_COMPILED_CFG_ITEM, eachString)
      if p:
        obj = p.groups()[0]
        attr = p.groups()[1]
        if currentObj != obj:
          currentObj = obj
          structuralList.append((currentObj, [attr]))
        else:
          structuralList[len(structuralList)-1][1].append(attr)
  return structuralList

def makeListOfEnabledEvents(gcauCfgDict):
  """make list of events which are enabled in SYSVAR
elements of this list are one-based
 parameter gcauCfgDict: dictionary of gCAU configuration
  as made by makeGcauCfgDictFromAgc"""
  OBJ_NAME = "SYSVAR"
  OBJ_ATTR = "EventEnable"
  list = []
  try:
    obj = gcauCfgDict[OBJ_NAME]
    try:
      mask = int(obj[OBJ_ATTR], 16)
    except KeyError:
      raise AgcAttrException("{0} misses: {1}"\
                             .format(jeep.defGetMyName(), OBJ_ATTR))
    else:
      n = 1
      while mask != 0:
        if mask % 2:
          list.append(n)
        mask = mask >> 1
        n = n + 1 
  except KeyError:
    raise AgcObjException("{0} mises: {1}"\
                          .format(jeep.defGetMyName(), OBJ_NAME))
  return list

def makeGcauAGCLineFromDict(dictio, objectName, attributeName):
  """look into a dictionary such as made by makeGcauCfgDictFromAgc
and make the corresponding AGC line as a string,
given an objectName and attributeName
string is ended with a line feed character"""
  if objectName not in dictio:
    raise AgcObjException(\
      "{0}: \"{1}\" object not found".format(jeep.defGetMyName(), objectName))
  if attributeName not in dictio[objectName]:
    raise AgcAttrException(\
      "{0}: \"{2}\" attribute not found in \"{1}\""\
      .format(jeep.defGetMyName(), objectName, attributeName))
  string = "{0}.{1} = \"{2}\"\n"\
           .format(objectName, attributeName, dictio[objectName][attributeName])
  return string

def updateAgcLineListWithDict(agcLineList, agcDictionary, bCompleteness=False):
  '''updates an agcLineList such as build by file.readlines()
with entries (object/attribute) defined in agcDictionary
such as build by makeGcauCfgDictFromAgc
when done, updated agcLineList can be directly updated with file.writelines()
method: traverse all lines of agcLineList and queries agcDictionary for data
 bCompleteness: if True, a key not found in agcDictionary will raise an error,
                either AgcObjException or AgcAttrException'''
  withinCfgData = False
  for (index, agcLine) in enumerate(agcLineList):
    if re.match(RE_COMPILED_CFG_START, agcLine):
      withinCfgData = True
    elif re.match(RE_COMPILED_CFG_END, agcLine):
      withinCfgData = False
    elif withinCfgData:
      p = re.match(RE_COMPILED_CFG_ITEM, agcLine)
      if p:
        objName = p.groups()[0]
        attrName = p.groups()[1]
        try:
          agcLineList[index] = makeGcauAGCLineFromDict(agcDictionary, objName, attrName)
        except (AgcObjException, AgcAttrException) as e:
          if bCompleteness:
            raise e
              
  
# Unit Tests

AGC_SAMPLE = r'''
$GCAUConfigurationData = "Start"

SYSVAR.SuperUserMenus = "2007"
SYSVAR.EventEnable = "A508A07E7"

BATTSEL.BatteryType = "0"
BATTSEL.NumberOfElements = "1"
BATTSEL.Capacity = "1"
BATTSEL.Efficiency = "99"
BATTSEL.FanDelay = "0"

COMMISS.Duration = "0"
COMMISS.RelayNb = "0"
COMMISS.NumberOfRelays = "1"
COMMISS.LedNb = "0"

EVT_1.Function = "AL"
EVT_1.LCDLatch = "1"
EVT_1.RelayLatch = "0"
EVT_1.Shutdown = "0"
EVT_1.CommonAlarm = "1"
EVT_1.RelayNumber = "0"
EVT_1.NumberOfRelays = "1"
EVT_1.LedNumber = "0"
EVT_1.Delay = "4"
EVT_1.Value = "2530"
EVT_1.!Text = "HIGH MAINS VOLTS"
EVT_1.!LocalText = "U MAX RESEAU"

$GCAUConfigurationData= "End"

CALIBR.!BatteryVoltage = "1024"
CALIBR.!BatteryChargeCurrent = "1024"
CALIBR.!BatteryDischargeCurrent = "1024"
CALIBR.!ChargeCurrent = "1024"
CALIBR.!EarthFault = "1024"
CALIBR.!ChargerVoltage = "1024"
CALIBR.!MainsVoltage = "1024"
CALIBR.!BatteryTemperature = "1024"
CALIBR.!AmbientTemperature = "1024"
CALIBR.!SpareAnalogue = "1024"'''

class TestAgc(unittest.TestCase):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.agcLineList = AGC_SAMPLE.split("\n")
    for c in range(len(self.agcLineList)):
      if c % 4 == 0:
        self.agcLineList[c] += "\n"
      if c % 4 == 1:
        self.agcLineList[c] += "\r\n"
      if c % 4 == 2:
        self.agcLineList[c] += "\r"
  def test_makeGcauCfgDictFromAgc(self):
    TRUE = self.assertTrue
    agcDict = makeGcauCfgDictFromAgc(self.agcLineList)
    TRUE(len(agcDict)==4)
    TRUE(agcDict["EVT_1"]["CommonAlarm"] == "1")
    TRUE(agcDict["EVT_1"]["!LocalText"] == "U MAX RESEAU")
    TRUE(agcDict["SYSVAR"]["SuperUserMenus"] == "2007")
    with self.assertRaises(KeyError):
      agcDict["CALIBR"]
  def test_makeGcauCfgStructureListFromAgc(self):
    TRUE = self.assertTrue
    agcStruct=makeGcauCfgStructureListFromAgc(self.agcLineList)
    TRUE(len(agcStruct)==4)
    TRUE(agcStruct[1][0]=="BATTSEL" and agcStruct[1][1][2]=="Capacity" and len(agcStruct[1][1])==5)
    TRUE(agcStruct[3][0]=="EVT_1" and len(agcStruct[3][1])==12 and \
         agcStruct[3][1][0]=="Function" and agcStruct[3][1][10]=="!Text")
  def test_makeListOfEnabledEvents(self):
    TRUE = self.assertTrue
    evtEnabledList=makeListOfEnabledEvents(makeGcauCfgDictFromAgc(self.agcLineList))
    TRUE(evtEnabledList, [1, 2, 3, 6, 7, 8, 7, 10, 11, 18, 20, 24, 29, 31, 34, 36])
  def test_makeGcauAGCLineFromDict(self):
    TRUE = self.assertTrue
    agcDict = makeGcauCfgDictFromAgc(self.agcLineList)
    DUT = functools.partial(makeGcauAGCLineFromDict, agcDict) # Def Under Test
    TRUE(DUT("BATTSEL", "Efficiency") == "BATTSEL.Efficiency = \"99\"\n")
    TRUE(DUT("EVT_1", "Value") == "EVT_1.Value = \"2530\"\n")
    with self.assertRaises(AgcObjException):
      DUT("WEIRD_OBJECT_12XU", "Value")
    with self.assertRaises(AgcAttrException):
      DUT("EVT_1", "WeirdAttribute12xu")
  def test_updateAgcLineListWithDict(self):
    TRUE = self.assertTrue
    FAIL = self.fail
    agcLineListTest = list(self.agcLineList)
    agcDict = makeGcauCfgDictFromAgc(self.agcLineList)
    DUT = functools.partial(updateAgcLineListWithDict, agcLineListTest, agcDict) # Def Under Test
    agcDict["COMMISS"]["RelayNb"] = str(32)
    agcDict["COMMISS"]["NumberOfRelays"] = str(4)
    DUT(True) # True means bCompleteness parameter is True
    for (targetIndex, lineText) in enumerate(agcLineListTest):
      if lineText.find("COMMISS.RelayNb") == 0:
        break # found where above token found, targetIndex (zero-based indexes it)
    TRUE(agcLineListTest[targetIndex] == "COMMISS.RelayNb = \"32\"\n")
    TRUE(agcLineListTest[targetIndex+1] == "COMMISS.NumberOfRelays = \"4\"\n")
    del agcDict["COMMISS"]["NumberOfRelays"]
    with self.assertRaises(AgcAttrException):
      DUT(True)
    del agcDict["BATTSEL"]
    with self.assertRaises(AgcObjException):
      DUT(True)
    try:
      # relaxed update: should run find even with missing entries in dictionary
      DUT(False)
    except Exception as e:
      FAIL("{0} unexpectely raised exception \"{1}\"!".format("", e))
    
if __name__ == "__main__":
    unittest.main()

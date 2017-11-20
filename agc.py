#! python3
"""library for data mining in AGC files for Protect RCS"""

import re
import unittest

class AgcException(Exception):
  pass

class AgcObjException(Exception):
  pass

class AgcAttrException(Exception):
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
 structure: {objectName:{attributeName: value, ...}, ...}"""  
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
          diction[obj]={}
        diction[obj][attr]=val
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
      raise AgcAttrException("makeListOfEnabledEvents misses: " + OBJ_ATTR)
    else:
      n = 1
      while mask != 0:
        if mask % 2:
          list.append(n)
        mask = mask >> 1
        n = n + 1 
  except KeyError:
    raise AgcObjException("makeListOfEnabledEvents mises: " + OBJ_NAME)
  return list

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
    agcDict=makeGcauCfgDictFromAgc(self.agcLineList)
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
      
if __name__ == "__main__":
    unittest.main()

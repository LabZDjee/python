#! python3
"""jeep: general purpose library"""

import glob
import os
import unittest

# 
def makeFilenameList(path, globMask="*"):
  """get list of filenames (without path) given a path
and a "glob" mask (ex: "*_APP.agc")"""
  list = []
  for infile in glob.glob(os.path.join(path, globMask)):
    if os.path.isfile(infile):
     list.append(os.path.basename(infile))
  return list

def subDirList(path, depth=0, posix=False):
  """get all subdirectories of a path
 depth: number of levels we can go down (0 is unlimited)
 posix: forces posix directory delimiter"""
  subDirList.result = []
  def recurseInside(path, curDepth):
    if depth==0 or curDepth<=depth:
      currentList = glob.glob(path + "/*/")
      subDirList.result += currentList
      for subPath in currentList:
        recurseInside(subPath, curDepth+1)
  recurseInside(path, 1)
  for x in range(len(subDirList.result)):
    subDirList.result[x] = os.path.normpath(subDirList.result[x])
    if posix:
      subDirList.result[x]=subDirList.result[x].replace("\\", "/")
  return subDirList.result

def incrementInOrderedMultiCounter(orderedCounter, incrementTuple):
  """assigns and increments counters which are ordered
by an identity in a list
structure of this ordered multi-counter list:
  [(identity, count)...]
this function takes such a list "orderedCounter" as parameter and
a tuple "incrementTuple" of definition (ident, increment)
if "ident" exists in the list, associated count is incremented by "increment"
otherwise (ident, increment) is added to the list in order this list
to be sorted by "ident\""""
  (IDENT, INCREMENT) = incrementTuple
  LG = len(orderedCounter)
  if LG != 0:
    i = 0
    while i < LG:
      (curIdent, count) = orderedCounter[i]
      if IDENT == curIdent:
        (_, COUNT) = orderedCounter[i] 
        orderedCounter[i] = (IDENT, COUNT+INCREMENT)
        return
      elif IDENT < curIdent:
        orderedCounter.insert(i, incrementTuple)
        return
      i += 1
  orderedCounter.append(incrementTuple)

# Unit Tests

class TestJeep(unittest.TestCase):
  def test_incrementInOrderedMultiCounter(self):
    orderedCountList = []
    DUT = incrementInOrderedMultiCounter # Definition Under Test
    TRUE = self.assertTrue
    DUT(orderedCountList, (4, 3))
    TRUE(orderedCountList == [(4, 3)])
    DUT(orderedCountList, (1, 5))
    TRUE(orderedCountList == [(1, 5), (4, 3)])
    DUT(orderedCountList, (1, 5))
    TRUE(orderedCountList == [(1, 10), (4, 3)])
    DUT(orderedCountList, (3, 2))
    TRUE(orderedCountList == [(1, 10), (3, 2), (4, 3)])
    DUT(orderedCountList, (3, -4))
    TRUE(orderedCountList == [(1, 10), (3, -2), (4, 3)])
    DUT(orderedCountList, (6, 8))
    TRUE(orderedCountList == [(1, 10), (3, -2), (4, 3), (6, 8)])
    orderedCountList.clear()
    DUT(orderedCountList, ("c", "C"))
    DUT(orderedCountList, ("c", "K"))
    DUT(orderedCountList, ("a", "A"))
    DUT(orderedCountList, ("b", "B"))
    DUT(orderedCountList, ("z", "Z"))
    TRUE(orderedCountList == [("a", "A"), ("b", "B"), ("c", "CK"), ("z", "Z")])
    
if __name__ == "__main__":
    unittest.main()


 

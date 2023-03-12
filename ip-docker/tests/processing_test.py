"""
Tests for image processing in the service Module go here
"""
import filecmp
import numpy as np
import unittest
import sys
sys.path.append("..") # added!
from util.image_processor import processImgFromLocal



class ProssessingTest(unittest.TestCase):
    # Tests the output of the image processing against a verified solution
    def testImageProcess(self):
        result_array = processImgFromLocal('res/example_input_image.tif')
        result_array = np.array(np.array(result_array))
        result_array.tofile('exampleArray.dat',",")
        self.assertEqual(filecmp.cmp('exampleArray.dat', 'array_solution.dat'), True)


if __name__ == '__main__':
    unittest.main()
  
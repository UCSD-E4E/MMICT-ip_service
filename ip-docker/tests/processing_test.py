"""
Tests for image processing in the service Module go here
"""
import filecmp
from numpy import ndarray
from service.image_processor import processImgFromLocal

# Tests the output of the image processing against a verified solution
def testImageProcess():
    array = processImgFromLocal('res/example_input_image.tif')
    array = ndarray(array)
    array.tofile('exampleArray.dat',",")
    return (filecmp.cmp('exampleArray.dat', 'array_solution.dat'))


assert(testImageProcess())
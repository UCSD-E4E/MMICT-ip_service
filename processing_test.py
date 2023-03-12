"""
Tests the processing methods in service against verified correct output
"""
import filecmp
from numpy import ndarray
from service.image_processor import processImgFromLocal


array = processImgFromLocal('res/example_input_image.tif')
array = ndarray(array)
array.tofile('exampleArray.dat',",")

assert(filecmp.cmp('exampleArray.dat', 'array_solution.dat'))

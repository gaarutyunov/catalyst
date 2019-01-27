from typing import Callable, Type, List

import numpy as np
from catalyst.data.functional import read_image


class BaseReader:
    """
    Reader abstraction for all Readers
    """
    def __init__(
            self,
            row_key: str,
            dict_key: str):
        """
        :param row_key: input key to use from annotation dict
        :param dict_key: output key to use to store the result
        """
        self.row_key = row_key
        self.dict_key = dict_key

    def __call__(self, row):
        """
        Applies a row from your annotations dict and
            transfer it to data, needed by your network
            for example open image by path, or read string and tokenize it.
        :param row: elem in your dataset. It can be row in csv, or image for example.
        :return: Data object used for your neural network
        """
        pass


class ImageReader(BaseReader):
    """
    Image reader abstraction.
    """

    def __init__(self, row_key: str, dict_key: str, datapath: str = None, grayscale: bool = False):
        """
        :param row_key: input key to use from annotation dict
        :param dict_key: output key to use to store the result
        :param datapath: path to images dataset
            (so your can use relative paths in annotations)
        :param grayscale: boolean flag
            if you need to work only with grayscale images
        """
        super().__init__(row_key, dict_key)
        self.datapath = datapath
        self.grayscale = grayscale

    def __call__(self, row):
        image_name = str(row[self.row_key])
        img = read_image(
            image_name, datapath=self.datapath, grayscale=self.grayscale
        )

        result = {self.dict_key: img}
        return result


class ScalarReader(BaseReader):
    """
    Numeric data reader abstraction.
    """

    def __init__(self, row_key: str, dict_key: str, dtype: Type = np.float32, default_value: float = None,
                 one_hot_classes: int = None):
        """
        :param row_key: input key to use from annotation dict
        :param dict_key: output key to use to store the result
        :param dtype: datatype of scalar values to use
        :param default_value: default value to use if something goes wrong
        """
        super().__init__(row_key, dict_key)
        self.dtype = dtype
        self.default_value = default_value
        self.one_hot_classes = one_hot_classes

    def __call__(self, row):
        scalar = self.dtype(row.get(self.row_key, self.default_value))
        if self.one_hot_classes is not None \
                and scalar is not None and scalar >= 0:
            one_hot = np.zeros(self.one_hot_classes, dtype=np.float32)
            one_hot[scalar] = 1.0
            scalar = one_hot
        result = {self.dict_key: scalar}
        return result


class TextReader(BaseReader):
    """
    Text reader abstraction.
    """

    def __init__(self, row_key: str, dict_key: str, encode_fn: Callable = lambda x: x):
        """
        :param row_key: input key to use from annotation dict
        :param dict_key: output key to use to store the result
        :param encode_fn: encode function to use to prepare your data
            for example convert chars/words/tokens to indices, etc
        """
        super().__init__(row_key, dict_key)
        self.encode_fn = encode_fn

    def __call__(self, row):
        text = row[self.row_key]
        text = self.encode_fn(text)
        result = {self.dict_key: text}
        return result


class ReaderCompose(object):
    """
    Abstraction to compose several readers into one open function.
    """

    def __init__(self, readers: List[BaseReader], mixins: [] = None):
        """
        :param readers: list of reader to compose
        :param mixins: list of mixins to use
        """
        self.readers = readers
        self.mixins = mixins or []

    def __call__(self, row):
        result = {}
        for fn in self.readers:
            result = {**result, **fn(row)}
        for fn in self.mixins:
            result = {**result, **fn(result)}
        return result

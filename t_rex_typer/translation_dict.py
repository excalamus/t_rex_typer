import re
import json


# TODO better parsing of text
WORD_REGEX = r"[\w']+|[{}()\[\]~`!@#$%^&*-_+=|\/.,]"


class TranslationDict:
    """Python dict-like storage for Plover dictionaries.

    Parameters
    ----------

    plover_dicts : iterable

      Iterable of paths to Plover dictionaries.


    """

    def __init__(self, plover_dicts=None):
        self._data = {}
        self._data = self.load(plover_dicts)

    @classmethod
    def load(self, to_load=None):
        """Import Plover json format dictionaries.

        Parameters
        ----------

        to_load : iterable, optional

          Iterable (e.g. list or tuple) of Plover dictionary file
          paths in json format.

        Returns
        -------

        Python dict mapping strokes to phrases.

        """

        # TODO handle different dictionary types

        if not to_load:
            to_load = []

        temp = {}
        for path in to_load:
            with open(path, 'r') as f:
                contents = f.read()
                loaded = json.loads(contents)

            temp = {**temp, **loaded}

        return temp

    def _get_stroke_indices(self, phrase):
        """Find indices of all strokes matching a phrase.

        Parameters
        ----------

        phrase : str

          Word or phrase.

        Returns
        -------

        List of indices corresponding to strokes in the Plover
        dictionary.

        """

        # TODO fails for some words and punctuation.  This may be
        # because of the direct comparison.  A phrase may map to
        # something like '{~|"^}' (i.e. double quote, KW-GS).

        return [i for i, entry in enumerate(list(self._data.values()))
                if entry == phrase.lower().strip()]

    def get_strokes(self, phrase, sorted=True):
        """Find strokes in the dictionary corresponding to the phrase.

        Parameters
        ----------

        phrase : str

          Word or phrase.

        sorted : bool, optional

          When True, return the list of strokes ordered from shortest
          to longest.  Default is True.

        Returns
        -------

        List of strokes corresponding to the given phrase.

        """

        # TODO performance

        indices = self._get_stroke_indices(phrase)
        strokes = [list(self._data.keys())[i] for i in indices]
        if sorted:
            strokes.sort(key=len)
        return strokes

    def translate(self, text):
        """Translate to steno strokes.

        Words are defined by the WORD_REGEX and are translated
        one-to-one.  Each word corresponds to a stroke.  For example,
        the phrase "as well as" returns three strokes even if a brief
        exists to do it in one stroke.

        Parameters
        ----------

        text : str

          Corpus to be translated.

        Returns
        -------

        List of strokes corresponding to each word in the text.

        """

        # TODO lots to optimize here. Aside from the lookup being
        # crazy slow, there's the issue of getting the correct
        # translation.  For example, "went" will be translated as
        # 'WEBLT' instead of 'WEPBT' since the strings have the same
        # length and B < P.

        split = re.findall(WORD_REGEX, text)
        translation = [self.get_strokes(w)[0] for w in split]
        return translation

    def __repr__(self):
        return self._data.__repr__()

    #######################
    # container emulation #
    #######################

    # The following functions are part of the Python API for dict-like
    # behavior. Details can be found in the Python documentation
    # (python) Emulating container types.

    def pop(self, key, default=None):
        return self._data.pop(key, default)

    def __setitem__(self, key, value):
        self._data[key] = value

    def __getitem__(self, key):
        return self._data[key]

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()

    def __iter__(self):
        return self._data.__iter__()

    def __contains__(self, item):
        return item in self._data

    def __len__(self):
        return len(self._data)

    def get(self, key, default=None):
        try:
            return self._data[key]
        except KeyError:
            return default

import re
import json


# single quotes are used in two ways. First, as apostrophes in the
# middle of a string of characters. Second at the boundary of a word
# as a quote or as an abbreviation.  Exclude single quotes and parse
# these out later.
WORD_REGEX = r"[\w']+|[{}()\[\]~`!@#$%^&*-_+=|\/.,:;\"]"


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

    @classmethod
    def split_into_strokable_units(self, text):
        """Split text into strokable units.

        NOTE: TODO: This is not likely accurate! It is assumed that
        text split on spaces and symbols will match a key in the
        Plover dictionary.  That assumption may not be true.  However,
        it should be good enough to get the application in a useable
        state.

        Parameters
        ----------
        text : str

          Text to be split.

        Returns
        -------

          List of strokable units (i.e. words and symbols)

        """

        # Symbols need to be strokable words except that single quote
        # shouldn't be a stroke word if it appears inside a word.  The
        # following works. TODO What's a better way to express this?

        # split into words
        _split_with_single_quotes = re.findall(WORD_REGEX, text)

        # split apostrophes at the beginning and end of a word
        text_split = []
        for stroke_word in _split_with_single_quotes:
            if stroke_word[0] == "\'" or stroke_word[-1] == "\'":
                for w in stroke_word.split("\'"):
                    if w:
                        text_split.append(w)
                    else:
                        # split removes separator and returns empty
                        # string
                        text_split.append("'")
            else:
                text_split.append(stroke_word)

        return text_split

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

        split = self.split_into_strokable_units(text)
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

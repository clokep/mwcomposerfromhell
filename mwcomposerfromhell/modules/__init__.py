import importlib


class UnknownModule(Exception):
    pass


class ModuleStore:
    """
    The module store handles invoking scripts installed in MediaWiki.

    See https://www.mediawiki.org/wiki/Extension:Scribunto
    """

    def get_function(self, module_name, function_name):
        # MediaWiki treats the first character of article names as
        # case-insensitive.
        possible_module_names = [module_name[0].lower() + module_name[1:],
                                 module_name[0].upper() + module_name[1:]]
        for module_name in possible_module_names:
            try:
                module = importlib.import_module('mwcomposerfromhell.modules.' + module_name)
                break
            except ModuleNotFoundError:
                pass
        else:
            raise UnknownModule()

        # Get the function from the module. (Note that this is case-sensitive.)
        try:
            function = getattr(module, function_name)
        except AttributeError:
            raise UnknownModule()

        return function

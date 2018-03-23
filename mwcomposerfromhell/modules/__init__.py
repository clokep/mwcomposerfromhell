import importlib

class ModuleStore:
    """
    The module store handles invoking scripts installed in MediaWiki.

    See https://www.mediawiki.org/wiki/Extension:Scribunto
    """

    def get_function(self, module_name, function_name):
        module = importlib.import_module('mwcomposerfromhell.modules.' + module_name)
        function = getattr(module, function_name)

        return function

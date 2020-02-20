import sublime, sublime_plugin
from sublime import Region

assertions = [
    ("TKAssert", "TKAssert(${1:condition});"),
    ("TKAssertEquals", "TKAssertEquals(${1:result}, ${2:expected});"),
    ("TKAssertNotEquals", "TKAssertNotEquals(${1:result}, ${2:expected});"),
    ("TKAssertFloatEquals", "TKAssertFloatEquals(${1:result}, ${2:expected});"),
    ("TKAssertExactEquals", "TKAssertExactEquals(${1:result}, ${2:expected});"),
    ("TKAssertNotExactEquals", "TKAssertNotExactEquals(${1:result}, ${2:expected});"),
    ("TKAssertObjectEquals", "TKAssertObjectEquals(${1:result}, ${2:expected});"),
    ("TKAssertNotObjectEquals", "TKAssertNotObjectEquals(${1:result}, ${2:expected});"),
    ("TKAssertNotNull", "TKAssertNotNull(${1:value});"),
    ("TKAssertNull", "TKAssertNull(${1:value});"),
    ("TKAssertNotUndefined", "TKAssertNotUndefined(${1:value});"),
    ("TKAssertUndefined", "TKAssertUndefined(${1:value});"),
    ("TKAssertThrows", "TKAssertThrows(function(){\n\t$1\n});"),
    ("TKAssertLessThan", "TKAssertLessThan(${1:result}, ${2:expected});"),
    ("TKAssertLessThanOrEquals", "TKAssertLessThanOrEquals(${1:result}, ${2:expected});"),
    ("TKAssertGreaterThan", "TKAssertGreaterThan(${1:result}, ${2:expected});"),
    ("TKAssertGreaterThanOrEquals", "TKAssertGreaterThanOrEquals(${1:result}, ${2:expected});"),
    ("TKAssertArrayEquals", "TKAssertArrayEquals(${1:result}, ${2:expected});"),
]

class JSKitAutocomplete(sublime_plugin.EventListener):

    def on_query_completions(self, view, prefix, locations):
        if not view.match_selector(locations[0], 'source.js - comment - string'):
            return None
        imports = self.imports(view)
        if 'TestKit' in imports and prefix.lower() == 't':
            return assertions
        return None

    def imports(self, view):
        imports = []
        regions = view.split_by_newlines(Region(0, 1024))
        for region in regions:
            line = view.substr(region)
            if line[0:11] == '// #import ':
                imports.append(line[11:])
        return set(imports)
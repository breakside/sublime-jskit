import os
import os.path
from SublimeLinter.lint import NodeLinter

# Adapted from https://github.com/SublimeLinter/SublimeLinter-jshint
class JSKit(NodeLinter):
    name = "jshint-jskit"
    cmd = ['jshint', '--verbose', '${args}', '-']
    regex = (
        r'^.+?: line (?P<line>\d+), col (?P<col>\d+), '
        r'(?P<message>'
        # unexpected use of ++ etc
        r'|.+\'(?P<unexpected>.+)\'\.(?=.+W016)'
        # duplicate key
        r'|.+\'(?P<duplicate>.+)\'.+(?=.+W075)'
        # camel case
        r'|.+\'(?P<no_camel>.+)\'.+(?=.+W106)'
        # unexpected use, typically use of non strict operators
        r'|.+\'(?P<actual>.+)\'\.(?=.+W116)'
        # match all messages
        r'|.+)'
        # capture error, warning and code
        r' \((?:(?P<error>E\d+)|(?P<warning>W\d+))\)'
    )
    defaults = {
        'selector': 'source.js - meta.attribute-with-value',
        # `filename` will determine the config finding algo of jshint. We
        # fake a name for unsaved files bc we sadly cannot just point to a
        # folder.
        '--filename:': '${file:${folder}/unsaved.js}',
        '--config:': '${config}'
    }

    @classmethod
    def can_lint_view(cls, view, settings):
        if settings.get('enable'):
            return super().can_lint_view(view, settings)
        return False

    def split_match(self, match):
        """
        Return the components of the match.

        We override this to catch linter error messages and return more presise
        info used for highlighting.

        """
        error = match.group('error')
        warning = match.group('warning')
        message = match.group('message')
        # force line numbers to be at least 0
        # if not they appear at end of file
        line = max(int(match.group('line')) - 1, 0)
        col = int(match.group('col')) - 1
        near = None

        # Note: jshint usually produces a `col` value, but sometimes the
        # col points to the last char of the offending code. When a col is
        # given, we can simply adjust the size of the error using near bc
        # SublimeLinter will just take the length of near in that case.
        # So when you see `col -= ...` we just shift the beginning of the
        # error to the left.

        if warning:
            # unexpected use of ++ etc.
            if warning == 'W016':
                near = match.group('unexpected')

            # mark the duplicate key
            elif warning == 'W075' and match.group('duplicate'):
                near = match.group('duplicate')
                col -= len(match.group('duplicate'))

            # mark the no camel case key
            elif warning == 'W106':
                near = match.group('no_camel')
                col -= len(match.group('no_camel'))

            # if we have a operator == or != manually change the column,
            # this also handles the warning when curly brackets are required
            elif warning == 'W116':
                # match the actual result
                near = match.group('actual')

                # if a comparison then also change the column
                if near == '!=' or near == '==':
                    col -= len(near)

        return match, line, col, error, warning, message, near

    def lint(self, code, view_has_changed):
        working_dir = self.get_working_dir()
        filename = self.context.get('file')
        if not filename:
            filename = os.path.join(self.context.get('folder') or working_dir, 'filename.js')
        predefs = get_jskit_globals(working_dir, filename, code)
        with ClosableNamedTemporaryFile() as fp:
            self.context['config'] = fp.name
            create_config(filename, fp, predefs)
            return super().lint(code, view_has_changed)


class ClosableNamedTemporaryFile(object):

    fp = None

    def __init__(self):
        import tempfile
        self.fp = tempfile.NamedTemporaryFile(delete=False)

    def __enter__(self):
        return self.fp

    def __exit__(self, type, value, tb):
        if self.fp is not None:
            self.fp.close()
            os.unlink(self.fp.name)
            self.fp = None


def create_config(jsfilename, configfp, predefs):
    import json
    config = existing_config(jsfilename)
    if 'predef' not in config:
        config['predef'] = []
    config['predef'].extend(predefs)
    configfp.write(json.dumps(config).encode('utf-8'))
    configfp.close()


def existing_config(filename):
    import json
    path = find_jshint_config_path(os.path.dirname(filename))
    if path is None:
        return dict()
    fp = open(path, 'r')
    jsontext = fp.read()
    config = json.loads(jsontext)
    return config


def find_jshint_config_path(folder):
    prev = None
    while folder != prev:
        candidate = os.path.join(folder, '.jshintrc')
        if os.path.exists(candidate):
            return candidate
        prev = folder
        folder = os.path.dirname(folder)
    return None


def get_jskit_globals(working_dir, filename, file_contents):
    import subprocess
    delimiter = ","
    cmd = ["npx", "--no-install", "jskit", "globals", "--frameworks", "--delimiter", delimiter, "--filename", filename, "-"]
    process = subprocess.Popen(cmd, cwd=working_dir, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (out, err) = process.communicate(file_contents.encode('utf-8'))
    names = []
    if process.returncode != 0:
        raise Exception(err.decode('utf-8'))
    names = out.decode('utf-8').split(delimiter)
    return names
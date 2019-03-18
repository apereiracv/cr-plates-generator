#######################################################################
# Copyright (c) 2019 Alejandro Pereira

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>

#######################################################################
#!/usr/bin/python

import jsonpickle

#region Module Functions
__jsonPyObjectAcceptedPrefixes = None


def initialize(acceptedPrefixes):
    if not acceptedPrefixes: return

    global __jsonPyObjectAcceptedPrefixes
    __jsonPyObjectAcceptedPrefixes = acceptedPrefixes


def encodeJson(value):
    jsonValue = jsonpickle.encode(value)
    return jsonValue


def decodeJson(jsonValue):
    if not jsonValue: return None

    __sanitize(jsonValue)

    value = jsonpickle.decode(jsonValue)
    return value


def serializeJson(value, fileName):
    jsonFile = open(fileName, 'w')
    jsonValue = encodeJson(value)
    jsonFile.write(jsonValue)
    jsonFile.close()


def deserializeJson(fileName):
    jsonFile = open(fileName)
    jsonValue = jsonFile.read()
    value = decodeJson(jsonValue)
    return value

def __sanitize(value):
    """Ensures the specified value contains safe JSON."""

    if not value: return

    # Allow "py/object" only. Do not allow "py/type" or "py/reduce".
    if 'py/reduce' in value or 'py/type' in value:
        raise ValueError('py/reduce and py/type are not allowed in JSON values to be decoded.')

    # Get the list of "py/object" values. Accept only the ones with the accepted prefix.
    global __jsonPyObjectAcceptedPrefixes
    if not __jsonPyObjectAcceptedPrefixes or len(__jsonPyObjectAcceptedPrefixes) == 0: return

    pattern = '"py/object"[ \t]*:[ \t]*"[^"]+"'
    matches = re.findall(pattern, value, re.DOTALL)
    if matches and len(matches):
        for match in matches:
            pair = match.split(":")
            typeName = pair[1].strip(' \t"')

            accepted = [ item for item in __jsonPyObjectAcceptedPrefixes if typeName.startswith(item) ]
            if not (accepted and len(accepted)):
                raise ValueError('Specified type name is not allowed for decoding.')

#endregion
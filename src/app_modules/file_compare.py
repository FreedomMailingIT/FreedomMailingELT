"""Class to compare zipped, zipped files for equality."""


from zipfile import ZipFile
from io import BytesIO
from pathlib import Path


class NestedZipPath:
    """Represents a file inside a ZIP that is itself inside another ZIP.

    Suggested by CoPilot after long conversation.
    """

    def __init__(self, outer_zip, inner_zip, inner_file, *, decode=True):
        self.outer_zip = Path(outer_zip)
        self.inner_zip = inner_zip
        self.inner_file = inner_file
        self.decode = decode

    def read(self):
        """The at text file enclosed in a zip file which is enclosed in a zip file.

        Used mainly in testing to make sure recently modified file matches known correct file.
        """
        with ZipFile(self.outer_zip) as outer:
            inner_bytes = outer.read(self.inner_zip)
            with ZipFile(BytesIO(inner_bytes)) as inner:
                data = inner.read(self.inner_file)
                return data.decode() if self.decode else data

    def __eq__(self, other):
        if not isinstance(other, NestedZipPath):
            return NotImplemented
        return self.read() == other.read()

    def __repr__(self):
        return f"NestedZipPath({self.outer_zip!r}, {self.inner_zip!r}, {self.inner_file!r})"

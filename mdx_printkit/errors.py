class PrintKitError(Exception):
    """An actionable conversion failure suitable for displaying in the CLI."""


class AssetError(PrintKitError):
    """An individual asset failure; the document can still be printed."""

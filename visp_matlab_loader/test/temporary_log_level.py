import logging


class TempLogLevel:
    """Temporary changes the log level of a logger.

    Can be used using the WITH statement, similar to this:

    with TempLogLevel('visp_matlab_loader.execute.compiled_project_executor', logging.INFO):
        # Do something

    """

    def __init__(self, logger=None, level=logging.DEBUG):
        """
        Initialize the context manager.

        :param logger: The logger to change the level of. If None, changes the level of the root logger.
        :param level: The temporary level to set the logger to.
        """
        self.logger = logging.getLogger(logger) if logger else logging.getLogger()
        self.level = level
        self.original_level = self.logger.level
        self.original_handler_levels = [handler.level for handler in self.logger.handlers]

        # If the logger has no handlers, add a StreamHandler.
        if not self.logger.handlers:
            self.logger.addHandler(logging.StreamHandler())

    def __enter__(self):
        """
        Enter the context, changing the logger's level and all handler levels to the temporary level.
        """
        self.logger.setLevel(self.level)
        for handler in self.logger.handlers:
            handler.setLevel(min(handler.level, self.level))

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the context, changing the logger's level and all handler levels back to the original levels.
        """
        self.logger.setLevel(self.original_level)
        for handler, original_level in zip(self.logger.handlers, self.original_handler_levels):
            handler.setLevel(original_level)

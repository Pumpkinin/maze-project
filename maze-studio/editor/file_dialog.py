class FileDialog:
    def __init__(self):
        self.mode = None
        self.files = []
        self.filename = ""

    def open_save(self, files, filename):
        self.mode = "save"
        self.files = files
        self.filename = filename

    def open_open(self, files, filename):
        self.mode = "open"
        self.files = files
        self.filename = filename

    def close(self):
        self.mode = None

import os


class AssetRegistry:
    def __init__(self, root):
        self.root = root
        self.entries = {}
        self._cache = {}

    def scan(self, kind, subdir):
        d = os.path.join(self.root, subdir)
        if not os.path.isdir(d):
            return
        self.entries.setdefault(kind, {})
        for f in os.listdir(d):
            if f.endswith(".json"):
                name = os.path.splitext(f)[0]
                self.entries[kind][name] = os.path.join(d, f)

    def path(self, kind, name):
        return self.entries.get(kind, {}).get(name)

    def list(self, kind):
        return sorted(self.entries.get(kind, {}).keys())

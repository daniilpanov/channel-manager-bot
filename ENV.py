class ENV:
    def __init__(self, filepath):
        self.filepath = filepath
        with open(filepath) as file:
            raw_data = list(file)
        self.data = dict()
        for i in raw_data:
            i = i.strip()
            if i:
                i = i.split('=')
                self.data[i[0].lower()] = i[1] if len(i) > 1 else None

    def get(self, key):
        return (self.data[key] if self.data[key] else key) if key in self.data else None

    def set(self, key, value):
        self.data[key] = value


env = ENV('.env')

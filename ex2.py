class om:
    _instance = None
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, value):
        # Verificăm dacă 'value' nu a fost deja setat pentru a preveni rescrierea
        if not hasattr(self, 'value'):
            self.value = value


human1 = om(3)
human2 = om(100)

print(human1.value)

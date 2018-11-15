from chatbots.backends.bdb import backend


class Model:
    def __init__(self, connection, _id):
        self.id = _id
        self.history = []
        self.load(connection)

    @property
    def raw(self):
        return self.history[0]['metadata']

    @property
    def namespace(self):
        return self.history[0]['metadata']['namespace']

    @property
    def recent(self):
        if len(self.history) > 0:
            return self.history[-1]
        return None

    def load(self, connection):
        self.history = backend.history(asset_id=self.id, connection=connection)

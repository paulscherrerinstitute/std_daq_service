
class StatusListener(object):
    def __init__(self, on_status_change_function):
        self.on_status_change = on_status_change_function

    def on_broker_message(self):
        pass

# client-app/main.py
import sys
import logging
import asyncio
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal
from ui.main_window import AgentMainWindow
from core.gateway_service import GatewayServiceThread
from core.command_handler import CommandDispatcher

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [AGENT] - %(levelname)s - %(message)s")
logger = logging.getLogger("Main")

class CommandBridge(QObject):
    dispatch_signal = pyqtSignal(dict)

    def __init__(self, dispatcher):
        super().__init__()
        self.dispatcher = dispatcher

    def handle(self, command_data: dict):
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(self.dispatcher.handle(command_data))
        finally:
            loop.close()

def main():
    app = QApplication(sys.argv)

    main_window = AgentMainWindow()
    main_window.show()

    gateway_thread = GatewayServiceThread()
    dispatcher = CommandDispatcher(gateway_thread)
    bridge = CommandBridge(dispatcher)

    gateway_thread.connection_changed.connect(main_window.update_connection_status)
    gateway_thread.command_received.connect(bridge.handle)

    gateway_thread.start()

    exit_code = app.exec()

    gateway_thread.stop()
    gateway_thread.wait()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
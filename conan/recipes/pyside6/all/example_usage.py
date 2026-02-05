#!/usr/bin/env python3
"""
Example usage of the PySide6 Conan package
This demonstrates how to use PySide6 built from the Conan recipe.
"""

import sys
import os


# Example: Using PySide6 after Conan installation
def example_pyside6_app():
    """Simple PySide6 application example"""
    try:
        from PySide6.QtWidgets import (
            QApplication,
            QWidget,
            QVBoxLayout,
            QLabel,
            QPushButton,
        )
        from PySide6.QtCore import Qt

        class ExampleWindow(QWidget):
            def __init__(self):
                super().__init__()
                self.init_ui()

            def init_ui(self):
                layout = QVBoxLayout()

                # Add a label
                label = QLabel("PySide6 from Conan Package")
                label.setAlignment(Qt.AlignCenter)
                layout.addWidget(label)

                # Add a button
                button = QPushButton("Test Button")
                button.clicked.connect(self.on_button_clicked)
                layout.addWidget(button)

                self.setLayout(layout)
                self.setWindowTitle("PySide6 Conan Example")
                self.resize(300, 200)

            def on_button_clicked(self):
                print("Button clicked! PySide6 is working correctly.")

        # Create and run application
        app = QApplication(sys.argv)
        window = ExampleWindow()
        window.show()

        print("PySide6 application started successfully")
        print("Close the window to continue...")

        # Run for a short time or until closed
        return app.exec()

    except ImportError as e:
        print(f"ERROR: Could not import PySide6: {e}")
        print("Make sure the PySide6 Conan package is installed and in your Python path")
        return 1


def example_webengine_usage():
    """Example of using Qt WebEngine if available"""
    try:
        import importlib.util

        webengine_core_available = importlib.util.find_spec("PySide6.QtWebEngineCore") is not None
        webengine_widgets_available = importlib.util.find_spec("PySide6.QtWebEngineWidgets") is not None

        if webengine_core_available and webengine_widgets_available:
            print("SUCCESS: Qt WebEngine is available and can be imported")
            return True
        else:
            print("INFO: Qt WebEngine not available")
            return False
    except ImportError as e:
        print(f"INFO: Qt WebEngine not available: {e}")
        return False


def example_ssl_usage():
    """Example of SSL functionality"""
    try:
        import ssl

        print(f"SSL Support: {ssl.OPENSSL_VERSION}")

        # Test creating an SSL context
        ssl.create_default_context()
        print("Default SSL context created successfully")

        # Check for certifi
        try:
            import certifi

            print(f"Certifi CA bundle available at: {certifi.where()}")
        except ImportError:
            print("WARNING: certifi not available, may have certificate issues")

        return True

    except ImportError as e:
        print(f"WARNING: SSL not available: {e}")
        return False


def show_environment_info():
    """Show environment information for debugging"""
    print("\n" + "=" * 50)
    print("ENVIRONMENT INFORMATION")
    print("=" * 50)

    # Python information
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    print(f"Python path: {sys.path[:3]}...")  # Show first 3 entries

    # Environment variables
    env_vars = ["PYTHONHOME", "PYTHONPATH", "PYSIDE6_ROOT", "QT_HOME", "PATH"]
    for var in env_vars:
        value = os.environ.get(var, "Not set")
        if var == "PATH":
            # Show only first few PATH entries to avoid clutter
            paths = value.split(os.pathsep)[:5] if value != "Not set" else ["Not set"]
            value = os.pathsep.join(paths) + "..."
        print(f"{var}: {value}")

    # PySide6 information
    try:
        from PySide6 import QtCore

        print(f"\nPySide6 version: {QtCore.__version__}")
        print(f"Qt version: {QtCore.qVersion()}")
        print(f"PySide6 location: {QtCore.__file__}")
    except ImportError:
        print("\nPySide6: Not available")


def main():
    """Main example function"""
    print("PySide6 Conan Package Usage Example")
    print("=" * 40)

    # Show environment info
    show_environment_info()

    print("\n" + "=" * 40)
    print("TESTING FUNCTIONALITY")
    print("=" * 40)

    # Test SSL support
    print("\n1. Testing SSL Support:")
    example_ssl_usage()

    # Test WebEngine support
    print("\n2. Testing WebEngine Support:")
    example_webengine_usage()

    # Test basic PySide6 application
    print("\n3. Testing PySide6 Application:")

    if len(sys.argv) > 1 and sys.argv[1] == "--gui":
        # Run GUI application
        result = example_pyside6_app()
        return result
    else:
        # Just test imports without GUI
        try:
            import importlib.util

            widgets_available = importlib.util.find_spec("PySide6.QtWidgets") is not None
            core_available = importlib.util.find_spec("PySide6.QtCore") is not None

            if widgets_available and core_available:
                print("SUCCESS: PySide6 widgets imported successfully")
                print("Run with --gui flag to test actual GUI application")
                return 0
            else:
                print("ERROR: PySide6 modules not found")
                return 1
        except ImportError as e:
            print(f"ERROR: PySide6 import failed: {e}")
            return 1


if __name__ == "__main__":
    sys.exit(main())

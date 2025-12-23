# Estilos QSS Modernos (CSS para Desktop)

DARK_THEME = """
QMainWindow {
    background-color: #1e1e1e;
}

/* Sidebar */
QWidget#Sidebar {
    background-color: #252526;
    border-right: 1px solid #3e3e42;
}

QPushButton#SidebarButton {
    background-color: transparent;
    border: none;
    color: #cccccc;
    text-align: left;
    padding: 12px 20px;
    font-size: 14px;
    font-weight: 500;
}

QPushButton#SidebarButton:hover {
    background-color: #37373d;
    color: white;
}

QPushButton#SidebarButton:checked {
    background-color: #37373d;
    color: #4cc2ff; /* Azul VS Code */
    border-left: 3px solid #4cc2ff;
}

/* Main Area */
QLabel {
    color: #eeeeee;
    font-family: 'Segoe UI', 'Roboto', sans-serif;
}

/* Inputs */
QLineEdit {
    background-color: #3c3c3c;
    border: 1px solid #3e3e42;
    color: white;
    padding: 8px;
    border-radius: 4px;
}
QLineEdit:focus {
    border: 1px solid #4cc2ff;
}

/* Logs */
QTextEdit {
    background-color: #1e1e1e;
    color: #00ff00; /* Hacker Green */
    border: 1px solid #333;
    font-family: Consolas, Monospace;
    font-size: 12px;
}
"""

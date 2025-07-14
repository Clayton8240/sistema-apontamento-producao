import os
from windows.login_window import LoginWindow

if __name__ == "__main__":
    # Define os caminhos para os assets para garantir que sejam encontrados
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    ICON_PATH = os.path.join(APP_DIR, 'icon.png')
    LOGO_PATH = os.path.join(APP_DIR, 'logo.png')
    
    # Inicia a janela de login
    login_app = LoginWindow(icon_path=ICON_PATH, logo_path=LOGO_PATH)
    login_app.mainloop()

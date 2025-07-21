# -*- coding: utf-8 -*-

"""
Ponto de entrada principal da aplicação GERENCIAMentor.
Inicia a janela de login e o loop principal da interface gráfica.
"""
import os
from windows.login_window import LoginWindow

if __name__ == "__main__":
    # Define os caminhos absolutos para os assets, garantindo que sejam encontrados
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    ICON_PATH = os.path.join(APP_DIR, 'icon.png')
    LOGO_PATH = os.path.join(APP_DIR, 'logo.png')
    
    # Cria uma instância da janela de login, passando os caminhos
    app = LoginWindow(icon_path=ICON_PATH, logo_path=LOGO_PATH)
    
    # Inicia o loop principal do Tkinter, que mantém a aplicação rodando
    app.mainloop()
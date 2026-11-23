# Raycleaner4000



<div align="center">



> Uma ferramenta de limpeza de sistema leve, moderna e elegante para Windows, desenvolvida em Python com CustomTkinter.



![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python&logoColor=white)

![CustomTkinter](https://img.shields.io/badge/CustomTkinter-UI-green?style=for-the-badge)

![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?style=for-the-badge&logo=windows&logoColor=white)



</div>



---



## Sobre o Projeto



O **Raycleaner4000** nasceu com o objetivo de oferecer uma interface limpa, rápida e agradável ("Dark Soft") para realizar a manutenção básica e a remoção de arquivos temporários no Windows. Chega de utilitários com visual antiquado; o Raycleaner une eficiência e design moderno.



---



## Funcionalidades



* **Limpeza de Pastas Temporárias do Sistema** (`C:\Windows\Temp`)

* **Temporários do Usuário** (`%TEMP%`)

* **Arquivos de Prefetch** (`C:\Windows\Prefetch`)

* **Histórico de Arquivos Recentes** do Windows

* **Esvaziamento Automático da Lixeira** via PowerShell

* **Verificação de Administrador** integrada para garantir permissões de acesso adequadas.



---



## Como Executar (Desenvolvimento)



Certifique-se de ter o **Python 3.8+** instalado em sua máquina.



1. Clone este repositório:

   ```bash

   git clone https://github.com/seu-usuario/raycleaner4000.git

   cd raycleaner4000

   ```



2. Instale as dependências necessárias:

   ```bash

   pip install customtkinter pillow

   ```



3. Execute a aplicação:

   ```bash

   python main.py

   ```



---



## Requisitos de Execução



* **Sistema Operacional:** Windows 10 ou 11.

* **Privilégios:** O aplicativo exige permissões de **Administrador** para conseguir limpar corretamente os diretórios protegidos do sistema (`Temp` e `Prefetch`).



---



## Contribuindo



Contribuições são sempre bem-vindas! Sinta-se à vontade para abrir uma *issue* ou enviar um *pull request* com melhorias, correções de bugs ou novas ideias.

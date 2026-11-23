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



## Como Instalar e Executar



Você pode usar o aplicativo de duas formas: através do arquivo executável pronto ou pelo código-fonte.



### Opção 1: Executável Pronto (Recomendado)



1. Clique na pasta **executável** no repositório.

2. Faça o download do arquivo `.exe` presente dentro da pasta.

3. Clique com o botão direito sobre o arquivo baixado e selecione **Executar como Administrador** (necessário para limpar pastas do sistema como Temp e Prefetch).



---



### Opção 2: Executar via Código-Fonte (Desenvolvimento)



Caso prefira rodar o projeto diretamente pelo Python:



1. Certifique-se de ter o **Python 3.8+** instalado em sua máquina.

2. Clone este repositório:

   ```bash

   git clone https://github.com/RayO-builder/RayCleaner4000.git

   cd RayCleaner4000

   ```

3. Instale as dependências necessárias:

   ```bash

   pip install customtkinter pillow

   ```

4. Execute a aplicação (como Administrador no terminal):

   ```bash

   python cleaner.py

   ```



---



## Requisitos de Execução



* **Sistema Operacional:** Windows 10 ou 11.

* **Privilégios:** O aplicativo exige permissões de **Administrador** para conseguir limpar corretamente os diretórios protegidos do sistema (`Temp` e `Prefetch`).



---



## Contribuindo



Contribuições são sempre bem-vindas! Sinta-se à vontade para abrir uma *issue* ou enviar um *pull request* com melhorias, correções de bugs ou novas ideias.

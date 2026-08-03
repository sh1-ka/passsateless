import os
import getpass
import time

# Зависимости для TUI
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt

try:
    import pyperclip
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False

# Импортируем вашу библиотеку (файл sisi_core.py должен лежать в этой же папке)
import sisi_core

# Имя файла базы данных по умолчанию (как в вашей библиотеке)
DB_FILENAME = "sisi.enc"

console = Console()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def draw_dashboard(data: dict):
    clear_screen()
    console.print(Panel("[bold cyan]SISI Password Manager[/bold cyan]", expand=False))
    
    if not data["content"]:
        console.print("[yellow]База данных пуста. Добавьте свою первую запись.[/yellow]\n")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("ID", style="dim", width=4, justify="center")
    table.add_column("Сервис (Service)", min_width=15)
    table.add_column("Логин (Login)", min_width=15)
    table.add_column("Версия", justify="center")
    table.add_column("Длина", justify="center")

    for idx, item in enumerate(data["content"]):
        table.add_row(
            str(idx),
            item.get("service", "N/A"),
            item.get("login", "N/A"),
            str(item.get("pass_ver", 0)),
            str(item.get("lnth", 15))
        )
    
    console.print(table)
    console.print()

def main_loop(master_key: str):
    while True:
        try:
            # Используем функцию из вашей библиотеки
            data = sisi_core._load_data(master_key, DB_FILENAME)
        except Exception as e:
            console.print(f"[bold red]Ошибка чтения базы данных: {e}[/bold red]")
            break

        draw_dashboard(data)
        
        console.print("[bold green]Доступные действия:[/bold green]")
        console.print(" [1] [cyan]Сгенерировать и получить пароль (по ID)[/cyan]")
        console.print(" [2] [green]Добавить новую запись[/green]")
        console.print(" [3] [red]Удалить запись[/red]")
        console.print(" [0] [dim]Выход[/dim]")
        
        choice = Prompt.ask("\nВыберите действие", choices=["0", "1", "2", "3"], default="0")
        
        if choice == "0":
            console.print("[dim]Выход из программы...[/dim]")
            break
            
        elif choice == "1":
            if not data["content"]:
                Prompt.ask("Нет записей. Нажмите Enter для продолжения")
                continue
                
            entry_id = IntPrompt.ask("Введите ID записи для получения пароля")
            if 0 <= entry_id < len(data["content"]):
                item = data["content"][entry_id]
                console.print("[yellow]Генерация пароля (Argon2 работает...)[/yellow]")
                
                try:
                    # Используем генератор из вашей библиотеки
                    pwd = sisi_core.generate_password(
                        master_key, 
                        item["login"], 
                        item["service"], 
                        item["pass_ver"], 
                        item["lnth"]
                    )
                    
                    console.print(Panel(f"[bold white]{pwd}[/bold white]", title="Сгенерированный пароль", expand=False))
                    
                    if CLIPBOARD_AVAILABLE:
                        pyperclip.copy(pwd)
                        console.print("[bold green]✔ Пароль скопирован в буфер обмена![/bold green]")
    
                    else:
                        console.print("[yellow]Установите pyperclip (pip install pyperclip), чтобы пароли копировались автоматически.[/yellow]")
                        
                    Prompt.ask("Нажмите Enter, чтобы продолжить (и скрыть пароль с экрана)")
                except Exception as e:
                    console.print(f"[bold red]Ошибка генерации: {e}[/bold red]")
                    Prompt.ask("Нажмите Enter")
            else:
                console.print("[bold red]Неверный ID![/bold red]")
                Prompt.ask("Нажмите Enter")

        elif choice == "2":
            console.print("\n[bold cyan]-- Добавление новой записи --[/bold cyan]")
            service = Prompt.ask("Название сервиса (например, Google)")
            login = Prompt.ask("Логин / Email")
            pass_ver = IntPrompt.ask("Версия пароля (по умолчанию 1)", default=1)
            lnth = IntPrompt.ask("Длина пароля (от 8 до 75)", default=16)
            
            if 8 <= lnth <= 75:
                # Используем добавление из вашей библиотеки
                sisi_core._add_new_item(master_key, DB_FILENAME, login, service, pass_ver, lnth)
                console.print("[bold green]✔ Запись успешно добавлена![/bold green]")
            else:
                console.print("[bold red]Длина должна быть от 8 до 75![/bold red]")
            Prompt.ask("Нажмите Enter")

        elif choice == "3":
            if not data["content"]:
                continue
            entry_id = IntPrompt.ask("Введите ID записи для УДАЛЕНИЯ")
            if 0 <= entry_id < len(data["content"]):
                confirm = Prompt.ask(f"[bold red]Вы уверены, что хотите удалить запись ID {entry_id}?[/bold red] (y/n)", choices=["y", "n"], default="n")
                if confirm == "y":
                    # Используем удаление из вашей библиотеки
                    sisi_core._delete_by_id(master_key, DB_FILENAME, entry_id)
                    console.print("[bold green]✔ Запись удалена.[/bold green]")
            else:
                console.print("[bold red]Неверный ID![/bold red]")
            Prompt.ask("Нажмите Enter")

def run():
    clear_screen()
    console.print(Panel.fit("[bold blue]Добро пожаловать в SISI Manager[/bold blue]\n[dim]Надежный детерминированный менеджер паролей[/dim]"))
    
    if not os.path.exists(DB_FILENAME):
        console.print("[yellow]База данных не найдена. Она будет создана при вводе мастер-пароля.[/yellow]")
    
    master_key = getpass.getpass("Введите Мастер-пароль: ")
    
    console.print("[yellow]Расшифровка и проверка ключа...[/yellow]")
    try:
        # Проверяем пароль вызовом функции загрузки из вашей библиотеки
        sisi_core._load_data(master_key, DB_FILENAME)
        main_loop(master_key)
    except ValueError as e:
        if str(e) == "fail":
            console.print("[bold red]❌ Неверный мастер-пароль или файл поврежден![/bold red]")
        else:
            console.print(f"[bold red]❌ Ошибка: {e}[/bold red]")
    except Exception as e:
         console.print(f"[bold red]❌ Неизвестная ошибка: {e}[/bold red]")

if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\nВыход из программы...")

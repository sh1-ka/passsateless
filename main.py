import sisi_core
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, Horizontal
from textual.widgets import Footer, DataTable, Input, Button, Label
from textual.screen import ModalScreen

try:
    import pyperclip
    HAS_CLIPBOARD = True
except ImportError:
    HAS_CLIPBOARD = False


class LoginScreen(ModalScreen):
    """Модальное окно для ввода мастер-пароля."""
    BINDINGS = [Binding("escape", "quit_app", "Quit")]

    def compose(self) -> ComposeResult:
        with Vertical(classes="dialog"):
            with Vertical(classes="dialog_content") as dialog:
                dialog.border_title = " Authentication "
                yield Label("Введите Master Key", classes="dialog_title")
                yield Input(password=True, id="master_key")

    def on_mount(self):
        self.query_one("#master_key").focus()

    def on_input_submitted(self, event: Input.Submitted):
        if event.input.id == "master_key":
            self.dismiss(event.value)

    def action_quit_app(self):
        self.app.exit()


class ConfirmDeleteScreen(ModalScreen):
    """Модальное окно подтверждения удаления."""
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(self, service_name: str, item_id: int):
        super().__init__()
        self.service_name = service_name
        self.item_id = item_id

    def compose(self) -> ComposeResult:
        with Vertical(classes="dialog"):
            with Vertical(classes="dialog_content") as dialog:
                dialog.border_title = " Confirm Deletion "
                yield Label(f"Удалить запись '{self.service_name}'?", classes="dialog_title")
                with Horizontal(classes="buttons"):
                    yield Button("Удалить", id="btn_delete", classes="btn-error")
                    yield Button("Отмена", id="btn_cancel", classes="btn-primary")

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn_delete":
            self.dismiss(self.item_id)
        else:
            self.dismiss(None)

    def action_cancel(self):
        self.dismiss(None)


class AddItemScreen(ModalScreen):
    """Модальное окно добавления новой записи."""
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def compose(self) -> ComposeResult:
        with Vertical(classes="dialog"):
            with Vertical(classes="dialog_content") as dialog:
                dialog.border_title = " New Record "
                
                # Поле Service
                yield Label("Service / Название", classes="input-label")
                yield Input(placeholder="например, github", id="input_service")
                
                # Поле Login
                yield Label("Login / Email", classes="input-label")
                yield Input(placeholder="например, user@mail.com", id="input_login")
                
                # Горизонтальный блок для чисел
                with Horizontal(id="num_inputs"):
                    with Vertical(classes="half_input_col"):
                        yield Label("Version", classes="input-label")
                        yield Input(value="0", id="input_ver")
                    with Vertical(classes="half_input_col"):
                        yield Label("Length", classes="input-label")
                        yield Input(value="15", id="input_len")
                        
                with Horizontal(classes="buttons"):
                    yield Button("Сохранить", id="btn_save", classes="btn-success")
                    yield Button("Отмена", id="btn_cancel", classes="btn-primary")

    def on_mount(self):
        self.query_one("#input_service").focus()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn_cancel":
            self.dismiss(None)
        elif event.button.id == "btn_save":
            self._submit_data()

    def action_cancel(self):
        self.dismiss(None)

    def _submit_data(self):
        service = self.query_one("#input_service").value.strip()
        login = self.query_one("#input_login").value.strip()
        try:
            ver = int(self.query_one("#input_ver").value)
            length = int(self.query_one("#input_len").value)
            if not service or not login:
                raise ValueError("Пустые поля")
        except ValueError:
            self.app.notify("Ошибка ввода! Проверьте данные.", severity="error")
            return
        
        self.dismiss({"service": service, "login": login, "pass_ver": ver, "lnth": length})

class ShowPasswordScreen(ModalScreen):
    """Модальное окно показа пароля. Пароль генерируется только по нажатию на глазок."""
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(self, master_key: str, item: dict):
        super().__init__()
        self.master_key = master_key
        self.item = item
        self.generated_pwd = None

    def compose(self) -> ComposeResult:
        with Vertical(classes="dialog"):
            with Vertical(classes="dialog_content") as dialog:
                dialog.border_title = f" {self.item['service']} "
                yield Label(f"Login: {self.item['login']}", classes="dialog_title")
                with Horizontal(id="pwd_row"):
                    yield Input(
                        value="•" * 16,
                        disabled=True,
                        id="pwd_field",
                    )
                    yield Button("◉", id="btn_show", classes="btn-eye")
                with Horizontal(classes="buttons"):
                    yield Button("Копировать", id="btn_copy", classes="btn-primary")
                    yield Button("Закрыть", id="btn_close", classes="btn-primary")

    def on_mount(self):
        self.query_one("#btn_show").focus()

    def _ensure_generated(self) -> str:
        if self.generated_pwd is None:
            self.generated_pwd = sisi_core.generate_password(
                self.master_key,
                self.item["login"],
                self.item["service"],
                self.item["pass_ver"],
                self.item["lnth"],
            )
        return self.generated_pwd

    def on_button_pressed(self, event: Button.Pressed):
        field = self.query_one("#pwd_field", Input)

        if event.button.id == "btn_show":
            if field.value.startswith("•"):
                pwd = self._ensure_generated()
                field.value = pwd
                event.button.label = "◎"
            else:
                field.value = "•" * 16
                event.button.label = "◉"

        elif event.button.id == "btn_copy":
            pwd = self._ensure_generated()
            if HAS_CLIPBOARD:
                pyperclip.copy(pwd)
                self.app.notify(f"Пароль для {self.item['service']} скопирован!", timeout=3)
            else:
                self.app.notify(f"Пароль: {pwd}", timeout=10)

        elif event.button.id == "btn_close":
            self.dismiss()

    def action_cancel(self):
        self.dismiss()

class SisiApp(App):
    """Основной класс приложения в стиле киберпанк/Posting."""
    
    CSS = """
    /* --- ЦВЕТОВАЯ ПАЛИТРА --- */
    $magenta: #d75fcf;
    $cyan: #00ffd7;
    $text-main: #e0e0e0;
    $text-muted: #8a8a8a;
    
    /* 1. ГЛОБАЛЬНАЯ ПРОЗРАЧНОСТЬ */
    Screen {
        background: #000000;
        color: $text-main;
    }
    App, Vertical, Horizontal {
        background: transparent; 
        color: $text-main;
    }

    /* 2. ГЛАВНОЕ ОКНО */
    #main_container {
        border: round rgba(215, 95, 207, 0.8);
        height: 1fr;
        margin: 1 2;
        background: transparent; 
    }

    /* 3. ФУТЕР (Шорткаты) */
    Footer {
        background: transparent;
        padding-left: 2;
        padding-right: 2;
    }
    Footer > .footer--highlight, 
    Footer > .footer--highlight:hover,
    Footer > .footer--key, 
    Footer > .footer--highlight-key,
    Footer > .footer--description {
        background: transparent; 
    }
    Footer > .footer--key, 
    Footer > .footer--highlight-key {
        color: $magenta;
        text-style: bold;
    }
    Footer > .footer--description {
        color: $text-main;
    }

    /* 4. ТАБЛИЦА */
    DataTable {
        background: transparent;
        border: none;
        padding: 0 1;
    }
    /* Делаем прозрачными четные и нечетные строки, чтобы убрать черный фон */
    DataTable > .datatable--odd-row,
    DataTable > .datatable--even-row,
    DataTable > .datatable--data-row {
        background: transparent;
    }
    DataTable > .datatable--header {
        background: rgba(43, 37, 74, 0.5);
        color: $text-main;
        text-style: bold;
    }
    DataTable > .datatable--cursor {
        background: rgba(0, 255, 215, 0.15);
        color: $cyan;
        text-style: bold;
    }

    /* 5. МОДАЛЬНЫЕ ОКНА (Эффект матового стекла) */
    .dialog {
        align: center middle;
        background: rgba(0, 0, 0, 0.4);
    }
    .dialog_content {
        border: round $magenta;
        background: #000000;  
        padding: 1 2;
        width: 60;
        height: auto;
    }

    /* 6. ПОЛЯ ВВОДА И ПОДПИСИ */
    .input-label {
        color: $cyan;
        text-style: bold;
        padding-left: 1;
        background: transparent;
    }
    Input {
        border: tall rgba(43, 37, 74, 0.6);
        background: transparent;
        margin-bottom: 1;
        color: $text-main;
    }
    Input:focus {
        border: tall $magenta;
        background: rgba(215, 95, 207, 0.05); 
    }
    #num_inputs {
        height: auto;
        margin-bottom: 1;
        background: transparent;
    }

    #pwd_row {
    height: 3;
    align: left middle;
    margin-bottom: 1;
    background: transparent;
    }
    #pwd_row Input {
        width: 1fr;
        height: 3;
        margin: 0 1 0 0;
    }
    .btn-eye {
        height: 3;
        width: 5;
        min-width: 5;
        margin: 0;
        border: round rgba(0, 255, 215, 0.5);
        color: $cyan;
    }
    .btn-eye:focus, .btn-eye:hover {
        border: round $cyan;
        background: rgba(0, 255, 215, 0.15);
    }
    .half_input_col {
        width: 1fr;
        height: auto;
        padding-right: 1;
        background: transparent;
    }

    /* 7. КНОПКИ (Контурные и прозрачные) */
    .buttons {
        height: auto;
        align: center middle;
        margin-top: 1;
        background: transparent;
    }
    Button {
        margin: 0 2;
        height: 3;
        min-width: 22;
        text-style: bold;
        background: transparent; 
    }
    
    /* Кнопка "Отмена" */
    .btn-primary {
        border: round rgba(80, 70, 120, 0.6);
        color: $text-muted;
    }
    .btn-primary:focus, .btn-primary:hover {
        border: round #6c5da8;
        background: rgba(108, 93, 168, 0.3);
        color: white;
    }

    /* Кнопка "Сохранить" */
    .btn-success {
        border: round $magenta;
        color: $magenta;
    }
    .btn-success:focus, .btn-success:hover {
        border: round $magenta;
        background: rgba(215, 95, 207, 0.2);
        color: #ff85fa;
    }

    /* Кнопка "Удалить" */
    .btn-error {
        border: round #af005f;
        color: #ff3385;
    }
    .btn-error:focus, .btn-error:hover {
        border: round #d7005f;
        background: rgba(215, 0, 95, 0.2);
        color: #ff66a3;
    }
    """

    BINDINGS = [
        Binding("a", "add_item", "Add"),
        Binding("d", "delete_item", "Delete"),
        Binding("g", "generate_pass", "Copy"),
        Binding("s", "toggle_show", "Show/Hide"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self.master_key = None
        self.filename = "sisi.enc"
        self.db_data = {"content": []}
        self.revealed_rows = set()   
        self.pwd_cache = {}          

    def compose(self) -> ComposeResult:
        with Vertical(id="main_container"):
            yield DataTable(id="pass_table")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "Sisi Password Manager"
        
        container = self.query_one("#main_container")
        container.border_title = " Sisi Password Manager "
        container.border_subtitle = " v1.0.0 "
        
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = False
        table.add_column("ID", key="id")
        table.add_column("Service", key="service")
        table.add_column("Login", key="login")
        table.add_column("Ver", key="ver")
        table.add_column("Len", key="len")
        table.add_column("Password", key="password", width=40)
        
        self.push_screen(LoginScreen(), self.check_login)

    def check_login(self, master_key: str):
        if not master_key:
            self.exit()
            return
            
        self.master_key = master_key
        try:
            self.db_data = sisi_core._load_data(self.master_key, self.filename)
            self.refresh_table()
        except ValueError:
            self.notify("Неверный Master Key или файл поврежден!", severity="error")
            self.push_screen(LoginScreen(), self.check_login)

    def refresh_table(self):
        table = self.query_one(DataTable)
        table.clear()
        self.revealed_rows = set()
        self.pwd_cache = {}
        self.db_data = sisi_core._load_data(self.master_key, self.filename)
        for i, item in enumerate(self.db_data["content"]):
            table.add_row(
                str(i),
                item["service"],
                item["login"],
                str(item["pass_ver"]),
                str(item["lnth"]),
                "•" * 10,
                key=str(i),
            )

    def action_add_item(self):
        self.push_screen(AddItemScreen(), self.handle_add)

    def handle_add(self, data):
        if data:
            sisi_core._add_new_item(
                self.master_key, 
                self.filename, 
                data["login"], 
                data["service"], 
                data["pass_ver"], 
                data["lnth"]
            )
            self.refresh_table()
            self.notify(f"Запись {data['service']} добавлена", severity="information")

    def action_show_pass(self):
        table = self.query_one(DataTable)
        try:
            row_idx = table.cursor_coordinate.row
            item = self.db_data["content"][row_idx]
            self.push_screen(ShowPasswordScreen(self.master_key, item))
        except Exception:
            self.notify("Выберите запись", severity="error")

    def action_delete_item(self):
        table = self.query_one(DataTable)
        try:
            row_idx = table.cursor_coordinate.row
            item = self.db_data["content"][row_idx]
            self.push_screen(ConfirmDeleteScreen(item["service"], row_idx), self.handle_delete)
        except Exception:
            self.notify("Сначала выберите запись", severity="error")

    def handle_delete(self, item_id):
        if item_id is not None:
            sisi_core._delete_by_id(self.master_key, self.filename, item_id)
            self.refresh_table()
            self.notify("Запись удалена", severity="warning")

    def action_generate_pass(self):
        table = self.query_one(DataTable)
        try:
            row_idx = table.cursor_coordinate.row
            item = self.db_data["content"][row_idx]
            pwd = self.pwd_cache.get(row_idx)
            
            if pwd is None:
                pwd = sisi_core.generate_password(
                    self.master_key, item["login"], item["service"],
                    item["pass_ver"], item["lnth"],
                )

            if HAS_CLIPBOARD:
                pyperclip.copy(pwd)
                self.notify(f"Пароль для {item['service']} скопирован в буфер!", timeout=3)
            else:
                self.notify(f"Пароль: {pwd}", timeout=10)
        except Exception:
            self.notify("Выберите запись для генерации", severity="error")

    def action_toggle_show(self):
        table = self.query_one(DataTable)
        try:
            row_idx = table.cursor_coordinate.row
            item = self.db_data["content"][row_idx]
        except Exception:
            self.notify("Выберите запись", severity="error")
            return

        row_key = str(row_idx)
        if row_idx in self.revealed_rows:
            
            self.revealed_rows.discard(row_idx)
            table.update_cell(row_key, "password", "•" * 10)
            
            
            if row_idx in self.pwd_cache:
                del self.pwd_cache[row_idx]
        else:
            pwd = self.pwd_cache.get(row_idx)
            if pwd is None:
                pwd = sisi_core.generate_password(
                    self.master_key, item["login"], item["service"],
                    item["pass_ver"], item["lnth"],
                )
                self.pwd_cache[row_idx] = pwd
            self.revealed_rows.add(row_idx)
            table.update_cell(row_key, "password", pwd)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        self.action_toggle_show()

if __name__ == "__main__":
    app = SisiApp()
    app.run()

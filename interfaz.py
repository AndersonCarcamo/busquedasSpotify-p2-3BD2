import tkinter as tk
from tkinter import messagebox, ttk
from Parser import MusicSearch  


ALL_BLOCKS = ["blocks1000", "blocks5000", "blocks10000"]
ALL_COLUMNS = ["doc_id", "title", "artist", "album", "release_date", "similarity"]
POSTGRES_DB_OPTIONS = ["songs1000", "songs5000", "songs10000"]

class MusicSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Music Search")
        self.root.configure(background="#282828")
        self.root.geometry("1000x850")

        # Estilos de colores y fuentes
        bg_color = "#444444"
        fg_color = "#ffffff"
        button_color = "#336699"
        entry_color = "#555555"
        font_style = ("Arial", 12)
        title_font = ("Arial", 14, "bold")

        # Titulo
        title_label = tk.Label(root, text="Búsqueda SPIMI", font=("Arial", 18, "bold"), bg="#282828", fg="#ffffff")
        title_label.pack(pady=(15, 10))



        # Botón para abrir ventana de conexión
        self.connect_button = tk.Button(root, text="Conectar a PostgreSQL", command=self.open_connection_window, bg=button_color, fg=fg_color, font=title_font)
        self.connect_button.pack(pady=10)

        # Selector de fuente de datos
        source_frame = tk.Frame(root, bg="#282828")
        source_frame.pack(pady=(10, 20))

        # Crear los botones de SPIMI y PostgreSQL como atributos de la clase
        self.spimi_button = tk.Button(source_frame, text="SPIMI", command=lambda: self.toggle_source(False), bg="#336699", fg="#ffffff")
        self.spimi_button.pack(side=tk.LEFT, padx=5)

        self.postgres_button = tk.Button(source_frame, text="PostgreSQL", command=lambda: self.toggle_source(True), bg="#336699", fg="#ffffff")
        self.postgres_button.pack(side=tk.LEFT, padx=5)

        # Selección de carpeta de bloques (solo visible cuando se usa SPIMI)
        self.block_frame = tk.Frame(root, bg=bg_color)
        self.block_frame.pack(pady=(10, 10), fill=tk.X, padx=15)
        tk.Label(self.block_frame, text="Seleccione bloques(spimi):", font=title_font, bg=bg_color, fg=fg_color).pack(side=tk.LEFT, padx=5)
        self.block_var = tk.StringVar(value=ALL_BLOCKS[0])  # Valor inicial: "blocks1000"

        for block in ALL_BLOCKS:
            tk.Radiobutton(
                self.block_frame, 
                text=block, 
                variable=self.block_var, 
                value=block, 
                command=self.change_blocks, 
                bg=bg_color, 
                fg=fg_color, 
                selectcolor=entry_color, 
                font=font_style
            ).pack(side=tk.LEFT, padx=5)
                
        # Frame para elegir base de datos PostgreSQL
        self.postgres_db_frame = tk.Frame(root, bg=bg_color )
        self.postgres_db_frame.pack(pady=(10, 10), fill=tk.X, padx=15)
        tk.Label(self.postgres_db_frame, text="Seleccione base de datos(PostgreSQL):", font=title_font,  bg=bg_color, fg=fg_color).pack(side=tk.LEFT, padx=5)
        # Crear botones de base de datos de PostgreSQL
        self.db_var = tk.StringVar(value=POSTGRES_DB_OPTIONS[0])  # Valor inicial
        for db in POSTGRES_DB_OPTIONS:
            tk.Radiobutton(
                self.postgres_db_frame, 
                text=db, 
                variable=self.db_var, 
                value=db, 
                command=self.change_postgres_db, 
                bg=bg_color, 
                fg=fg_color, 
                selectcolor=entry_color, 
                font=font_style
            ).pack(side=tk.LEFT, padx=5)
    

        # Crear entrada para la consulta
        query_frame = tk.Frame(root, bg=bg_color)
        query_frame.pack(pady=15, fill=tk.X, padx=15)
        
        tk.Label(query_frame, text="Enter Query:", font=title_font, bg=bg_color, fg=fg_color).pack(side=tk.LEFT, padx=10)
        self.query_entry = tk.Entry(query_frame, width=50, bg=entry_color, fg=fg_color, font=font_style)
        self.query_entry.pack(side=tk.LEFT, padx=(10, 20), fill=tk.X, expand=True)

        # Botón para realizar la búsqueda
        self.search_button = tk.Button(root, text="Search", command=self.perform_search, bg=button_color, fg=fg_color, font=title_font)
        self.search_button.pack(pady=10)

        # Crear el Treeview para mostrar los resultados
        self.results_tree = ttk.Treeview(root)
        self.results_tree.pack(pady=10, fill=tk.BOTH, expand=True, padx=15)

        # Scrollbars para el Treeview
        self.scroll_y = ttk.Scrollbar(root, orient="vertical", command=self.results_tree.yview)
        self.scroll_y.pack(side="right", fill="y")
        self.scroll_x = ttk.Scrollbar(root, orient="horizontal", command=self.results_tree.xview)
        self.scroll_x.pack(side="bottom", fill="x")
        
        self.results_tree.configure(yscrollcommand=self.scroll_y.set, xscrollcommand=self.scroll_x.set)

        # Label para mostrar tiempo de ejecución
        self.time_label = tk.Label(root, text="", font=("Arial", 10), bg="#282828", fg="#ffffff")
        self.time_label.pack(pady=10)

        # Crear Frame para el texto de ejemplo y el botón de copiar
        example_frame = tk.Frame(root, bg="#282828")
        example_frame.pack(pady=(10, 20))

        example_text = "Copie y pegue este ejemplo: select * from Audio where content liketo 'mayor que yo' limit 5"
        self.example_label = tk.Label(example_frame, text=example_text, font=("Arial", 10), bg="#282828", fg="#bbbbbb")
        self.example_label.pack(side=tk.LEFT)

        # Botón de copiar
        self.copy_button = tk.Button(example_frame, text="Copiar", command=self.copy_example_to_clipboard, bg="#336699", fg="#ffffff", font=("Arial", 10))
        self.copy_button.pack(side=tk.LEFT, padx=(10, 0))

        # Conectar con el motor de búsqueda
        self.search_engine = MusicSearch("./blocks1000/")

    def change_postgres_db(self):
        """Cambia la base de datos de PostgreSQL seleccionada."""
        selected_db = self.db_var.get()
        self.search_engine = MusicSearch(f"./{selected_db}/", use_db=True)
        messagebox.showinfo("Cambio de base de datos", f"Ahora estás usando la base de datos {selected_db}.")

    def change_blocks(self):
        """Cambia la carpeta de bloques activos en el motor de búsqueda."""
        selected_block_folder = self.block_var.get()
        self.search_engine = MusicSearch(f"./{selected_block_folder}/")
        #messagebox.showinfo("Cambio de bloques", f"Ahora estás usando los bloques de: {selected_block_folder}")
    
    def toggle_source(self, use_db):
        """Cambiar entre el uso de SPIMI y PostgreSQL."""
        self.search_engine = MusicSearch(f"./{self.block_var.get()}/", use_db=use_db)
        source = 'PostgreSQL' if use_db else 'SPIMI'
        messagebox.showinfo("Cambio de fuente", f"Ahora estás usando {source} como fuente de datos.")
        # Cambiar colores de los botones para indicar el estado actual
        self.update_source_buttons(source)

    def update_source_buttons(self, source):
        if source == 'SPIMI':
            self.spimi_button.config(bg="#00AA00")  # Color verde para SPIMI
            self.postgres_button.config(bg="#336699")  # Color azul para PostgreSQL
        else:
            self.spimi_button.config(bg="#336699")
            self.postgres_button.config(bg="#00AA00")
    def open_connection_window(self):
        # Crear una nueva ventana para ingresar las credenciales
        connection_window = tk.Toplevel(self.root)
        connection_window.title("Conectar a PostgreSQL")
        connection_window.geometry("400x500")

        # Valores predeterminados
        default_dbname = "proyect2"
        default_user = "postgres"
        default_password = "3215932112"
        default_host = "localhost"
        default_port = "5432"

        # Crear campos para las credenciales con valores predeterminados
        tk.Label(connection_window, text="Base de datos:").pack(pady=5)
        self.db_name_entry = tk.Entry(connection_window)
        self.db_name_entry.insert(0, default_dbname)  # Insertar valor predeterminado
        self.db_name_entry.pack(pady=5)

        tk.Label(connection_window, text="Usuario:").pack(pady=5)
        self.db_user_entry = tk.Entry(connection_window)
        self.db_user_entry.insert(0, default_user)  # Insertar valor predeterminado
        self.db_user_entry.pack(pady=5)

        tk.Label(connection_window, text="Contraseña:").pack(pady=5)
        self.db_password_entry = tk.Entry(connection_window, show="*")
        self.db_password_entry.insert(0, default_password)  # Insertar valor predeterminado
        self.db_password_entry.pack(pady=5)

        tk.Label(connection_window, text="Host:").pack(pady=5)
        self.db_host_entry = tk.Entry(connection_window)
        self.db_host_entry.insert(0, default_host)  # Insertar valor predeterminado
        self.db_host_entry.pack(pady=5)

        tk.Label(connection_window, text="Puerto:").pack(pady=5)
        self.db_port_entry = tk.Entry(connection_window)
        self.db_port_entry.insert(0, default_port)  # Insertar valor predeterminado
        self.db_port_entry.pack(pady=5)

        # Botón para conectar
        connect_button = tk.Button(connection_window, text="Conectar", command=self.connect_to_postgres)
        connect_button.pack(pady=20)
    def connect_to_postgres(self):
        # Obtener valores de los campos de la ventana de conexión
        dbname = self.db_name_entry.get()
        user = self.db_user_entry.get()
        password = self.db_password_entry.get()
        host = self.db_host_entry.get()
        port = self.db_port_entry.get()

        # Pasar las credenciales a la clase MusicSearch
        self.search_engine = MusicSearch(use_db=True, db_params={
            "dbname": dbname,
            "user": user,
            "password": password,
            "host": host,
            "port": port
        })

        # Cerrar la ventana de conexión
        messagebox.showinfo("Conexión exitosa", "Conectado a PostgreSQL exitosamente.")
    def perform_search(self):
        query = self.query_entry.get()

        if not query:
            messagebox.showerror("Error", "Por favor, ingrese una consulta.")
            return
        
        # Realizar la búsqueda
        results , tiempo_ejecucion = self.search_engine.search(query)
        parsed_query = self.search_engine.queryparser.parse_query(query)
        selected_columns = parsed_query["columns"]

        # Mostrar el tiempo de ejecución
        self.time_label.config(text=f"Tiempo de ejecución: {tiempo_ejecucion:.4f} milisegundos")
    
        if '*' in selected_columns:
            selected_columns = ALL_COLUMNS

        # Limpiar las columnas previas
        self.results_tree.delete(*self.results_tree.get_children())
        for col in self.results_tree["columns"]:
            self.results_tree.heading(col, text="")  # Borrar encabezados anteriores
            self.results_tree.column(col, width=0)  # Borrar las columnas anteriores
        
        # Configurar las columnas de acuerdo al SELECT
        self.results_tree["columns"] = selected_columns
        for col in selected_columns:
            self.results_tree.heading(col, text=col.capitalize())  # Añadir encabezados
            self.results_tree.column(col, anchor=tk.W, width=150)

        # Insertar los resultados
        if results:
            for result in results:
                row = [result.get(col, "N/A") for col in selected_columns]
                self.results_tree.insert("", tk.END, values=row)
        else:
            self.results_tree.insert("", tk.END, values=["No results found."] * len(selected_columns))

    def copy_example_to_clipboard(self):
        example_text = "select * from Audio where content liketo 'mayor que yo' limit 5"
        self.root.clipboard_clear()  # Limpiar el portapapeles
        self.root.clipboard_append(example_text)  # Agregar el texto al portapapeles


# Inicializar la aplicación
root = tk.Tk()
app = MusicSearchApp(root)
root.mainloop()

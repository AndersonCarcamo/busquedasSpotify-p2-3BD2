import tkinter as tk
from tkinter import messagebox, ttk
from Parser import MusicSearch  # Asegúrate de importar tu clase MusicSearch aquí

block_folder = './blocks/'

class MusicSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Music Search")
        self.root.configure(background="#282828")
        self.root.geometry("800x600")


        # Estilos de colores y fuentes
        bg_color = "#444444"
        fg_color = "#ffffff"
        button_color = "#336699"
        entry_color = "#555555"
        font_style = ("Arial", 12)
        title_font = ("Arial", 14, "bold")

        # Título de la aplicación
        title_label = tk.Label(root, text="Búsqueda SPIMI", font=("Arial", 18, "bold"), bg="#282828", fg="#ffffff")
        title_label.pack(pady=(15, 10))

        # Crear entrada para la consulta
        query_frame = tk.Frame(root, bg=bg_color)
        query_frame.pack(pady=15, fill=tk.X, padx=15)
        
        tk.Label(query_frame, text="Enter Query:", font=title_font, bg=bg_color, fg=fg_color).pack(side=tk.LEFT, padx=5)
        self.query_entry = tk.Entry(query_frame, width=50, bg=entry_color, fg=fg_color, font=font_style)
        self.query_entry.pack(side=tk.LEFT, padx=10)

        # Entrada para el valor de K
        k_frame = tk.Frame(root, bg=bg_color)
        k_frame.pack(pady=5, fill=tk.X, padx=15)

        tk.Label(k_frame, text="Enter number of results (K):", font=title_font, bg=bg_color, fg=fg_color).pack(side=tk.LEFT, padx=5)
        self.k_entry = tk.Entry(k_frame, width=10, bg=entry_color, fg=fg_color, font=font_style, justify="left")
        self.k_entry.pack(side=tk.LEFT, padx=10)

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

        # Crear Frame para el texto de ejemplo y el botón de copiar
        example_frame = tk.Frame(root, bg="#282828")
        example_frame.pack(pady=(10, 20))

        example_text = "Copie y pegue este ejemplo: select title, artist , lyrics from Audio where content liketo 'yea you just can't walk away"
        self.example_label = tk.Label(example_frame, text=example_text, font=("Arial", 10), bg="#282828", fg="#bbbbbb")
        self.example_label.pack(side=tk.LEFT)

        # Botón de copiar
        self.copy_button = tk.Button(example_frame, text="Copiar", command=self.copy_example_to_clipboard, bg="#336699", fg="#ffffff", font=("Arial", 10))
        self.copy_button.pack(side=tk.LEFT, padx=(10, 0))

        # Conectar con el motor de búsqueda
        self.search_engine = MusicSearch()


    def perform_search(self):
        query = self.query_entry.get()
        k = self.k_entry.get()

        if not query.strip():
            messagebox.showwarning("Input Error", "Please enter a query.")
            return
        if not k.strip():
            messagebox.showwarning("Input Error", "Please enter a value for K.")
            return
        k = int(k)

        # Realizar la búsqueda
        results = self.search_engine.search(query, top_k=k)
        parsed_query = self.search_engine.queryparser.parse_query(query)
        selected_columns = parsed_query['columns']

        # Limpiar las columnas previas
        self.results_tree.delete(*self.results_tree.get_children())
        for col in self.results_tree["columns"]:
            self.results_tree.heading(col, text="")
            self.results_tree.column(col, width=0)
        
        # Configurar las columnas de acuerdo al SELECT
        self.results_tree["columns"] = selected_columns
        for col in selected_columns:
            self.results_tree.heading(col, text=col.capitalize())
            self.results_tree.column(col, anchor=tk.W, width=150)

        # Insertar los resultados
        if results:
            for result in results:
                row = [result.get(col, "N/A") for col in selected_columns]
                self.results_tree.insert("", tk.END, values=row)
        else:
            self.results_tree.insert("", tk.END, values=["No results found."] * len(selected_columns))
    def copy_example_to_clipboard(self):
        example_text = "SELECT title, artist FROM Audio WHERE content LIKETO 'yea you just can't walk away'"
        self.root.clipboard_clear()  # Limpiar el portapapeles
        self.root.clipboard_append(example_text)  # Agregar el texto al portapapeles
        messagebox.showinfo("Copiado", "Texto de ejemplo copiado al portapapeles.")

# Inicializar la aplicación
root = tk.Tk()
app = MusicSearchApp(root)
root.mainloop()

import tkinter as tk
from tkinter import messagebox, ttk
from tkinter.filedialog import askopenfilename  # Para seleccionar archivos
from Parser import MusicSearch  
import pandas as pd
from Proyecto3.extractFeatures.busquedas import KNN_Sequential , KNN_RTree , KNN_HighD
from setting.extract import extract_mfcc , load_batches


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
        self.bg_color = "#444444" 
        self.fg_color = "#ffffff"
        self.button_color = "#336699"
        self.entry_color = "#555555"
        self.font_style = ("Arial", 12)
        self.title_font = ("Arial", 14, "bold")

        # Crear el Notebook (la barra de pestañas)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Crear los Frames para cada pestaña
        self.main_frame = tk.Frame(self.notebook, bg="#282828")  # Fondo oscuro para la pestaña principal
        self.upload_frame = tk.Frame(self.notebook, bg="#282828")  # Fondo más claro para la pestaña de carga

        # Añadir los Frames al Notebook
        self.notebook.add(self.main_frame, text="Main")
        self.notebook.add(self.upload_frame, text="Upload")
        
        # Añadir widgets dentro del main_frame
        self.create_main_frame()
        self.create_upload_frame()

    def create_main_frame(self):

        # Botón para abrir ventana de conexión
        self.connect_button = tk.Button(self.main_frame, text="Conectar a PostgreSQL", command=self.open_connection_window, bg=self.button_color, fg=self.fg_color, font=self.title_font)
        self.connect_button.pack(pady=10)

        # Selector de fuente de datos
        source_frame = tk.Frame(self.main_frame, bg="#282828")
        source_frame.pack(pady=(10, 20))

        # Crear los botones de SPIMI y PostgreSQL como atributos de la clase
        self.spimi_button = tk.Button(source_frame, text="SPIMI", command=lambda: self.toggle_source(False), bg="#336699", fg="#ffffff")
        self.spimi_button.pack(side=tk.LEFT, padx=5)

        self.postgres_button = tk.Button(source_frame, text="PostgreSQL", command=lambda: self.toggle_source(True), bg="#336699", fg="#ffffff")
        self.postgres_button.pack(side=tk.LEFT, padx=5)

        # Selección de carpeta de bloques (solo visible cuando se usa SPIMI)
        self.block_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        self.block_frame.pack(pady=(10, 10), fill=tk.X, padx=15)
        tk.Label(self.block_frame, text="Seleccione bloques(spimi):", font=self.title_font, bg=self.bg_color, fg=self.fg_color).pack(side=tk.LEFT, padx=5)
        self.block_var = tk.StringVar(value=ALL_BLOCKS[0])  # Valor inicial: "blocks1000"

        for block in ALL_BLOCKS:
            tk.Radiobutton(
                self.block_frame, 
                text=block, 
                variable=self.block_var, 
                value=block, 
                command=self.change_blocks, 
                bg=self.bg_color, 
                fg=self.fg_color, 
                selectcolor=self.entry_color, 
                font=self.font_style
            ).pack(side=tk.LEFT, padx=5)
                
        # Frame para elegir base de datos PostgreSQL
        self.postgres_db_frame = tk.Frame(self.main_frame, bg=self.bg_color )
        self.postgres_db_frame.pack(pady=(10, 10), fill=tk.X, padx=15)
        tk.Label(self.postgres_db_frame, text="Seleccione base de datos(PostgreSQL):", font=self.title_font,  bg=self.bg_color, fg=self.fg_color).pack(side=tk.LEFT, padx=5)
        # Crear botones de base de datos de PostgreSQL
        self.db_var = tk.StringVar(value=POSTGRES_DB_OPTIONS[0])  # Valor inicial
        for db in POSTGRES_DB_OPTIONS:
            tk.Radiobutton(
                self.postgres_db_frame, 
                text=db, 
                variable=self.db_var, 
                value=db, 
                command=self.change_postgres_db, 
                bg=self.bg_color, 
                fg=self.fg_color, 
                selectcolor=self.entry_color, 
                font=self.font_style
            ).pack(side=tk.LEFT, padx=5)
    

        # Crear entrada para la consulta
        query_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        query_frame.pack(pady=15, fill=tk.X, padx=15)
        
        tk.Label(query_frame, text="Enter Query:", font=self.title_font, bg=self.bg_color, fg=self.fg_color).pack(side=tk.LEFT, padx=10)
        self.query_entry = tk.Entry(query_frame, width=50, bg=self.entry_color, fg=self.fg_color, font=self.font_style)
        self.query_entry.pack(side=tk.LEFT, padx=(10, 20), fill=tk.X, expand=True)

        # Botón para realizar la búsqueda
        self.search_button = tk.Button(self.main_frame, text="Search", command=self.perform_search, bg=self.button_color, fg=self.fg_color, font=self.title_font)
        self.search_button.pack(pady=10)

        # Crear el Treeview para mostrar los resultados
        self.results_tree = ttk.Treeview(self.main_frame)
        self.results_tree.pack(pady=10, fill=tk.BOTH, expand=True, padx=15)

        # Scrollbars para el Treeview
        self.scroll_y = ttk.Scrollbar(self.main_frame, orient="vertical", command=self.results_tree.yview)
        self.scroll_y.pack(side="right", fill="y")
        self.scroll_x = ttk.Scrollbar(self.main_frame, orient="horizontal", command=self.results_tree.xview)
        self.scroll_x.pack(side="bottom", fill="x")
        
        self.results_tree.configure(yscrollcommand=self.scroll_y.set, xscrollcommand=self.scroll_x.set)

        # Label para mostrar tiempo de ejecución
        self.time_label = tk.Label(self.main_frame, text="", font=("Arial", 10), bg="#282828", fg="#ffffff")
        self.time_label.pack(pady=10)

        # Crear Frame para el texto de ejemplo y el botón de copiar
        example_frame = tk.Frame(self.main_frame, bg="#282828")
        example_frame.pack(pady=(10, 20))

        example_text = "Copie y pegue este ejemplo: select * from Audio where content liketo 'mayor que yo' limit 5"
        self.example_label = tk.Label(example_frame, text=example_text, font=("Arial", 10), bg="#282828", fg="#bbbbbb")
        self.example_label.pack(side=tk.LEFT)

        # Botón de copiar
        self.copy_button = tk.Button(example_frame, text="Copiar", command=self.copy_example_to_clipboard, bg="#336699", fg="#ffffff", font=("Arial", 10))
        self.copy_button.pack(side=tk.LEFT, padx=(10, 0))

        # Conectar con el motor de búsqueda
        self.search_engine = MusicSearch("./blocks1000/")
    def create_upload_frame(self):
        """Crea los elementos de la pestaña de carga de archivos"""
        # Etiqueta
        upload_label = tk.Label(self.upload_frame, text="Subir archivo de canción", font=("Arial", 14, "bold"), bg="#444444", fg="#ffffff")
        upload_label.pack(pady=20)

        # Botón para seleccionar el archivo
        self.upload_button = tk.Button(self.upload_frame, text="Subir archivo", command=self.upload_file, bg="#336699", fg="#ffffff", font=("Arial", 12))
        self.upload_button.pack(pady=10)

        # Crear un Label para la entrada de la cantidad de batches
        self.batch_label = tk.Label(self.upload_frame, text="Cantidad de canciones :", font=("Arial", 12), bg="#444444", fg="#ffffff")
        self.batch_label.pack(pady=10)

        # Crear un Entry para que el usuario ingrese la cantidad de batches
        self.batch_entry = tk.Entry(self.upload_frame, font=("Arial", 12))
        self.batch_entry.pack(pady=10)

        # Selector de algoritmo k-NN
        self.knn_alg_label = tk.Label(self.upload_frame, text="Seleccione el algoritmo k-NN", font=("Arial", 14, "bold"), bg="#444444", fg="#ffffff")
        self.knn_alg_label.pack(pady=10)

        self.knn_alg_var = tk.StringVar(value="knnsequential")  # Valor por defecto
        knn_algorithms = ["knnsequential_heap", "knnsequential_rango" , "knn_rtree", "knnHighD"]

        # Crear combobox para seleccionar el algoritmo
        self.knn_combobox = ttk.Combobox(self.upload_frame, textvariable=self.knn_alg_var, values=knn_algorithms, state="readonly", font=("Arial", 12))
        self.knn_combobox.pack(pady=10)
        # Crear un Label para la entrada de k
        self.k_label = tk.Label(self.upload_frame, text="Valor de k:", font=("Arial", 12), bg="#444444", fg="#ffffff")
        self.k_entry = tk.Entry(self.upload_frame, font=("Arial", 12))
        
        # Crear un Label para la entrada de m (RTree)
        self.m_label = tk.Label(self.upload_frame, text="Valor de m:", font=("Arial", 12), bg="#444444", fg="#ffffff")
        self.m_entry = tk.Entry(self.upload_frame, font=("Arial", 12))

        #crear un label para la entrada num_bits(knnHighD)
        self.num_bits_label = tk.Label(self.upload_frame, text="Numero de bits:", font=("Arial", 12), bg="#444444", fg="#ffffff")
        self.num_bits_entry = tk.Entry(self.upload_frame, font=("Arial", 12))

        # Función que se llama cuando se cambia el algoritmo seleccionado
        self.knn_combobox.bind("<<ComboboxSelected>>", self.toggle_k_m_entry)
    
        # Botón para realizar la búsqueda
        self.search_button = tk.Button(self.upload_frame, text="Buscar", command=self.perform_knn, bg="#336699", fg="#ffffff", font=("Arial", 12))
        self.search_button.pack(pady=10)

        # Crear el Treeview para mostrar los resultados
        self.result_tree = ttk.Treeview(self.upload_frame, columns=("track_id", "track_title", "artist_name"), show="headings", height=10)
        self.result_tree.pack(pady=10)

        # Definir las columnas del Treeview
        self.result_tree.heading("track_id", text="ID de Canción")
        self.result_tree.heading("track_title", text="Título")
        self.result_tree.heading("artist_name", text="Artista")

        # Ajustar el ancho de las columnas
        self.result_tree.column("track_id", width=100)
        self.result_tree.column("track_title", width=250)
        self.result_tree.column("artist_name", width=200)

        # Inicialmente, ocultamos los Entry de k y m
        self.k_label.pack_forget()
        self.k_entry.pack_forget()
        self.m_label.pack_forget()
        self.m_entry.pack_forget()
        self.num_bits_label.pack_forget()
        self.num_bits_entry.pack_forget()

    def toggle_k_m_entry(self, event):
        if self.knn_alg_var.get() == "knnsequential_heap":
            self.k_label.pack(pady=10)
            self.k_entry.pack(pady=10)
            self.m_label.pack_forget()
            self.m_entry.pack_forget()
            self.num_bits_label.pack_forget()
            self.num_bits_entry.pack_forget()
        elif self.knn_alg_var.get() == "knnsequential_rango":
            self.k_label.pack(pady=10)
            self.k_entry.pack(pady=10)
            self.m_label.pack_forget()
            self.m_entry.pack_forget()
            self.num_bits_label.pack_forget()
            self.num_bits_entry.pack_forget()
        elif self.knn_alg_var.get() == "knn_rtree":
            self.k_label.pack(pady=10)
            self.k_entry.pack(pady=10)
            self.m_label.pack(pady=10)
            self.m_entry.pack(pady=10)
            self.num_bits_label.pack_forget()
            self.num_bits_entry.pack_forget()
        elif self.knn_alg_var.get() == "knnHighD":
            self.k_label.pack(pady=10)
            self.k_entry.pack(pady=10)
            self.m_label.pack_forget()
            self.m_entry.pack_forget()
            self.num_bits_label.pack(pady=10)
            self.num_bits_entry.pack(pady=10)
        else:
            self.k_label.pack_forget()
            self.k_entry.pack_forget()
            self.m_label.pack_forget()
            self.m_entry.pack_forget()
            self.num_bits_label.pack_forget()
            self.num_bits_entry.pack_forget()
    def upload_file(self):
        file_path = askopenfilename(title="Seleccionar archivo de canción", filetypes=[("Audio files", "*.mp3 *.wav")])
        if file_path:
            print(f"Archivo cargado: {file_path}")
            self.extract_feature_vector(file_path)
        else:
            print("No se selecciono ningun archivo.")
    def extract_feature_vector(self, file_path):
        """Extrae el vector característico de un archivo de audio."""
        print(f"Extrayendo vector característico del archivo: {file_path}")
        query_mfcc = extract_mfcc(file_path)

        # Obtener la cantidad de batches del usuario
        try:
            num_songs = int(self.batch_entry.get())
            if num_songs <= 0 or num_songs >= 25001:
                raise ValueError("La cantidad de batches debe estar entre 1 y 25000.")
        except ValueError as e:
            print(f"Error en la entrada de batches: {e}")
            tk.messagebox.showerror("Error", "Por favor, ingrese un número válido para la cantidad de batches.")
            return
        
        collection = load_batches(batchs_folder='Proyecto3/extractFeatures/batchs', num_songs=num_songs)
        self.query_entry = query_mfcc
        self.collection = collection

        self.perform_knn(query_mfcc , collection)

    def perform_knn(self):
        """Realiza el k-NN dependiendo de la selección del usuario"""
        if not hasattr(self, "query_entry") or not hasattr(self, "collection"):
            messagebox.showerror("Error", "Primero debes cargar un archivo.")
            
        query_mfcc = self.query_entry
        collection = self.collection
        
        knn_algorithm = self.knn_alg_var.get()
        if knn_algorithm == "knnsequential_heap":
            # Obtener el valor de k desde el Entry
            try:
                k = int(self.k_entry.get())  # Obtener el valor de k como entero
                print(f"Realizando k-NN secuencial con k={k}...")
            except ValueError:
                print("Valor de k no válido.")
                return

            print("Realizando k-NN secuencial...")
            knn = KNN_Sequential.KNN_Sequential(collection)
            result = knn.knn_heap_query(query_mfcc, k)
            tracks_df = pd.read_csv('setting/raw_tracks.csv')  

            track_ids = [track_id for track_id, _ in result]
            track_ids = [str(int(track_id)) for track_id in track_ids]
            tracks_df['track_id'] = tracks_df['track_id'].astype(str)
            matched_tracks = tracks_df[tracks_df['track_id'].isin(track_ids)]
            
            # Limpiar el Treeview antes de insertar nuevos resultados
            for item in self.result_tree.get_children():
                self.result_tree.delete(item)

            if matched_tracks.empty:
                self.result_tree.insert("", tk.END, values=("No se encontraron coincidencias", "", ""))
            else:
                # Insertar los resultados en el Treeview
                for _, row in matched_tracks.iterrows():
                    self.result_tree.insert("", tk.END, values=(row['track_id'], row['track_title'], row['artist_name']))
        elif knn_algorithm == "knnsequential_rango":
            # Obtener el valor de k desde el Entry
            try:
                r = int(self.k_entry.get())  # Obtener el rango 
                print(f"Realizando k-NN secuencial con r={r}...")
            except ValueError:
                print("Valor de k no válido.")
                return
            print("Realizando k-NN secuencial por rangos ...")
            knn = KNN_Sequential.KNN_Sequential(collection)
            result = knn.range_query(query_mfcc, r)
            tracks_df = pd.read_csv('setting/raw_tracks.csv')

            track_ids = [track_id for track_id, _ in result]
            track_ids = [str(int(track_id)) for track_id in track_ids]
            tracks_df['track_id'] = tracks_df['track_id'].astype(str)
            matched_tracks = tracks_df[tracks_df['track_id'].isin(track_ids)]

            # Limpiar el Treeview antes de insertar nuevos resultados
            for item in self.result_tree.get_children():
                self.result_tree.delete(item)

            if matched_tracks.empty:
                self.result_tree.insert("", tk.END, values=("No se encontraron coincidencias", "", ""))
            else:
                # Insertar los resultados en el Treeview
                for _, row in matched_tracks.iterrows():
                    self.result_tree.insert("", tk.END, values=(row['track_id'], row['track_title'], row['artist_name']))

        elif knn_algorithm == "knn_rtree":
            try:
                k = int(self.k_entry.get())  # Obtener el valor de k como entero
                m = int(self.m_entry.get())  # Obtener el valor de m como entero
                print(f"Realizando k-NN con RTree con k={k} y m={m}...")
            except ValueError:
                print("Valor de k o m no válido.")
                return
            knn = KNN_RTree.KNN_RTree(m, collection)
            result = knn.query(query_mfcc, k)
            tracks_df = pd.read_csv('setting/raw_tracks.csv')

            track_ids = [track_id for track_id, _ in result]
            track_ids = [str(int(track_id)) for track_id in track_ids]
            tracks_df['track_id'] = tracks_df['track_id'].astype(str)
            matched_tracks = tracks_df[tracks_df['track_id'].isin(track_ids)]

            # Limpiar el Treeview antes de insertar nuevos resultados
            for item in self.result_tree.get_children():
                self.result_tree.delete(item)

            if matched_tracks.empty:
                self.result_tree.insert("", tk.END, values=("No se encontraron coincidencias", "", ""))
            else:
                # Insertar los resultados en el Treeview
                for _, row in matched_tracks.iterrows():
                    self.result_tree.insert("", tk.END, values=(row['track_id'], row['track_title'], row['artist_name']))

            
        elif knn_algorithm == "knnHighD":
            try:
                num_bits = int(self.num_bits_entry.get())  # Obtener el valor de num_bits como entero
                k = int(self.k_entry.get())  # Obtener el valor de k como entero
                print(f"Realizando k-NN con HighD con k={k} y num_bits={num_bits}...")
            except ValueError:
                print("Valor de k o num_bits no válido.")
                return
            knn = KNN_HighD.KNN_HighD(num_bits, collection)
            result = knn.knn_query(query_mfcc, k)
            tracks_df = pd.read_csv('setting/raw_tracks.csv')

            track_ids = [track_id for track_id, _ in result]
            track_ids = [str(int(track_id)) for track_id in track_ids]
            tracks_df['track_id'] = tracks_df['track_id'].astype(str)
            matched_tracks = tracks_df[tracks_df['track_id'].isin(track_ids)]

            # Limpiar el Treeview antes de insertar nuevos resultados
            for item in self.result_tree.get_children():
                self.result_tree.delete(item)

            if matched_tracks.empty:
                self.result_tree.insert("", tk.END, values=("No se encontraron coincidencias", "", ""))
            else:
                # Insertar los resultados en el Treeview
                for _, row in matched_tracks.iterrows():
                    self.result_tree.insert("", tk.END, values=(row['track_id'], row['track_title'], row['artist_name']))
        else:
            WindowsError("Algoritmo no encontrado")
    def change_postgres_db(self):
        """Cambia la base de datos de PostgreSQL seleccionada."""
        selected_db = self.db_var.get()
        self.search_engine = MusicSearch(f"./{selected_db}/", use_db=True)
        #messagebox.showinfo("Cambio de base de datos", f"Ahora estás usando la base de datos {selected_db}.")

    def change_blocks(self):
        """Cambia la carpeta de bloques activos en el motor de búsqueda."""
        selected_block_folder = self.block_var.get()
        self.search_engine = MusicSearch(f"./{selected_block_folder}/")
        #messagebox.showinfo("Cambio de bloques", f"Ahora estás usando los bloques de: {selected_block_folder}")
    
    def toggle_source(self, use_db):
        """Cambiar entre el uso de SPIMI y PostgreSQL."""
        self.search_engine = MusicSearch(f"./{self.block_var.get()}/", use_db=use_db)
        source = 'PostgreSQL' if use_db else 'SPIMI'
        #messagebox.showinfo("Cambio de fuente", f"Ahora estás usando {source} como fuente de datos.")
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

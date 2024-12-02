# Proyecto de Índice Invertido y Busquedas por cancion en mp3 sobre canciones de Spotify y 

<details>
    <summary> Sobre la data: </summary>

## Para el Proyecto 2

Se ha utilizado un csv con las canciones obtenido de https://www.kaggle.com/datasets/imuhammad/audio-features-and-lyrics-of-spotify-songs.

El cual contiene un track_id, con su información obtenida como: lyric, album_name, artists, genre, entre otras. 

## Para el Proyecto 3

Se ha usado datos dados encontrados en el repositorio: https://github.com/mdeff/fma/tree/master

Donde se ha descargado el fma_medium.zip con 25k de canciones (algunas de las cuales estaban corrompidas, pero una cantidad insignificante).

Y el raw_tracks.csv que contiene la informacion basada en un track_id, mismo nombre del archivo de la canción.

</details>

<details>
    <summary> Proyecto 2: Construccion de Spimi </summary>

## Introducción
Este proyecto implementa un sistema de búsqueda basado en un índice invertido para una base de datos de letras de canciones. Con un enfoque en eficiencia y accesibilidad, el proyecto incluye una interfaz gráfica para consultas SQL-like, facilitando la interacción con los datos a través de un frontend intuitivo. Además, la implementación fue diseñada para ser comparable en rendimiento con bases de datos robustas como PostgreSQL.

Su importancia se basa en busquedas textuales no exactas. Un ejemplo tenemos un buscador de productor, del cual sabemos su descripción que objeto es o que marca es. Y nos devuelve la busqueda mas parecida a nuestra consulta. Esto resulta importante, porque el usuario no tiene que saber los productos que existen en stock, solo necesita saber su necesidad para poder realizar una consulta eficiente.

## 2. Backend

### Índice Invertido
La base de este sistema de búsqueda es un índice invertido, una estructura que asocia cada término de la base de datos con los documentos en los que aparece, junto con la frecuencia y la posición. Para optimizar el rendimiento:
- El índice se divide en bloques almacenados en archivos `.txt`, con una estructura que sigue el formato: `término (DF: frecuencia de documento): (ID del documento, frecuencia)`.
- Esto permite que el índice sea escalable y eficiente para consultas de texto.

### Implementación SPIMI
Se utilizó el algoritmo SPIMI (Single-Pass In-Memory Indexing) para construir el índice invertido en bloques:
1. **Creación de bloques en Spimi Invert**: Se generan bloques parciales, cada uno almacenado en un archivo de texto.

    **Lógica de implementación**:
    
    El sistema lee una cancion, es decir un doc[i] del cual se extrae:

    ``` py
        col_text = [
        'lyrics', 'track_name', 'track_artist', 
        'track_album_name', 'playlist_name', 
        'playlist_genre', 'playlist_subgenre'
    ]
    ```

    Una vez procesado. El doc[i] se convierte en una liste de terminos, la cual llamaremos list_term_i.

    Ahora usaremos un diccionario de la libreria **SortedDict**, el cual actua como un arbol. Con el beneficio de manter un diccionario ordenado para los terminos, los cuales serán escritos en disco.
    
    De tal manera de tener la forma:

    | Word_for_term_i | df_word | posting_list            |
    |-----------------|---------|-------------------------|
    | word1           | 5       | [(1, 3), (2, 1)]        |
    | word2           | 8       | [(3, 4), (5, 2)]        |
    | word3           | 3       | [(6, 2), (7, 5)]        |
    
    En caso el doc[i] sea demasiado grande, se escribira solo hasta lo permitido de **4 kB**. Y lo demas se mantendra en el diccionario. De tal manera que se puedan escribir doc[i] en un solo bloque, con tal de que quepan en el espacio limite.

    <details>
        <summary>Parte del código: </summary>

    ```py
    def spimi_invert(self, token_stream, docId, num_block):
        for token in token_stream:
            if token not in self.global_dictionary:
                posting_block = PostingBlock()
                self.global_dictionary[token] = {
                    'df': 1,
                    'posting_block': posting_block
                }
                posting_block.add_doc(docId)
                self.global_block_size += sys.getsizeof(token) + sys.getsizeof(self.global_dictionary[token])
            else:
                posting_block = self.global_dictionary[token]['posting_block']
                doc_found = False
                while posting_block:
                    if docId in posting_block.doc_dict:
                        posting_block.doc_dict[docId] += 1
                        doc_found = True
                        break
                    if posting_block.next_block is None:
                        break
                    else:
                        posting_block = posting_block.next_block
                if not doc_found:
                    self.global_dictionary[token]['df'] += 1
                    if posting_block.is_full():
                        new_posting_block = PostingBlock()
                        posting_block.next_block = new_posting_block
                        posting_block = new_posting_block
                    posting_block.add_doc(docId)
                    self.global_block_size += sys.getsizeof(docId)
            if self.global_block_size >= self.size_per_block:
                self.write_block_to_disk(self.global_dictionary, num_block)
                self.global_dictionary = SortedDict()
                self.global_block_size = 0
                num_block += 1
        return num_block
    ```

    </details>

2. **Merge de bloques**: Al finalizar la construcción de todos los bloques, se realiza un proceso de `mergeblock` para unirlos y optimizar el acceso y consulta al índice.

    **Input:** Diccionario de <bloque_name> y <path_block>.

    **Logica:** El proceso recibe como parametros un factor de bloque de salida, que determina el tamaño que debe tener cada bloque final (**4kB** aproximadamente) y el tamaño de ram dedicada para el heap. 

    Lo que se intenta hacer es primero. Abrir todos los archivos por grupos, con el objetivo de usar poca ram. Y por cada archivo dentro de ese bloque carga un buffer, cuyo tamaño se obtiene de $(self.max_ram_limit - self.block_size_limit) // len(block_files)$.  Cada buffer es cargado al heap.

    ```py
    for file_group in file_groups:
    open_files = {file_id: open(file_path, 'r') for file_id, file_path in file_group.items()}
    for file_id, file in open_files.items():
        file_positions[file_id] = file.tell()

    for file_id, file in open_files.items():
        buffer = []
        buffer_size = 0
        while buffer_size < max_memory_per_block:
            line = file.readline().strip()
            if not line:
                break
            term, df, posting_block = self.parse_block_line(line)
            buffer.append((term, df, posting_block))
            buffer_size += sys.getsizeof(term) + sys.getsizeof(df) + sys.getsizeof(posting_block)

        input_buffers[file_id] = buffer

        # Insertar elementos del buffer en el heap
        for term, df, posting_block in buffer:
            heapq.heappush(heap, (term, df, file_id, posting_block))
    for file in open_files.values():
        file.close()
    ```

    De tal menera que se tiene un buffer activo por archivo de bloque, si en caso el buffer se queda vacio, se vuelve a cargar el buffer.

    En este caso, usamos un file_positions, para guardar la linea donde se quedó el buffer dentro del archivo.

    ```py
    if not input_buffers[file_id]:
        with open(block_files[file_id], 'r') as file:
            file.seek(file_positions[file_id])
            buffer = []
            buffer_size = 0
            while buffer_size < max_memory_per_block:
                line = open_files[file_id].readline().strip()
                if not line:
                    break
                term, df, posting_block = self.parse_block_line(line)
                buffer.append((term, df, posting_block))
                buffer_size += sys.getsizeof(term) + sys.getsizeof(df) + sys.getsizeof(posting_block)
            input_buffers[file_id] = buffer
            file_positions[file_id] = file.tell()

        # Agregar nuevos términos del buffer al heap con fusión de duplicados
        for term, df, posting_block in buffer:
            heapq.heappush(heap, (term, df, file_id, posting_block))
    ```

    De tal menera que mientras el heap tenga datos, se extrae el minimo y se inserta en el ouput verificando que ya no exista, en caso exista se junta con la data ya tenida.

    Ademas se usa un contador para ver si ya el output alcanzó el tamaño de salida, cuando sea así, se escribe en disco en el directorio final. Que será ya usado para las consultas.

## 3. Frontend

### Parser SQL-like
El sistema de consulta SQL-like permite a los usuarios hacer preguntas al índice usando una sintaxis similar a SQL, facilitando la familiarización y flexibilidad en las búsquedas. Por ejemplo:
- `select title from Audio where content liketo 'yea you just cant walk away' limit 5'`

### Interfaz gráfica (Tkinter)
La interfaz gráfica, implementada en **Tkinter**, ofrece una experiencia de usuario sencilla y eficiente. Permite:
- Realizar consultas de texto usando el parser SQL-like.
- Visualizar los resultados de las búsquedas.
- Limpiar y reiniciar la interfaz para realizar nuevas consultas.

La GUI está diseñada para ser intuitiva y funcional, mejorando la experiencia de búsqueda en la base de datos de letras de canciones.

## 4. Experimentación

Se realizaron pruebas de rendimiento comparando el tiempo de respuesta de esta implementación en Python con el de PostgreSQL en consultas sobre diferentes tamaños de datos, con valores de N de 1k, 5k, 10k y 18k.

Esto se encuentra en la ruta: /Proyecto2/Experimentacion.ipynb 

### Resultados de la Comparación

| Tamaño de N | Tiempo (ms) - Índice Invertido (Python) Promediado en 5 veces | Tiempo GIN (ms) - PostgreSQL | Tiempo GIST (ms) - PostgreSQL | 
|-------------|----------------------------------------|------------------------------|-------------------------------|
| 1000        | 175,059 ms                                   | 0.245 ms                     | 197.937 ms                    |
| 5000        | 320,940 ms                                   | 0.575 ms                     | 894.740 ms                    |
| 10000       | 377,610 ms                                   | 1.169 ms                     | 1756.667 ms                   |
| 18000       | 971,799 ms                                   | 2.507 ms                     | 3226.991 ms                   |

![alt text](./images/graficoComparativoProyecto2.png)

En los resultados obtenidos, el índice GIN muestra tiempos de respuesta mucho menores en comparación con GIST. A medida que aumenta el tamaño de la tabla (cantidad de canciones), los tiempos de consulta con GIN se mantienen bajos, mientras que GIST presenta un incremento lineal en los tiempos de ejecución.

- Índice GIN: Es eficiente para consultas de texto completo debido a su estructura de índice invertido, permitiendo búsquedas rápidas en grandes volúmenes de texto. PostgreSQL utiliza un Bitmap Index Scan para este índice, optimizando aún más las búsquedas con múltiples términos.

- Índice GIST: Aunque es versátil, no es adecuado para búsquedas de texto completo en grandes volúmenes de datos. No utiliza un índice invertido ni un Bitmap Index Scan, lo que resulta en tiempos de ejecución más altos.

En el caso de la implementacion de Spimi, los tiempos son menores que el indice GIST pero mayores que el indice GIN. Dicha diferencia se infiere que es por la cantidad de bloques que se tienen que buscar, ademas que un word puede estar en mas de un bloque, por la cantidad de terminos que tenga, por lo que una vez encontrada la word en el archivo, hay que buscar en sus vecinos hasta que no encuentre. La busqueda en memoria secundaria de tal manera, ademas de la carga por lineas para la busqueda resulta en dicha diferencia. Sin embargo, los tiempos son los esperados, siendo imperseptibles para el usuario, pues su aumento por la cantidad de datos, no es exponencial, a los mas polinomial.

## 5. Conclusiones
Este proyecto demuestra la eficiencia y flexibilidad de un índice invertido en Python para realizar búsquedas de texto en una base de datos de letras de canciones. Si bien PostgreSQL ofrece ventajas en términos de optimización avanzada, la implementación de este índice invertido permite un control más detallado sobre las consultas y la estructura de datos. Aunque presenta la desventaja de creacion de bloques, y que es estática.


---

</details>

<details>
    <summary> Proyecto 3: Busquedas multidimensionales sobre canciones </summary>
</details>


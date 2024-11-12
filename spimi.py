# librerias
import numpy as np
import pandas as pd
import os
import sys
from sortedcontainers import SortedDict
import nltk
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer
import regex as re
import heapq
import shutil
nltk.download('punkt')

class PostingBlock:
    def __init__(self, max_size=10):
        self.doc_dict = {}
        self.next_block = None
        self.max_size = max_size

    def is_full(self):
        return len(self.doc_dict) >= self.max_size

    def add_doc(self, doc_id, tf=1):
        if doc_id in self.doc_dict:
            self.doc_dict[doc_id] += tf
        else:
            self.doc_dict[doc_id] = tf


class SPIMI:
    def __init__(self, size_per_block=10240*4, output_folder='./blocks/', ram_limit = 1024*1024*1024, size_per_block_out = 1024*5.9):
        self.size_per_block = size_per_block
        self.path_block = './.temp/'
        self.global_dictionary = SortedDict()
        self.global_block_size = 0
        self.output_folder = output_folder
        self.max_ram_limit = ram_limit
        self.size_per_block_out = size_per_block_out

    def parse_docs(self, doc):
        words = []
        col_text = ['lyrics', 'track_name', 'track_artist', 'track_album_name', 'playlist_name', 'playlist_genre', 'playlist_subgenre']
        texto = ' '.join(doc[col] for col in col_text).lower()
        texto = re.sub(r'[^a-zA-Z0-9_À-ÿ]', ' ', texto)
        
        ln = 'spanish' if doc['language'] == 'es' else 'english'
        for word in texto.split():
            if word not in stopwords.words(ln):
                words.append(word)

        stemmer = SnowballStemmer(language=ln)
        return [stemmer.stem(word) for word in words]

    def write_block_to_disk(self, dictionary, block_id):
        output_file = f"{self.path_block}block_{block_id}.txt"
        with open(output_file, 'w') as f:
            for term, data in dictionary.items():
                df = data['df']
                postings_list = []
                posting_block = data['posting_block']
                while posting_block is not None:
                    postings_list.extend([f"({doc_id}, {tf})" for doc_id, tf in posting_block.doc_dict.items()])
                    posting_block = posting_block.next_block
                f.write(f"{term} (DF: {df}): {', '.join(postings_list)}\n")


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

    def parse_block_line(self, line):
        """Parsea una línea del archivo de bloque en el formato (término, DF, PostingBlock)."""
        term, rest = line.split(" (DF: ")
        df, postings = rest.split("): ")
        df = int(df)
        posting_block = PostingBlock()
        postings_list = postings.strip("()").split("), (")
        for posting in postings_list:
            doc_id, tf = map(int, posting.strip("()").split(", "))
            posting_block.add_doc(doc_id, tf)
        return term, df, posting_block
    
    def write_to_output_block(self, 
                              block_id, 
                            output_terms):
        """Escribe los términos y postings en un bloque de salida"""
        output_file = os.path.join(self.output_folder, f"block_{block_id}.txt")

        with open(output_file, 'w') as f:
            for term, (df, posting_block) in output_terms.items():
                term_entry = f"{term} (DF: {df}): "
                postings = []

                current_block = posting_block
                while current_block is not None:
                    postings.extend([f"({doc}, {tf})" for doc, tf in current_block.doc_dict.items()])
                    current_block = current_block.next_block

                term_entry += ', '.join(postings) + "\n"
                f.write(term_entry)

        return block_id + 1, output_file

    def MergeBlocks(self, 
                    block_files):
        
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

        open_files = {file_id: open(file_path, 'r') for file_id, file_path in block_files.items()}
        
        print('Pasa el test 1')

        input_buffers = {}
        current_ram_usage = 0
        # dedico la ram disponible quitando el del bloque de output, que seran las lineas que voy a traer de cada bloque
        max_memory_per_block = (self.max_ram_limit - self.size_per_block_out) // len(block_files) 
        merged_files = []
        
        heap = []
        for file_id, file in open_files.items():
            buffer = []
            buffer_size = 0
            while buffer_size < max_memory_per_block:
                line = file.readline().strip()
                if not line:
                    break  # Si no hay más líneas en el archivo, salir del bucle
                term, df, posting_block = self.parse_block_line(line)
                buffer.append((term, df, posting_block))
                current_ram_usage += sys.getsizeof(term) + sys.getsizeof(df) + sys.getsizeof(posting_block)
            
            # Añadir el buffer al diccionario de buffers y cargar sus términos en el heap
            input_buffers[file_id] = buffer
            
            for term, df, posting_block in buffer:
                found = False
                for i, (existing_term, existing_df, existing_file_id, existing_posting_block) in enumerate(heap):
                    if existing_term == term:
                        existing_df += df
                        current_block = existing_posting_block
                        while current_block.next_block:
                            current_block = current_block.next_block
                        if current_block.is_full():
                            current_block.next_block = posting_block
                        else:
                            for doc, tf in posting_block.doc_dict.items():
                                if current_block.is_full():
                                    new_block = PostingBlock()
                                    current_block.next_block = new_block
                                    current_block = new_block
                                current_block.add_doc(doc, tf)
                        heap[i] = (existing_term, existing_df, existing_file_id, existing_posting_block)
                        found = True
                        break
                
                if not found:
                    heapq.heappush(heap, (term, df, file_id, posting_block))

        block_id = 0
        output_terms = {}
        current_output_size = 0
        
        print('Pasa el test 2, crea el heap')

        while heap:
            # Extraer el término mínimo del heap
            term, df, file_id, posting_block = heapq.heappop(heap)

            # Fusionar postings si el término ya existe en output_terms
            if term in output_terms:
                existing_df, existing_posting_block = output_terms[term]
                output_terms[term] = (existing_df + df, existing_posting_block)
                current_block = existing_posting_block
                while current_block.next_block:
                    current_block = current_block.next_block
                if current_block.is_full():
                    current_block.next_block = posting_block
                else:
                    for doc, tf in posting_block.doc_dict.items():
                        if current_block.is_full():
                            new_block = PostingBlock()
                            current_block.next_block = new_block
                            current_block = new_block
                        current_block.add_doc(doc, tf)
                
                # Solo sumar el tamaño de los nuevos postings agregados
                additional_postings_size = len(', '.join([f"({doc}, {tf})" for doc, tf in posting_block.doc_dict.items()]))
                current_output_size += additional_postings_size
            else:
                output_terms[term] = (df, posting_block)

                # Calcular el tamaño en memoria del término y postings
                postings_str = ', '.join([f"({doc}, {tf})" for doc, tf in posting_block.doc_dict.items()])
                term_entry = f"{term} (DF: {df}): {postings_str}\n"
                term_size = len(term_entry)
                current_output_size += term_size

            # Escribir el bloque de salida cuando se alcanza el límite
            if current_output_size > self.size_per_block_out:
                block_id, block_file = self.write_to_output_block(block_id, output_terms)
                merged_files.append(block_file)
                output_terms.clear()
                current_output_size = 0
                print("Se ha escrito un bloque al disco")
            
            if not input_buffers[file_id]:
                # Cargar nuevas líneas hasta llenar el buffer o alcanzar el límite de RAM
                buffer = []
                buffer_size = 0
                while buffer_size < max_memory_per_block:
                    line = open_files[file_id].readline().strip()
                    if not line:
                        break  # No hay más líneas en el archivo
                    term, df, posting_block = self.parse_block_line(line)
                    buffer.append((term, df, posting_block))
                    buffer_size += sys.getsizeof(term) + sys.getsizeof(df) + sys.getsizeof(posting_block)
                
                input_buffers[file_id] = buffer  # Actualizar el buffer

            # Agregar el siguiente término al heap
            if file_id in input_buffers and input_buffers[file_id]:
                next_term, next_df, next_posting_block = input_buffers[file_id].pop(0)
                heapq.heappush(heap, (next_term, next_df, file_id, next_posting_block))

        # Escribir el último bloque de salida si hay términos restantes
        if output_terms:
            block_id, block_file = self.write_to_output_block(block_id, output_terms)
            merged_files.append(block_file)

        print('Pasa el test 3, termina de hacer el merge')

        for file in open_files.values():
            file.close()

        return merged_files

    def BSBIndexConstuction(self, data):

        if not os.path.exists(self.path_block):
            os.makedirs(self.path_block)

        f = {} # archivos de bloques
        num_block = 0
        for doc_id, row  in data.iterrows():

            token_stream = self.parse_docs(row)
            num_block = self.spimi_invert(token_stream, doc_id, num_block)
            f[num_block] = f'{self.path_block}block_{num_block}.txt'
        
        # en caso de que el ultimo bloque no se haya escrito
        if self.global_dictionary:
            self.write_block_to_disk(self.global_dictionary, num_block)
            f[num_block] = f'{self.path_block}block_{num_block}.txt'
            num_block += 1
            # innecesario pero me sirve para indicar que se acabo y limpiarlo
            self.global_dictionary = SortedDict()
            self.global_block_size = 0

        f = self.MergeBlocks(f)
        shutil.rmtree(self.path_block)
        return f
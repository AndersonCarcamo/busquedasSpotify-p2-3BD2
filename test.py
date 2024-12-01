
from spimi import SPIMI
import pandas as pd
import os
from busquedas_cosine import CosineSimilaritySearch

# testeo
path = './dataset/'
data_path = path + 'spotify_songs.csv'

data = pd.read_csv(data_path)


data1000 = data.head(1000)
data5000 = data.head(5000)
data10000 = data.head(10000)
data18000 = data


# spimi = SPIMI(size_per_block=10240*4,
#               path_block= './.temp1000/',
#               output_folder='./blocks1000_2/',
#               ram_limit=1024*1024*1024*4,
#               size_per_block_out= 1024*4)

# merged_1000 = spimi.BSBIndexConstuction(data1000)
#
#
spimi = SPIMI(size_per_block=10240*4,
              path_block= './.temp5000/',
              output_folder='./blocks5000/',
              ram_limit=1024*1024*1024*4,
              size_per_block_out= 1024*4)

spimi.BSBIndexConstuction(data5000)

spimi = SPIMI(size_per_block=10240*4,
              path_block= './.temp10000/',
              output_folder='./blocks10000/',
              ram_limit=1024*1024*1024*4,
              size_per_block_out= 1024*4)

spimi.BSBIndexConstuction(data10000)

# spimi = SPIMI(size_per_block=10240*4,
#               path_block= './.temp18000/',
#               output_folder='./blocks18000/',
#               ram_limit=1024*1024*1024*4,
#               size_per_block_out= 1024*4)

# def get_block_files(directory):
#     block_files = {}
#     for file_name in os.listdir(directory):
#         file_path = os.path.join(directory, file_name)
#         if os.path.isfile(file_path):  # Asegurarse de que es un archivo
#             block_files[file_name] = file_path
#     return block_files
# #
# f= get_block_files('./.temp18000')
# # print(f)
# spimi.MergeBlocks(f)
# # spimi.BSBIndexConstuction(data18000)


# block_folder = './blocks1/'
# search_engine = CosineSimilaritySearch(block_folder, data)
# results_df = search_engine.get_top_k_similar_documents("mayor que yo", lang='es', k=5)
# print("Top K documentos más similares:")
# print(results_df)
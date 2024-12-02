import psycopg2
from psycopg2 import sql


class PostgresPy:
    # constructor
    def __init__(self, dbname="proyect2",
                 user="postgres",
                 password="3215932112",
                 host="localhost",
                 port="5432"):
        self.connection = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
        self.cursor = self.connection.cursor()

    def procesandoConsulta(self, consulta):
        # agregando | entre las palabras
        palabras = consulta.split()
        return "|".join(palabras)
    
    def consulta(self, limite, consulta, tabla="songs1000"):
        try:
            consulta = self.procesandoConsulta(consulta)
            query = sql.SQL("""
            SELECT track_id, track_name, track_artist , track_album_name , track_album_release_date
            FROM {tabla}
            WHERE to_tsvector('english', lyrics) @@ to_tsquery({consulta})
            LIMIT {limite};
            """).format(
                tabla=sql.Identifier(tabla),
                limite=sql.Literal(limite),
                consulta=sql.Literal(consulta)
            )
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            return results
        except Exception as e:
            print(f"Error ejecutando la consulta: {e}")
            return None
    def CrearBaseDeDatos(self):
        try:
            self.connection.autocommit = True
            cursor = self.connection.cursor()
            cursor.execute("CREATE DATABASE IF NOT EXISTS proyect2;")
            cursor.close()
            self.connection.close()
            print("Base de datos creada con éxito")
        except Exception as e:
            print(f"Error creando base de datos: {e}")
    def __del__(self):
        self.connection.close()
        self.cursor.close()


'''
limite = "5"
consulta_texto = "amor"

try:
    db = PostgresPy()
    results = db.consulta(limite, consulta_texto )

    # Mostrar los resultados
    for row in results:
        print(f'{row[0]} - {row[1]}: {row[2]} - {row[3]} - {row[4]}')
except Exception as e:
    print(f"Error: {e}")'''


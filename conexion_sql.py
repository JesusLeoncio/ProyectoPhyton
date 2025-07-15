import pyodbc
import pyodbc

def conectar_bd():
    try:
        conexion = pyodbc.connect(
            'DRIVER={ODBC Driver 17 for SQL Server};'
            'SERVER=DESKTOP-R4AJ94T;'
            'DATABASE=Tienda_Virtual_Don_Pepe;'
            'Trusted_Connection=yes;'
        )
        print("✅ Conexión exitosa a la base de datos")
        return conexion
    except Exception as e:
        print("❌ Error de conexión:", e)
        return None

if __name__ == "__main__":
    conn = conectar_bd()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sys.tables")
        tablas = cursor.fetchall()
        print("📋 Tablas encontradas en la base de datos:")
        for t in tablas:
            print(" -", t[0])
        conn.close()
    else:
        print("❌ No se pudo conectar.")
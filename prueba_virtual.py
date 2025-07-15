# ------------------------ PARTE 1: IMPORTACIONES, CONEXIÓN Y VARIABLES ------------------------
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import pyodbc
from decimal import Decimal
def conectar_bd():
    try:
        conexion = pyodbc.connect(
            'DRIVER={ODBC Driver 17 for SQL Server};'
            'SERVER=DESKTOP-R4AJ94T;'
            'DATABASE=Tienda_Virtual_Don_Pepe;'
            'Trusted_Connection=yes;'
        )
        return conexion
    except Exception as e:
        messagebox.showerror("Error de conexión", str(e))
        return None

carrito = {}
datos_comprador = {}

# ------------------------ PARTE 2: INTERFAZ PRINCIPAL Y COMPRADOR ------------------------
def menu_principal():
    limpiar_ventana()
    ttk.Label(root, text="TIENDA VIRTUAL DON PEPE", font=("Arial", 20)).pack(pady=20)
    ttk.Button(root, text="Comprador", command=comprador).pack(pady=5)
    ttk.Button(root, text="Administrador", command=login_admin).pack(pady=5)
    ttk.Button(root, text="Finalizar", command=root.quit).pack(pady=5)

def limpiar_ventana():
    for widget in root.winfo_children():
        widget.destroy()

def cargar_categorias():
    categorias = {}
    conn = conectar_bd()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT CategoriaID, Nombre FROM Categorias")
        cat_data = cursor.fetchall()
        for cat in cat_data:
            categorias[cat[1]] = {}
        for nombre_cat in categorias:
            cursor.execute("""
                SELECT p.Nombre, p.Precio FROM Productos p
                JOIN Categorias c ON p.CategoriaID = c.CategoriaID
                WHERE c.Nombre = ?
            """, (nombre_cat,))
            productos = cursor.fetchall()
            for nombre, precio in productos:
                categorias[nombre_cat][nombre] = precio
        conn.close()
    return categorias

def comprador():
    limpiar_ventana()
    ttk.Label(root, text="SELECCIONE CATEGORÍA", font=("Arial", 16)).pack()
    global categorias_db
    categorias_db = cargar_categorias()
    for categoria in categorias_db:
        ttk.Button(root, text=categoria, command=lambda c=categoria: mostrar_productos(c)).pack(pady=2)
    ttk.Button(root, text="Finalizar Compra", command=finalizar_compra).pack(pady=10)
    ttk.Button(root, text="Volver", command=menu_principal).pack()

def mostrar_productos(categoria):
    limpiar_ventana()
    ttk.Label(root, text=f"Productos - {categoria}", font=("Arial", 14)).pack()
    for producto, precio in categorias_db[categoria].items():
        frame = ttk.Frame(root)
        frame.pack()
        ttk.Label(frame, text=f"{producto} - S/ {precio}").pack(side="left")
        cantidad = tk.IntVar()
        ttk.Entry(frame, textvariable=cantidad, width=5).pack(side="left")
        ttk.Button(frame, text="Agregar", command=lambda p=producto, pr=precio, c=cantidad: agregar_carrito(p, pr, c)).pack(side="left")
    ttk.Button(root, text="Volver", command=comprador).pack(pady=10)

def agregar_carrito(producto, precio, cantidad_var):
    cantidad = cantidad_var.get()
    if cantidad > 0:
        if producto in carrito:
            carrito[producto]["cantidad"] += cantidad
        else:
            carrito[producto] = {"precio": precio, "cantidad": cantidad}
        messagebox.showinfo("Producto agregado", f"Se agregaron {cantidad} {producto}(s) al carrito.")
    else:
        messagebox.showerror("Error", "Cantidad inválida")

def finalizar_compra():
    limpiar_ventana()
    ttk.Label(root, text="Ingrese sus datos de pago", font=("Arial", 14)).pack(pady=10)

    ttk.Label(root, text="Nombre y Apellido:").pack()
    nombre = tk.StringVar()
    ttk.Entry(root, textvariable=nombre).pack()

    ttk.Label(root, text="Tarjeta (16 dígitos):").pack()
    tarjeta = tk.StringVar()
    ttk.Entry(root, textvariable=tarjeta).pack()

    ttk.Label(root, text="Contraseña (4 dígitos):").pack()
    clave = tk.StringVar()
    ttk.Entry(root, textvariable=clave, show="*").pack()

    ttk.Label(root, text="Fecha de Caducidad (MM/AA):").pack()
    fecha = tk.StringVar()
    ttk.Entry(root, textvariable=fecha).pack()

    ttk.Button(root, text="Pagar", command=lambda: procesar_pago(tarjeta.get(), nombre.get(), clave.get(), fecha.get())).pack(pady=10)
    ttk.Button(root, text="Volver", command=comprador).pack()

# ------------------------ PARTE 3: PROCESAR PAGO Y BOLETA ------------------------
def procesar_pago(tarjeta, nombre, clave, fecha):
    if len(tarjeta) != 16 or not tarjeta.isdigit():
        messagebox.showerror("Error", "Número de tarjeta inválido")
        return
    if len(clave) != 4 or not clave.isdigit():
        messagebox.showerror("Error", "Contraseña inválida")
        return
    try:
        fecha_ingresada = datetime.strptime(fecha, "%m/%y")
        if fecha_ingresada < datetime.now():
            messagebox.showerror("Error", "Tarjeta caducada")
            return
    except:
        messagebox.showerror("Error", "Formato de fecha inválido")
        return

    conn = conectar_bd()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Compradores (NombreCompleto, Tarjeta, Clave, FechaCaducidad)
            VALUES (?, ?, ?, ?)
        """, (nombre.strip(), tarjeta, clave, fecha))
        conn.commit()

        cursor.execute("SELECT TOP 1 CompradorID FROM Compradores ORDER BY CompradorID DESC")
        comprador_id = cursor.fetchone()[0]
        datos_comprador["nombre"] = nombre.strip()
        datos_comprador["tarjeta"] = "**** **** **** " + tarjeta[-4:]

        total = sum(
     (info["precio"] * info["cantidad"] * Decimal("0.9") if info["cantidad"] >= 5 else info["precio"] * info["cantidad"])
     for info in carrito.values()
     )
        igv = total * Decimal("0.18")

        cursor.execute("""
            INSERT INTO Boletas (CompradorID, FechaCompra, Total, IGV)
            VALUES (?, GETDATE(), ?, ?)
        """, (comprador_id, total, igv))
        conn.commit()

        cursor.execute("SELECT TOP 1 BoletaID FROM Boletas ORDER BY BoletaID DESC")
        boleta_id = cursor.fetchone()[0]

        for producto, info in carrito.items():
            # Búsqueda segura ignorando espacios y mayúsculas/minúsculas
            cursor.execute("""
                SELECT ProductoID 
                FROM Productos 
                WHERE RTRIM(LTRIM(Nombre)) = RTRIM(LTRIM(?)) COLLATE Latin1_General_CI_AI
            """, (producto,))
            resultado = cursor.fetchone()
            if not resultado:
                messagebox.showerror("Error", f"No se encontró el producto: '{producto}' en la base de datos.")
                continue  # Salta este producto

            producto_id = resultado[0]
            cantidad = info["cantidad"]
            precio = info["precio"]
            subtotal = precio * cantidad
            if cantidad >= 5:
             subtotal *= Decimal("0.9")

            cursor.execute("""
                INSERT INTO DetalleBoleta (BoletaID, ProductoID, Cantidad, PrecioUnitario, Subtotal)
                VALUES (?, ?, ?, ?, ?)
            """, (boleta_id, producto_id, cantidad, precio, subtotal))

        conn.commit()
        conn.close()
    print(">> Mostrando boleta...")
    mostrar_boleta()



def mostrar_boleta():
    ventana_boleta = tk.Toplevel(root)
    ventana_boleta.title("Boleta de Compra")
    ventana_boleta.geometry("400x600")

    ttk.Label(ventana_boleta, text="BOLETA DE COMPRA", font=("Arial", 16)).pack(pady=10)
    ttk.Label(ventana_boleta, text="La Tiendita de Don Pepe - SAC", font=("Arial", 12)).pack()
    ttk.Label(ventana_boleta, text="RUC: 20481234567").pack()
    ttk.Label(ventana_boleta, text=f"Cliente: {datos_comprador.get('nombre', '-')}", font=("Arial", 10)).pack()
    ttk.Label(ventana_boleta, text=f"Tarjeta: {datos_comprador.get('tarjeta', '-')}", font=("Arial", 10)).pack()
    ttk.Label(ventana_boleta, text=f"Fecha y hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}").pack(pady=5)

    ttk.Separator(ventana_boleta).pack(fill='x', pady=5)

    total = Decimal("0.00")
    for producto, info in carrito.items():
        cantidad = info["cantidad"]
        precio_unit = info["precio"]
        subtotal = precio_unit * cantidad

        if cantidad >= 5:
            descuento = subtotal * Decimal("0.10")
            subtotal -= descuento
            descuento_msg = " (10% desc)"
        else:
            descuento_msg = ""

        ttk.Label(ventana_boleta, text=f"{producto} x{cantidad} - S/ {subtotal:.2f}{descuento_msg}").pack(anchor='w', padx=10)
        total += subtotal

    igv = total * Decimal("0.18")
    total_con_igv = total + igv

    ttk.Label(ventana_boleta, text=f"\nIGV (18%): S/ {igv:.2f}").pack()
    ttk.Label(ventana_boleta, text=f"Total a pagar: S/ {total_con_igv:.2f}", font=("Arial", 14)).pack(pady=10)

    ttk.Button(ventana_boleta, text="Volver al Menú Principal", command=lambda: [carrito.clear(), ventana_boleta.destroy(), menu_principal()]).pack(pady=10)

#------------------------ CONTINÚO EN LA PARTE 4 ------------------------
# ------------------------ ADMIN ------------------------
def login_admin():
    limpiar_ventana()
    ttk.Label(root, text="Login Administrador", font=("Arial", 16)).pack(pady=10)

    ttk.Label(root, text="Usuario:").pack()
    usuario = tk.StringVar()
    ttk.Entry(root, textvariable=usuario).pack()

    ttk.Label(root, text="Contraseña:").pack()
    clave = tk.StringVar()
    ttk.Entry(root, textvariable=clave, show="*").pack()

    ttk.Button(root, text="Entrar", command=lambda: validar_admin(usuario.get(), clave.get())).pack(pady=10)
    ttk.Button(root, text="Volver", command=menu_principal).pack()

def validar_admin(usuario, clave):
    if usuario == "AdminSus" and clave == "1520":
        crud_admin()
    else:
        messagebox.showerror("Acceso denegado", "Usuario o contraseña incorrectos")

def crud_admin():
    limpiar_ventana()
    ttk.Label(root, text="Panel CRUD", font=("Arial", 16)).pack(pady=10)
    ttk.Button(root, text="Agregar Categoría", command=agregar_categoria).pack(pady=2)
    ttk.Button(root, text="Eliminar Categoría", command=eliminar_categoria).pack(pady=2)
    ttk.Button(root, text="Agregar Producto", command=agregar_producto).pack(pady=2)
    ttk.Button(root, text="Eliminar Producto", command=eliminar_producto).pack(pady=2)
    ttk.Button(root, text="Modificar Precio", command=modificar_precio).pack(pady=2)
    ttk.Button(root, text="Ver Productos", command=ver_productos).pack(pady=2)
    ttk.Button(root, text="Volver", command=menu_principal).pack(pady=10)

# ------------------------ CRUD ADMINISTRADOR ------------------------

def crud_admin():
    limpiar_ventana()
    ttk.Label(root, text="Panel CRUD", font=("Arial", 16)).pack(pady=10)
    ttk.Button(root, text="Agregar Categoría", command=agregar_categoria).pack(pady=5)
    ttk.Button(root, text="Eliminar Categoría", command=eliminar_categoria).pack(pady=5)
    ttk.Button(root, text="Agregar Producto", command=agregar_producto).pack(pady=5)
    ttk.Button(root, text="Eliminar Producto", command=eliminar_producto).pack(pady=5)
    ttk.Button(root, text="Modificar Precio de Producto", command=modificar_precio).pack(pady=5)
    ttk.Button(root, text="Ver Productos", command=ver_productos).pack(pady=10)
    ttk.Button(root, text="Volver", command=menu_principal).pack(pady=10)

def agregar_categoria():
    def guardar():
        nombre = entrada.get().strip()
        if nombre:
            conn = conectar_bd()
            if conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO Categorias (Nombre) VALUES (?)", nombre)
                conn.commit()
                conn.close()
                messagebox.showinfo("Éxito", f"Categoría '{nombre}' agregada.")
                ventana.destroy()

    ventana = tk.Toplevel(root)
    ventana.title("Agregar Categoría")
    ttk.Label(ventana, text="Nombre de la categoría:").pack(pady=5)
    entrada = ttk.Entry(ventana)
    entrada.pack()
    ttk.Button(ventana, text="Guardar", command=guardar).pack(pady=10)

def eliminar_categoria():
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("SELECT Nombre FROM Categorias")
    categorias = [row[0] for row in cursor.fetchall()]
    conn.close()

    def eliminar():
        nombre = combo.get()
        if nombre:
            conn = conectar_bd()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Categorias WHERE Nombre = ?", nombre)
            conn.commit()
            conn.close()
            messagebox.showinfo("Éxito", f"Categoría '{nombre}' eliminada.")
            ventana.destroy()

    ventana = tk.Toplevel(root)
    ventana.title("Eliminar Categoría")
    ttk.Label(ventana, text="Seleccione la categoría:").pack()
    combo = ttk.Combobox(ventana, values=categorias)
    combo.pack()
    ttk.Button(ventana, text="Eliminar", command=eliminar).pack(pady=10)

def agregar_producto():
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("SELECT CategoriaID, Nombre FROM Categorias")
    categorias = cursor.fetchall()
    conn.close()

    def guardar():
        nombre_prod = entrada_nombre.get().strip()
        try:
            precio = float(entrada_precio.get())
            id_categoria = categorias[combo.current()][0]
            conn = conectar_bd()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Productos (Nombre, Precio, CategoriaID) VALUES (?, ?, ?)",
                           (nombre_prod, precio, id_categoria))
            conn.commit()
            conn.close()
            messagebox.showinfo("Éxito", "Producto agregado.")
            ventana.destroy()
        except:
            messagebox.showerror("Error", "Datos inválidos.")

    ventana = tk.Toplevel(root)
    ventana.title("Agregar Producto")
    ttk.Label(ventana, text="Nombre del producto:").pack()
    entrada_nombre = ttk.Entry(ventana)
    entrada_nombre.pack()
    ttk.Label(ventana, text="Precio:").pack()
    entrada_precio = ttk.Entry(ventana)
    entrada_precio.pack()
    ttk.Label(ventana, text="Categoría:").pack()
    combo = ttk.Combobox(ventana, values=[c[1] for c in categorias])
    combo.pack()
    ttk.Button(ventana, text="Guardar", command=guardar).pack(pady=10)

def eliminar_producto():
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("SELECT Nombre FROM Productos")
    productos = [row[0] for row in cursor.fetchall()]
    conn.close()

    def eliminar():
        nombre = combo.get()
        if nombre:
            conn = conectar_bd()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Productos WHERE Nombre = ?", nombre)
            conn.commit()
            conn.close()
            messagebox.showinfo("Éxito", f"Producto '{nombre}' eliminado.")
            ventana.destroy()

    ventana = tk.Toplevel(root)
    ventana.title("Eliminar Producto")
    ttk.Label(ventana, text="Seleccione el producto:").pack()
    combo = ttk.Combobox(ventana, values=productos)
    combo.pack()
    ttk.Button(ventana, text="Eliminar", command=eliminar).pack(pady=10)

def modificar_precio():
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("SELECT Nombre FROM Productos")
    productos = [row[0] for row in cursor.fetchall()]
    conn.close()

    def actualizar():
        nuevo_precio = entrada_precio.get()
        nombre_producto = combo.get()
        try:
            precio = float(nuevo_precio)
            conn = conectar_bd()
            cursor = conn.cursor()
            cursor.execute("UPDATE Productos SET Precio = ? WHERE Nombre = ?", (precio, nombre_producto))
            conn.commit()
            conn.close()
            messagebox.showinfo("Éxito", "Precio actualizado.")
            ventana.destroy()
        except:
            messagebox.showerror("Error", "Precio inválido")

    ventana = tk.Toplevel(root)
    ventana.title("Modificar Precio")
    ttk.Label(ventana, text="Producto:").pack()
    combo = ttk.Combobox(ventana, values=productos)
    combo.pack()
    ttk.Label(ventana, text="Nuevo precio:").pack()
    entrada_precio = ttk.Entry(ventana)
    entrada_precio.pack()
    ttk.Button(ventana, text="Actualizar", command=actualizar).pack(pady=10)

def ver_productos():
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT P.Nombre, C.Nombre AS Categoria, P.Precio
        FROM Productos P
        JOIN Categorias C ON P.CategoriaID = C.CategoriaID
    """)
    productos = cursor.fetchall()
    conn.close()

    ventana = tk.Toplevel(root)
    ventana.title("Lista de Productos")
    tree = ttk.Treeview(ventana, columns=("Producto", "Categoría", "Precio"), show="headings")
    tree.heading("Producto", text="Producto")
    tree.heading("Categoría", text="Categoría")
    tree.heading("Precio", text="Precio (S/.)")

    for prod in productos:
        tree.insert("", tk.END, values=prod)

    tree.pack(expand=True, fill="both")

# ------------------------ EJECUTAR APP ------------------------
root = tk.Tk()
root.title("Tienda Virtual Don Pepe")
root.geometry("500x600")
menu_principal()
root.mainloop()
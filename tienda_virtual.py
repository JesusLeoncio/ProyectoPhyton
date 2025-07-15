import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import pyodbc

# ------------------------ CONEXIÓN A BASE DE DATOS ------------------------
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

categorias = {
    "Tecnología": {
        "Laptop": 2500,
        "Mouse": 50,
        "Teclado": 120,
        "Monitor": 800,
        "USB": 40
    },
    "Ropa": {
        "Polo": 30,
        "Pantalón": 60,
        "Zapatillas": 150,
        "Casaca": 200,
        "Gorra": 25
    },
    "Alimentos": {
        "Arroz": 3,
        "Leche": 5,
        "Pan": 2,
        "Huevos": 8,
        "Pollo": 20
    },
    "Hogar": {
        "Escoba": 10,
        "Detergente": 15,
        "Platos": 25,
        "Taza": 12,
        "Sartén": 35
    },
    "Juguetes": {
        "Pelota": 40,
        "Rompecabezas": 22,
        "Muñeca": 30,
        "Autito": 18,
        "Lego": 60
    }
}

carrito = {}
datos_comprador = {}

# ------------------------ INTERFAZ PRINCIPAL ------------------------
def menu_principal():
    limpiar_ventana()
    ttk.Label(root, text="TIENDA VIRTUAL DON PEPE", font=("Arial", 20)).pack(pady=20)
    ttk.Button(root, text="Comprador", command=comprador).pack(pady=5)
    ttk.Button(root, text="Administrador", command=login_admin).pack(pady=5)
    ttk.Button(root, text="Finalizar", command=root.quit).pack(pady=5)

def limpiar_ventana():
    for widget in root.winfo_children():
        widget.destroy()

# ------------------------ COMPRADOR ------------------------
def comprador():
    limpiar_ventana()
    ttk.Label(root, text="SELECCIONE CATEGORÍA", font=("Arial", 16)).pack()
    for categoria in categorias:
        ttk.Button(root, text=categoria, command=lambda c=categoria: mostrar_productos(c)).pack(pady=2)
    ttk.Button(root, text="Finalizar Compra", command=finalizar_compra).pack(pady=10)
    ttk.Button(root, text="Volver", command=menu_principal).pack()

def mostrar_productos(categoria):
    limpiar_ventana()
    ttk.Label(root, text=f"Productos - {categoria}", font=("Arial", 14)).pack()
    for producto, precio in categorias[categoria].items():
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
        """, (nombre, tarjeta, clave, fecha))
        conn.commit()

        cursor.execute("SELECT TOP 1 CompradorID FROM Compradores ORDER BY CompradorID DESC")
        comprador_id = cursor.fetchone()[0]
        datos_comprador["nombre"] = nombre
        datos_comprador["tarjeta"] = "**** **** **** " + tarjeta[-4:]

        total = sum(
            (info["precio"] * info["cantidad"] * 0.9 if info["cantidad"] >= 5 else info["precio"] * info["cantidad"])
            for info in carrito.values()
        )
        igv = total * 0.18

        cursor.execute("""
            INSERT INTO Boletas (CompradorID, FechaCompra, Total, IGV)
            VALUES (?, GETDATE(), ?, ?)
        """, (comprador_id, total, igv))
        conn.commit()

        cursor.execute("SELECT TOP 1 BoletaID FROM Boletas ORDER BY BoletaID DESC")
        boleta_id = cursor.fetchone()[0]

        for producto, info in carrito.items():
            cursor.execute("SELECT ProductoID FROM Productos WHERE Nombre = ?", producto)
            resultado = cursor.fetchone()
            if resultado:
                producto_id = resultado[0]
                cantidad = info["cantidad"]
                precio = info["precio"]
                subtotal = precio * cantidad
                if cantidad >= 5:
                    subtotal *= 0.9
                cursor.execute("""
                    INSERT INTO DetalleBoleta (BoletaID, ProductoID, Cantidad, PrecioUnitario, Subtotal)
                    VALUES (?, ?, ?, ?, ?)
                """, (boleta_id, producto_id, cantidad, precio, subtotal))
        conn.commit()
        conn.close()

    mostrar_boleta()

def mostrar_boleta():
    limpiar_ventana()
    ttk.Label(root, text="BOLETA DE COMPRA", font=("Arial", 16)).pack(pady=10)
    ttk.Label(root, text="La Tiendita de Don Pepe - SAC", font=("Arial", 12)).pack()
    ttk.Label(root, text="RUC: 20481234567").pack()
    ttk.Label(root, text=f"Cliente: {datos_comprador.get('nombre', '-')}").pack()
    ttk.Label(root, text=f"Tarjeta: {datos_comprador.get('tarjeta', '-')}").pack()
    ttk.Label(root, text=f"Fecha y hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}").pack(pady=5)

    total = 0
    for producto, info in carrito.items():
        cantidad = info["cantidad"]
        precio_unit = info["precio"]
        subtotal = cantidad * precio_unit
        if cantidad >= 5:
            descuento = subtotal * 0.10
            subtotal -= descuento
            descuento_msg = " (10% desc aplicado)"
        else:
            descuento_msg = ""
        ttk.Label(root, text=f"{producto} x{cantidad} - S/ {subtotal:.2f}{descuento_msg}").pack()
        total += subtotal

    igv = total * 0.18
    ttk.Label(root, text=f"\nIGV (18%): S/ {igv:.2f}").pack()
    ttk.Label(root, text=f"Total a pagar: S/ {total:.2f}", font=("Arial", 14)).pack(pady=10)
    ttk.Button(root, text="Volver al Menú Principal", command=lambda: [carrito.clear(), menu_principal()]).pack(pady=10)

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
    ttk.Button(root, text="Volver", command=menu_principal).pack(pady=10)

# ------------------------ EJECUTAR APP ------------------------
root = tk.Tk()
root.title("Tienda Virtual Don Pepe")
root.geometry("500x600")
menu_principal()
root.mainloop()

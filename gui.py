import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import gestor
import motor
import csv
import time
import webbrowser
import os
import sys
import json

# --- CLASE DEL TECLADO EMERGENTE ---
class TecladoHebreo(tk.Toplevel):
    def __init__(self, parent, callback_insert, callback_backspace):
        super().__init__(parent)
        self.title("Teclado")
        self.geometry("320x220")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        
        letras = ['א', 'ב', 'ג', 'ד', 'ה', 'ו', 'ז', 'ח', 'ט', 'י', 'כ', 'ל', 'מ', 'נ', 'ס', 'ע', 'פ', 'צ', 'ק', 'ר', 'ש', 'ת']
        frame_letras = tk.Frame(self)
        frame_letras.pack(pady=5)
        for i, letra in enumerate(letras):
            btn = tk.Button(frame_letras, text=letra, width=3, height=1, font=("Arial", 12), command=lambda l=letra: callback_insert(l))
            btn.grid(row=i//7, column=6-(i%7), padx=1, pady=1)
        
        frame_ctrl = tk.Frame(self)
        frame_ctrl.pack(fill="x", padx=10, pady=5)
        tk.Button(frame_ctrl, text="← Borrar", bg="#f44336", fg="white", width=12, command=callback_backspace).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_ctrl, text="ENTER", bg="#4CAF50", fg="white", width=12, command=self.destroy).pack(side=tk.RIGHT, padx=5)

class AplicacionELS:
    def __init__(self, ventana):
        self.ventana = ventana
        self.ventana.title("Buscador de Códigos Bíblicos by Alvaro Ricaurte")
        self.ventana.geometry("1600x950")
        
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        self.ruta_datos = os.path.join(base_path, "DATA")
        self.texto_actual = None 
        self.df_idx = None
        self.font_size = 10
        self.division_actual = 0 
        self.matriz_actual_letras = [] 
        self.matriz_actual_indices = []
        self.dicc_pos_rapida = {}

        self.ultimo_foco = None
        self.entries_extra = []
        self.resultados_secundarios = []
        self.rango_local = 5 
        self.idx_color_local_persistente = 0 
        
        self.colores_extra = ["#FFB6C1", "#90EE90", "#ADD8E6", "#FFD700", "#E6E6FA", "#F5DEB3", "#B0E0E6", "#D8BFD8", "#F0E68C", "#AFEEEE"]
        self.colores_local = ["#FF4500", "#1E90FF", "#32CD32", "#BA55D3", "#FF8C00", "#00CED1"]

        self.MAX_F, self.MAX_C = 60, 60 
        self.celdas = []

        self.paned = tk.PanedWindow(ventana, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=6)
        self.paned.pack(fill="both", expand=True)

        self.frame_izq = tk.Frame(self.paned); self.paned.add(self.frame_izq, width=350)

        # 1. Dimensiones
        p_u = tk.LabelFrame(self.frame_izq, text=" 1. Dimensiones del Umbral ", padx=10, pady=10)
        p_u.pack(fill="x", padx=10, pady=5)
        tk.Label(p_u, text="Ancho:").grid(row=0, column=0)
        self.ent_w = tk.Entry(p_u, width=5); self.ent_w.insert(0, "30"); self.ent_w.grid(row=0, column=1)
        self.ent_w.bind("<Return>", lambda e: self.actualizar_visor(None))
        
        tk.Button(p_u, text="-", width=2, command=lambda: self.ajustar_dim(self.ent_w, -1)).grid(row=0, column=2, padx=2)
        tk.Button(p_u, text="+", width=2, command=lambda: self.ajustar_dim(self.ent_w, 1)).grid(row=0, column=3, padx=2)
        
        tk.Label(p_u, text="    Alto:").grid(row=0, column=4)
        self.ent_h = tk.Entry(p_u, width=5); self.ent_h.insert(0, "30"); self.ent_h.grid(row=0, column=5)
        self.ent_h.bind("<Return>", lambda e: self.actualizar_visor(None))
        
        tk.Button(p_u, text="-", width=2, command=lambda: self.ajustar_dim(self.ent_h, -1)).grid(row=0, column=6, padx=2)
        tk.Button(p_u, text="+", width=2, command=lambda: self.ajustar_dim(self.ent_h, 1)).grid(row=0, column=7, padx=2)

        # 2. Búsqueda Global
        p_s = tk.LabelFrame(self.frame_izq, text=" 2. Búsqueda Global ", padx=10, pady=5)
        p_s.pack(fill="x", padx=10, pady=5)
        tk.Label(p_s, text="Libro:").grid(row=0, column=0)
        self.cb_libro = ttk.Combobox(p_s, values=["GENESIS", "EXODO", "LEVITICO", "NUMEROS", "DEUTERONOMIO", "TORAH"], width=15); self.cb_libro.grid(row=0, column=1, columnspan=2); self.cb_libro.current(5)
        
        tk.Label(p_s, text="ANCLA:", font=("Arial", 9, "bold"), fg="blue").grid(row=1, column=0)
        self.ent_ancla = tk.Entry(p_s, justify="right", font=("Arial", 10, "bold"), width=15)
        self.ent_ancla.grid(row=1, column=1, pady=8)
        self.ent_ancla.bind("<FocusIn>", lambda e: self.set_foco(self.ent_ancla))
        
        tk.Button(p_s, text="⌫", width=2, command=lambda: self.limpiar_entry(self.ent_ancla), bg="#ffebee").grid(row=1, column=2, padx=1)
        tk.Button(p_s, text="⌨", width=3, command=self.abrir_teclado, bg="#eee").grid(row=1, column=3, padx=1)

        for i in range(10):
            r, c_base = (i % 5) + 2, 0 if i < 5 else 2
            tk.Label(p_s, text=f"Ex {i+1}:").grid(row=r, column=c_base, sticky="w")
            ent = tk.Entry(p_s, justify="right", width=10)
            ent.grid(row=r, column=c_base+1, pady=2, padx=1)
            ent.bind("<FocusIn>", lambda e, en=ent: self.set_foco(en))
            self.entries_extra.append(ent)
            tk.Button(p_s, text="⌫", font=("Arial", 7), width=2, command=lambda en=ent: self.limpiar_entry(en)).grid(row=r, column=c_base+1, sticky="e")

        self.ent_min = tk.Entry(p_s, width=10); self.ent_min.insert(0, "-100"); self.ent_min.grid(row=7, column=1)
        self.ent_max = tk.Entry(p_s, width=10); self.ent_max.insert(0, "100"); self.ent_max.grid(row=7, column=3)
        tk.Label(p_s, text="S. Mín:").grid(row=7, column=0); tk.Label(p_s, text="S. Máx:").grid(row=7, column=2)
        
        self.btn_run = tk.Button(p_s, text="BUSCAR ENCUENTROS", bg="#1a73e8", fg="white", font=("Arial", 10, "bold"), command=self.procesar)
        self.btn_run.grid(row=8, column=0, columnspan=4, sticky="we", pady=10)

        self.progreso = ttk.Progressbar(p_s, orient="horizontal", mode="determinate")
        self.progreso.grid(row=9, column=0, columnspan=4, sticky="we", padx=5)
        self.lbl_timer = tk.Label(p_s, text="Tiempo: 0.00s", font=("Arial", 8))
        self.lbl_timer.grid(row=10, column=0, columnspan=4, sticky="e", padx=5)

        self.btn_clear_all = tk.Button(self.frame_izq, text="🗑 LIMPIAR TODO", bg="#f44336", fg="white", font=("Arial", 10, "bold"), command=self.limpiar_todo)
        self.btn_clear_all.pack(fill="x", padx=10, pady=5)

        self.frame_tabla = tk.Frame(self.frame_izq)
        self.frame_tabla.pack(fill="both", expand=True, padx=10, pady=5)
        self.scroll_tabla = tk.Scrollbar(self.frame_tabla)
        self.scroll_tabla.pack(side=tk.RIGHT, fill=tk.Y)
        self.tabla = ttk.Treeview(self.frame_tabla, columns=("s", "e", "r"), show='headings', yscrollcommand=self.scroll_tabla.set)
        self.tabla.heading("s", text="Salto Ancla", command=lambda: self.ordenar_columna("s", False))
        self.tabla.heading("e", text="Encuentros", command=lambda: self.ordenar_columna("e", False))
        self.tabla.heading("r", text="Referencia", command=lambda: self.ordenar_columna("r", False))

        self.tabla.column("s", width=50, anchor="center"); self.tabla.column("e", width=50, anchor="center"); self.tabla.column("r", width=100)
        self.tabla.pack(side=tk.LEFT, fill="both", expand=True)
        self.scroll_tabla.config(command=self.tabla.yview)
        self.tabla.bind("<<TreeviewSelect>>", self.actualizar_visor)

        # --- PANEL DERECHO ---
        self.frame_der = tk.Frame(self.paned); self.paned.add(self.frame_der)
        self.frame_tools = tk.Frame(self.frame_der, pady=8, bg="#f0f0f0", relief=tk.RAISED, bd=1)
        self.frame_tools.pack(fill="x")

        # Gestión de Sesión
        tk.Button(self.frame_tools, text="📁 ABRIR", bg="#fff176", command=self.cargar_sesion).pack(side=tk.LEFT, padx=5)
        tk.Button(self.frame_tools, text="💾 GUARDAR", bg="#81c784", command=self.guardar_sesion).pack(side=tk.LEFT, padx=5)
        ttk.Separator(self.frame_tools, orient=tk.VERTICAL).pack(side=tk.LEFT, fill="y", padx=10)

        tk.Label(self.frame_tools, text="letra:", font=("Arial", 9, "bold"), bg="#f0f0f0").pack(side=tk.LEFT, padx=(10, 2))
        tk.Button(self.frame_tools, text="+", width=2, command=lambda: self.cambiar_fuente(1)).pack(side=tk.LEFT)
        tk.Button(self.frame_tools, text="-", width=2, command=lambda: self.cambiar_fuente(-1)).pack(side=tk.LEFT, padx=(0, 5))
        
        for d in [1, 2, 3]:
            tk.Button(self.frame_tools, text=str(d), width=2, bg="#e0e0e0", command=lambda x=d: self.set_division(x)).pack(side=tk.LEFT, padx=1)
        tk.Button(self.frame_tools, text="N", width=2, bg="#e0e0e0", command=lambda: self.set_division(0)).pack(side=tk.LEFT, padx=(1, 10))

        tk.Label(self.frame_tools, text="local:", font=("Arial", 9, "bold"), bg="#f0f0f0").pack(side=tk.LEFT, padx=5)
        self.ent_local = tk.Entry(self.frame_tools, justify="right", width=10); self.ent_local.pack(side=tk.LEFT, padx=2)
        self.ent_local.bind("<FocusIn>", lambda e: self.set_foco(self.ent_local))
        tk.Button(self.frame_tools, text="⌫", width=2, command=lambda: self.limpiar_entry(self.ent_local), bg="#ffebee").pack(side=tk.LEFT, padx=1)
        
        tk.Button(self.frame_tools, text="BUSCAR", bg="#34a853", fg="white", command=self.ejecutar_busqueda_local).pack(side=tk.LEFT, padx=2)
        tk.Button(self.frame_tools, text="LIMPIAR", bg="#5f6368", fg="white", command=self.limpiar_busqueda_local).pack(side=tk.LEFT, padx=2)

        # Alcance
        tk.Label(self.frame_tools, text="alcance:", font=("Arial", 9, "bold"), bg="#f0f0f0").pack(side=tk.LEFT, padx=(10, 2))
        self.lbl_rango_val = tk.Label(self.frame_tools, text=str(self.rango_local), width=2, bg="white", relief="sunken")
        self.lbl_rango_val.pack(side=tk.LEFT, padx=2)
        tk.Button(self.frame_tools, text="-", width=2, command=lambda: self.ajustar_rango_local(-1)).pack(side=tk.LEFT)
        tk.Button(self.frame_tools, text="+", width=2, command=lambda: self.ajustar_rango_local(1)).pack(side=tk.LEFT)

        ttk.Separator(self.frame_tools, orient=tk.VERTICAL).pack(side=tk.LEFT, fill="y", padx=10)
        tk.Button(self.frame_tools, text="CSV", bg="#e8f0fe", command=self.exportar_matriz_csv).pack(side=tk.LEFT, padx=2)
        tk.Button(self.frame_tools, text="HTML", bg="#e8f0fe", command=self.exportar_matriz_html).pack(side=tk.LEFT, padx=2)
        
        self.btn_salir = tk.Button(self.frame_tools, text="✖ SALIR", bg="#333333", fg="white", font=("Arial", 9, "bold"), command=self.salir_programa)
        self.btn_salir.pack(side=tk.LEFT, padx=5)

        self.lbl_info_matriz = tk.Label(self.frame_der, text="Seleccione un resultado para ver la matriz", font=("Arial", 14, "bold"), bg="#ffffff", pady=8)
        self.lbl_info_matriz.pack(fill="x")

        self.v_cont = tk.Frame(self.frame_der, bg="white")
        self.v_cont.pack(fill="both", expand=True)
        self.canvas_matriz = tk.Canvas(self.v_cont, bg="white", highlightthickness=0)
        self.scroll_y = tk.Scrollbar(self.v_cont, orient="vertical", command=self.canvas_matriz.yview)
        self.scroll_x = tk.Scrollbar(self.v_cont, orient="horizontal", command=self.canvas_matriz.xview)
        self.grid_wrapper = tk.Frame(self.canvas_matriz, bg="white")
        self.canvas_matriz.create_window((0, 0), window=self.grid_wrapper, anchor="nw")
        self.canvas_matriz.configure(yscrollcommand=self.scroll_y.set, xscrollcommand=self.scroll_x.set)
        self.scroll_y.pack(side=tk.RIGHT, fill=tk.Y); self.scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas_matriz.pack(side=tk.LEFT, fill="both", expand=True)

        for f in range(self.MAX_F):
            fila_l = []
            for c in range(self.MAX_C + 2):
                es_ref = (c == 0 or c == self.MAX_C + 1)
                lbl = tk.Label(self.grid_wrapper, text="", width=2 if not es_ref else 20, font=("Courier New", self.font_size), bg="white", borderwidth=0)
                lbl.grid(row=f, column=c, padx=0, pady=0); lbl.grid_remove()
                fila_l.append(lbl)
            self.celdas.append(fila_l)

    def guardar_sesion(self):
        archivo = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if not archivo: return
        datos = {
            "config": {"libro": self.cb_libro.get(), "w": self.ent_w.get(), "h": self.ent_h.get(), "min": self.ent_min.get(), "max": self.ent_max.get()},
            "busqueda": {"ancla": self.ent_ancla.get(), "extras": [e.get() for e in self.entries_extra]},
            "tabla": [self.tabla.item(i, "values") + (self.tabla.item(i, "tags"),) for i in self.tabla.get_children()],
            "seleccion": self.tabla.item(self.tabla.selection()[0], "tags") if self.tabla.selection() else None,
            "notas": self.notas_celdas  
        }
        with open(archivo, 'w', encoding='utf-8') as f: json.dump(datos, f, indent=4, ensure_ascii=False)

    def cargar_sesion(self):
        archivo = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if not archivo: return
        with open(archivo, 'r', encoding='utf-8') as f: 
            datos = json.load(f)
        self.cb_libro.set(datos["config"]["libro"])
        self.ent_w.delete(0, tk.END); self.ent_w.insert(0, datos["config"]["w"])
        self.ent_h.delete(0, tk.END); self.ent_h.insert(0, datos["config"]["h"])
        self.ent_min.delete(0, tk.END); self.ent_min.insert(0, datos["config"]["min"])
        self.ent_max.delete(0, tk.END); self.ent_max.insert(0, datos["config"]["max"])
        self.ent_ancla.delete(0, tk.END); self.ent_ancla.insert(0, datos["busqueda"]["ancla"])
        self.notas_celdas = datos.get("notas", {})
        for i, t in enumerate(datos["busqueda"]["extras"]): 
            if i < len(self.entries_extra):
                self.entries_extra[i].delete(0, tk.END)
                self.entries_extra[i].insert(0, t)
        self.texto_actual, self.df_idx = gestor.cargar_recursos(self.ruta_datos, self.cb_libro.get())
        for i in self.tabla.get_children(): self.tabla.delete(i)
        for v in datos["tabla"]: self.tabla.insert("", "end", values=v[:3], tags=v[3])
        self.resultados_secundarios = []
        for i, ent in enumerate(self.entries_extra):
            val = ent.get().strip()
            if val:
                pal = gestor.normalizar_hebreo(val)
                hits, _ = motor.buscar_els_cilindrico(self.texto_actual, pal, int(self.ent_min.get()), int(self.ent_max.get()))
                self.resultados_secundarios.append({"palabra": pal, "hits": hits, "color": self.colores_extra[i]})
        seleccion_previa = datos.get("seleccion")
        if seleccion_previa:
            target_tags = list(seleccion_previa)
            for item in self.tabla.get_children():
                if list(self.tabla.item(item, "tags")) == target_tags:
                    self.tabla.selection_set(item); self.tabla.focus(item); self.actualizar_visor(None); break

    def salir_programa(self):
        if messagebox.askokcancel("Salir", "¿Desea cerrar el programa?"): self.ventana.destroy(); os._exit(0)

    def limpiar_entry(self, entry): entry.delete(0, tk.END)
    def ordenar_columna(self, col, reverse):
        l = [(self.tabla.set(k, col), k) for k in self.tabla.get_children('')]
        try: l.sort(key=lambda t: float(t[0]), reverse=reverse)
        except ValueError: l.sort(reverse=reverse)
        for index, (val, k) in enumerate(l): self.tabla.move(k, '', index)
        self.tabla.heading(col, command=lambda: self.ordenar_columna(col, not reverse))

    def limpiar_todo(self):
        self.ent_ancla.delete(0, tk.END); self.ent_local.delete(0, tk.END)
        for ent in self.entries_extra: ent.delete(0, tk.END)
        for i in self.tabla.get_children(): self.tabla.delete(i)
        for f in range(self.MAX_F):
            for c in range(self.MAX_C + 2): self.celdas[f][c].config(text="", bg="white", fg="black"); self.celdas[f][c].grid_remove()
        self.limpiar_busqueda_local(); self.matriz_actual_letras = []; self.matriz_actual_indices = []; self.notas_celdas = {}
        self.lbl_info_matriz.config(text="Seleccione un resultado para ver la matriz", bg="#ffffff", fg="black")
        self.canvas_matriz.config(scrollregion=(0, 0, 0, 0))

    def set_division(self, d): self.division_actual = d; self.actualizar_visor(None)
    def ajustar_rango_local(self, delta):
        nv = self.rango_local + delta
        if 1 <= nv <= 20: self.rango_local = nv; self.lbl_rango_val.config(text=str(nv))

    def set_foco(self, entry): self.ultimo_foco = entry
    def abrir_teclado(self): TecladoHebreo(self.ventana, self.insertar_letra, self.borrar_letra)
    def insertar_letra(self, letra): 
        if self.ultimo_foco: self.ultimo_foco.insert(tk.INSERT, letra)
    def borrar_letra(self):
        if self.ultimo_foco:
            pos = self.ultimo_foco.index(tk.INSERT)
            if pos > 0: self.ultimo_foco.delete(pos-1, pos)

    def ajustar_dim(self, entry, delta):
        try:
            val = int(entry.get()); nv = max(5, min(self.MAX_C, val + delta))
            entry.delete(0, tk.END); entry.insert(0, str(nv)); self.actualizar_visor(None)
        except: pass

    def cambiar_fuente(self, delta):
        self.font_size = max(6, min(72, self.font_size + delta))
        for f in range(self.MAX_F):
            for c in range(self.MAX_C + 2): self.celdas[f][c].config(font=("Courier New", self.font_size))
        self.actualizar_visor(None)

    def actualizar_visor(self, event):
        if not self.tabla.selection(): return
        item = self.tabla.selection()[0]; p_ini, s_anc = self.tabla.item(item, "tags")
        try: 
            W = min(int(self.ent_w.get()), self.MAX_C)
            H_v = min(int(self.ent_h.get()), self.MAX_F)
        except: return 
        S, P = int(s_anc), int(p_ini)
        
        # --- Lógica de obtención de matriz ---
        factor = self.division_actual + 1; S_v = S // factor if self.division_actual > 0 else S
        if S_v == 0: S_v = 1 if S > 0 else -1
        pal_a = gestor.normalizar_hebreo(self.ent_ancla.get())
        matriz, m_idx, _, _ = motor.obtener_matriz_vertical_fija(self.texto_actual, P, S_v, W, 80)
        self.matriz_actual_letras, self.matriz_actual_indices = matriz, m_idx
        filas_obtenidas = len(m_idx)        
        self.dicc_pos_rapida = {m_idx[f][c]: (f, c) for f in range(filas_obtenidas) for c in range(W)}
        
        # Calcular desfase visual (f_ini)
        lv = len(pal_a) + (len(pal_a)-1)*self.division_actual
        f_ini = int(((80//2) + (lv/2 if S>=0 else -lv/2)) - (H_v/2))

        # Limpiar celdas antes de pintar
        for f in range(self.MAX_F):
            for c in range(self.MAX_C + 2): 
                self.celdas[f][c].config(text="", bg="white", fg="black"); self.celdas[f][c].grid_remove()

        # Dibujar caracteres base y referencias
        for fg in range(H_v):
            fr = f_ini + fg
            if 0 <= fr < filas_obtenidas and fg < self.MAX_F:
                self.celdas[fg][0].config(text=gestor.obtener_referencia(self.df_idx, m_idx[fr][W-1]), fg="gray", bg="#f8f8f8", width=18, anchor="w"); self.celdas[fg][0].grid()
                for c in range(W):
                    col_vis = W - c
                    if col_vis <= self.MAX_C:
                        self.celdas[fg][col_vis].config(text=matriz[fr][c], width=2); self.celdas[fg][col_vis].grid()
                if W + 1 < self.MAX_C + 2:
                    self.celdas[fg][W+1].config(text=gestor.obtener_referencia(self.df_idx, m_idx[fr][0]), fg="gray", bg="#f8f8f8", width=18, anchor="e"); self.celdas[fg][W+1].grid()

        # --- PINTADO ESTRICTO DE ANCLA ---
        indices_ancla = [(P + (i * S)) % len(self.texto_actual) for i in range(len(pal_a))]
        # Solo pintamos si TODA la palabra está en el diccionario de la matriz
        if all(idx in self.dicc_pos_rapida for idx in indices_ancla):
            for idx in indices_ancla:
                fm, mc = self.dicc_pos_rapida[idx]
                f_vis = fm - f_ini
                if 0 <= f_vis < H_v: 
                    self.celdas[f_vis][W - mc].config(bg="yellow")

        # --- PINTADO ESTRICTO DE BÚSQUEDAS EXTRA ---
        for g in self.resultados_secundarios:
            for h in g["hits"]:
                idxs = [(h["letra_ini"] + (i * h["salto"])) % len(self.texto_actual) for i in range(len(g["palabra"]))]
                # VERIFICACIÓN CLAVE: que todos los índices existan y estén en el rango visual vertical
                if all(id in self.dicc_pos_rapida for id in idxs):
                    # Segunda verificación: ¿Están todas las letras dentro de las filas visibles (f_ini a f_ini + H_v)?
                    if all(0 <= (self.dicc_pos_rapida[id][0] - f_ini) < H_v for id in idxs):
                        for id in idxs:
                            fm, mc = self.dicc_pos_rapida[id]
                            f_vis, c_vis = fm - f_ini, W - mc
                            if 0 <= f_vis < H_v and 0 < c_vis <= self.MAX_C: 
                                self.celdas[f_vis][c_vis].config(bg=g["color"])
        
    def ejecutar_busqueda_local(self):
        pal = gestor.normalizar_hebreo(self.ent_local.get().strip())
        if not pal or not self.matriz_actual_letras: return
        H_v, W = int(self.ent_h.get()), int(self.ent_w.get())
        item = self.tabla.selection()[0]; _, s_anc = self.tabla.item(item, "tags")
        pal_ancla_norm = gestor.normalizar_hebreo(self.ent_ancla.get())
        lv = len(pal_ancla_norm) + (len(pal_ancla_norm)-1)*self.division_actual
        f_ini = int(((80//2) + (lv/2 if int(s_anc)>=0 else -lv/2)) - (H_v/2))
        filas_m = len(self.matriz_actual_letras)
        m_n = [[gestor.normalizar_hebreo(lt) for lt in f] for f in self.matriz_actual_letras]
        enc = False
        for f1 in range(filas_m):
            for c1 in range(W):
                if m_n[f1][c1] == pal[0]:
                    for df in range(-self.rango_local, self.rango_local+1):
                        for dc in range(-self.rango_local, self.rango_local+1):
                            if df==0 and dc==0: continue
                            pts = []
                            for i in range(len(pal)):
                                nf, nc = f1+(i*df), c1+(i*dc)
                                if 0<=nf<filas_m and 0<=nc<W and m_n[nf][nc]==pal[i]: pts.append((nf,nc))
                                else: break
                            if len(pts) == len(pal):
                                v = True
                                for mf, mc in pts:
                                    if not (0 <= mf-f_ini < H_v): v = False; break
                                if v:
                                    for mf, mc in pts: 
                                        if (W-mc) <= self.MAX_C: self.celdas[mf-f_ini][W-mc].config(bg=self.colores_local[self.idx_color_local_persistente % 6], fg="white")
                                    enc = True
        if enc: self.idx_color_local_persistente += 1

    def limpiar_busqueda_local(self):
        for f in range(self.MAX_F):
            for c in range(self.MAX_C + 2):
                if self.celdas[f][c].cget("bg") in self.colores_local: self.celdas[f][c].config(bg="white", fg="black")

    def procesar(self):
        try:
            st = time.time(); self.btn_run.config(text="BUSCANDO...", state="disabled")
            self.texto_actual, self.df_idx = gestor.cargar_recursos(self.ruta_datos, self.cb_libro.get())
            s_min, s_max, W, H = int(self.ent_min.get()), int(self.ent_max.get()), int(self.ent_w.get()), int(self.ent_h.get())
            pal_a = gestor.normalizar_hebreo(self.ent_ancla.get().strip())
            res_a, _ = motor.buscar_els_cilindrico(self.texto_actual, pal_a, s_min, s_max)
            self.resultados_secundarios = []
            for i, ent in enumerate(self.entries_extra):
                if ent.get().strip():
                    p = gestor.normalizar_hebreo(ent.get().strip())
                    h, _ = motor.buscar_els_cilindrico(self.texto_actual, p, s_min, s_max)
                    self.resultados_secundarios.append({"palabra": p, "hits": h, "color": self.colores_extra[i]})
            for i in self.tabla.get_children(): self.tabla.delete(i)
            for r in res_a:
                num_e = 0
                _, m_idx, _, _ = motor.obtener_matriz_vertical_fija(self.texto_actual, r['letra_ini'], r['salto'], W, H)
                vis = {idx for fila in m_idx for idx in fila}
                for g in self.resultados_secundarios:
                    for h in g["hits"]:
                        if all((h["letra_ini"] + (i*h["salto"])) % len(self.texto_actual) in vis for i in range(len(g["palabra"]))): num_e += 1
                self.tabla.insert("", "end", values=(r['salto'], num_e, gestor.obtener_referencia(self.df_idx, r['letra_ini'])), tags=(r['letra_ini'], r['salto']))
            self.lbl_timer.config(text=f"Tiempo: {time.time()-st:.2f}s"); self.btn_run.config(text="BUSCAR ENCUENTROS", state="normal")
        except Exception as e: self.btn_run.config(text="BUSCAR ENCUENTROS", state="normal"); messagebox.showerror("Error", str(e))

    def exportar_matriz_csv(self):
        archivo = filedialog.asksaveasfilename(defaultextension=".csv")
        if not archivo or not self.matriz_actual_letras: return
        try:
            W = int(self.ent_w.get())
            H = int(self.ent_h.get())
            pal_a = self.ent_ancla.get()
            libro = self.cb_libro.get()
            seleccion = self.tabla.selection()
            if seleccion:
                item = seleccion[0]
                _, s_anc = self.tabla.item(item, "tags")
            else:
                s_anc = "N/A"
            encabezado_texto = f"ANCLA: {pal_a}  |  LIBRO: {libro}  |  SALTO: {s_anc}"
            with open(archivo, mode='w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow([encabezado_texto])
                writer.writerow([])
                for f_idx in range(H):
                    fila_datos = []
                    for c_idx in range(W + 2):
                        celda = self.celdas[f_idx][c_idx]
                        texto = celda.cget("text")
                        if celda.winfo_viewable() or texto != "":
                            fila_datos.append(texto)
                    if fila_datos:
                        writer.writerow(fila_datos)
            messagebox.showinfo("Éxito", "Matriz exportada a CSV correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar el CSV: {e}")

    def exportar_matriz_html(self):
        archivo = filedialog.asksaveasfilename(defaultextension=".html")
        if not archivo or not self.matriz_actual_letras: return
        try:
            W = int(self.ent_w.get())
            H = int(self.ent_h.get())
            pal_a = gestor.normalizar_hebreo(self.ent_ancla.get())
            libro = self.cb_libro.get()
            seleccion = self.tabla.selection()
            if not seleccion:
                messagebox.showwarning("Aviso", "Seleccione un resultado en la tabla antes de exportar.")
                return
            item = seleccion[0]
            _, s_anc = self.tabla.item(item, "tags")
        except Exception as e: 
            messagebox.showerror("Error", f"Error al preparar datos: {e}")
            return
        html = f"""
        <html>
        <head>
            <meta charset='UTF-8'>
            <style>
                body {{ 
                    background-color: #f0f7f0; 
                    font-family: 'Segoe UI', sans-serif; 
                    padding: 40px; 
                    display: flex; 
                    flex-direction: column; 
                    align-items: center; 
                }}
                .header-card {{
                    background: #ffffff;
                    padding: 20px 40px;
                    border-radius: 12px;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.05);
                    border-left: 6px solid #2e7d32;
                    margin-bottom: 30px;
                    text-align: center;
                    min-width: 600px;
                }}
                .header-card h2 {{ margin: 0; color: #1b5e20; font-size: 22px; }}
                .header-card p {{ margin: 8px 0 0; color: #666; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; }}
                table {{
                    border-collapse: separate;
                    border-spacing: 2px;
                    background-color: #ffffff;
                    padding: 25px;
                    border-radius: 10px;
                    box-shadow: 0 15px 35px rgba(0,0,0,0.1);
                }}
                td {{
                    width: 32px;
                    height: 32px;
                    text-align: center;
                    font-family: 'Courier New', monospace;
                    font-size: 18px;
                    font-weight: bold;
                    border-radius: 4px;
                    border: 1px solid #f0f0f0;
                }}
                .ref {{
                    font-size: 11px;
                    color: #2e7d32;
                    background-color: #e8f5e9 !important;
                    min-width: 150px;
                    padding: 0 12px;
                }}
            </style>
        </head>
        <body>
            <div class='header-card'>
                <h2>INFORME DE BÚSQUEDA ELS</h2>
                <p>ANCLA: <b>{pal_a}</b> &nbsp;|&nbsp; LIBRO: <b>{libro}</b> &nbsp;|&nbsp; SALTO: <b>{s_anc}</b></p>
            </div>
            <table>
        """
        for f_idx in range(H):
            html += "<tr>"
            for c_idx in range(W + 2):
                celda = self.celdas[f_idx][c_idx]
                texto = celda.cget("text")
                bg_color = celda.cget("bg")
                fg_color = celda.cget("fg")
                es_ref = (c_idx == 0 or c_idx == W + 1)
                if es_ref:
                    clase = "class='ref'"
                    estilo_celda = "" 
                else:
                    clase = ""
                    if bg_color.lower() in ["white", "#ffffff", "systembuttonface"]:
                        estilo_celda = f"background-color: #ffffff; color: {fg_color};"
                    else:
                        estilo_celda = f"background-color: {bg_color}; color: {fg_color};"
                if celda.winfo_viewable() or texto != "":
                    html += f"<td {clase} style='{estilo_celda}'>{texto}</td>"
            html += "</tr>"
        html += "</table></body></html>"
        try:
            with open(archivo, "w", encoding="utf-8") as f: 
                f.write(html)
            messagebox.showinfo("Éxito", "Matriz exportada a HTML correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar: {e}")

if __name__ == "__main__":
    root = tk.Tk(); app = AplicacionELS(root); root.mainloop()
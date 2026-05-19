import os
import pandas as pd
import numpy as np
import re

MAPA_LIBROS = {
    # TORA (Instrucción)
    1: "Génesis", 2: "Éxodo", 3: "Levítico", 4: "Números", 5: "Deuteronomio",
    
    # NEVI'IM (Profetas)
    6: "Josué", 7: "Jueces", 8: "1 Samuel", 9: "2 Samuel", 10: "1 Reyes", 
    11: "2 Reyes", 12: "Isaías", 13: "Jeremías", 14: "Ezequiel", 15: "Oseas", 
    16: "Joel", 17: "Amós", 18: "Abdías", 19: "Jonás", 20: "Miqueas", 
    21: "Nahum", 22: "Habacuc", 23: "Sofonías", 24: "Hageo", 25: "Zacarías", 
    26: "Malaquías",
    
    # KETUVIM (Escritos)
    27: "Salmos", 28: "Proverbios", 29: "Job", 30: "Cantares", 31: "Rut", 
    32: "Lamentaciones", 33: "Eclesiastés", 34: "Ester", 35: "Daniel", 
    36: "Esdras", 37: "Nehemías", 38: "1 Crónicas", 39: "2 Crónicas",
    
    # ARCHIVOS ESPECIALES
    40: "Torah", 41: "Tanaj"
}

def normalizar_hebreo(texto):
    """Elimina signos masoréticos (Nequdot) y convierte letras Sofit (finales) en normales."""
    if not texto:
        return ""
        
    # 1. ELIMINAR VOCALES Y DIACRÍTICOS HEBREOS (Rango Unicode \u0591 a \u05C7)
    texto_sin_vocales = re.sub(r'[\u0591-\u05C7]', '', texto)
    
    # 2. NORMALIZAR LETRAS SOFIT (Tu lógica existente intacta)
    # ך -> כ, ם -> מ, ן -> נ, ף -> פ, ץ -> צ
    tab_sofit = str.maketrans("ךםןףץ", "כמנפצ")
    return texto_sin_vocales.translate(tab_sofit)

def cargar_recursos(ruta_base, nombre_libro):
    r_bin = os.path.join(ruta_base, f"{nombre_libro.lower()}.bin")
    r_csv = os.path.join(ruta_base, f"{nombre_libro.lower()}.csv")
    
    if not os.path.exists(r_bin):
        raise FileNotFoundError(f"No existe: {r_bin}")

    with open(r_bin, 'r', encoding='utf-8') as f:
        contenido = f.read()
        
        # 1. Normalizamos las Sofit y removemos diacríticos del archivo binario
        contenido_norm = normalizar_hebreo(contenido)
        
        # 2. FILTRO CRÍTICO: Solo dejamos caracteres hebreos consonánticos
        texto_limpio = "".join(re.findall(r'[\u0590-\u05FF]', contenido_norm))
        
    if not texto_limpio:
        # Fallback para archivos sin rango unicode específico
        texto_limpio = "".join(contenido_norm.split())
        
    texto_array = np.array(list(texto_limpio), dtype='U1').view(np.uint32)
    df = pd.read_csv(r_csv, names=['posicion', 'libro', 'capitulo', 'versiculo'], header=0)
    
    return texto_array, df

def obtener_referencia(df_indices, pos_letra):
    idx = df_indices['posicion'].searchsorted(pos_letra, side='right') - 1
    row = df_indices.iloc[max(0, min(idx, len(df_indices) - 1))]
    nombre = MAPA_LIBROS.get(int(row['libro']), f"Libro {int(row['libro'])}")
    return f"{nombre} {int(row['capitulo'])}:{int(row['versiculo'])}"
import os
import pandas as pd
import numpy as np
import re

MAPA_LIBROS = {1: "Génesis", 2: "Éxodo", 3: "Levítico", 4: "Números", 5: "Deuteronomio", 6: "Torah"}

def normalizar_hebreo(texto):
    """Convierte letras Sofit (finales) en sus versiones normales."""
    # ך -> כ, ם -> מ, ן -> נ, ף -> פ, ץ -> צ
    tab_sofit = str.maketrans("ךםןףץ", "כמנפצ")
    return texto.translate(tab_sofit)

def cargar_recursos(ruta_base, nombre_libro):
    r_bin = os.path.join(ruta_base, f"{nombre_libro.lower()}.bin")
    r_csv = os.path.join(ruta_base, f"{nombre_libro.lower()}.csv")
    
    if not os.path.exists(r_bin):
        raise FileNotFoundError(f"No existe: {r_bin}")

    with open(r_bin, 'r', encoding='utf-8') as f:
        contenido = f.read()
        
        # 1. Normalizamos las Sofit que puedan venir en el archivo original
        contenido_norm = normalizar_hebreo(contenido)
        
        # 2. FILTRO CRÍTICO: Solo dejamos caracteres hebreos
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
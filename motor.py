import numpy as np
import time

def buscar_els_cilindrico(texto_array, palabra, r_min, r_max):
    if not palabra: return [], 0
    buscada = np.array(list(palabra), dtype='U1').view(np.uint32)
    n_palabra = len(buscada)
    longitud_texto = len(texto_array)
    posiciones_iniciales = np.where(texto_array == buscada[0])[0]
    saltos = [s for s in range(r_min, r_max + 1) if s != 0]
    resultados = []
    inicio_tiempo = time.time()

    for salto in saltos:
        indices_activos = posiciones_iniciales
        for i in range(1, n_palabra):
            pos_a_revisar = (indices_activos + (i * salto)) % longitud_texto
            indices_activos = indices_activos[texto_array[pos_a_revisar] == buscada[i]]
            if indices_activos.size == 0: break
        for h in indices_activos:
            resultados.append({"salto": salto, "letra_ini": int(h)})

    resultados.sort(key=lambda x: abs(x['salto']))
    return resultados, time.time() - inicio_tiempo

def obtener_matriz_vertical_fija(texto_array, pos_ini, salto, ancho_umbral, alto_umbral):
    longitud = len(texto_array)
    matriz = []
    indices_matriz = [] 
    centro_x = ancho_umbral // 2
    centro_y = alto_umbral // 2
    
    for f in range(alto_umbral):
        fila_chars = []
        fila_indices = []
        distancia_v = f - centro_y
        indice_fila = (pos_ini + (distancia_v * abs(salto))) % longitud
        
        for c in range(ancho_umbral):
            distancia_h = c - centro_x
            idx = (indice_fila + distancia_h) % longitud
            fila_chars.append(chr(texto_array[idx]))
            fila_indices.append(idx)
        matriz.append(fila_chars)
        indices_matriz.append(fila_indices)
        
    return matriz, indices_matriz, centro_x, centro_y
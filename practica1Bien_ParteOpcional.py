#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 28 18:29:51 2023

@author: Pedro Corral Ortiz-Coronado
"""

from multiprocessing import Process
from multiprocessing import Semaphore #BoundedSemaphore , Lock
from multiprocessing import current_process
from multiprocessing import Value, Array
from time import sleep
import random


NPROD=6
N=5


def delay(factor = 3):
    sleep(random.random()/factor)



def producir_y_guardar(valor, array, i):
    a_sumar=random.randint(1,10)
    
    valor+=a_sumar
    delay(6)

    array[i]=valor
    
    return valor
    
def productor(array, nonEmpty):
    valor=0
    
    for i in range(N):
        
        valor=producir_y_guardar(valor, array,i)
        
        print(f'Produciendo {current_process().name} el valor {valor}', flush=True)
        
        
        nonEmpty.release()
        
        # delay(6)

"""
NO SÉ POR QUÉ NO ME PERMITE HACER UN DELAY PARA QUE NO SE PRODUZCAN TODOS LOS ELEMENTOS ANTES DE QUE SE ALMACENEN
"""
        


def coger_menor(indices_array_prod, array_prods):
    i=0
    prod_min=-1
    valor_min=-1
    terminado= True
    #Filtramos aquellos productores que ya hayan terminado
    while i<NPROD and terminado:
        ind_i=indices_array_prod[i].value
        
        if ind_i!=N:
            terminado=False
            prod_min=i
            valor_min=array_prods[i][ind_i]
        i+=1
    
    for j in range(i,NPROD):
        ind_j=indices_array_prod[j].value
        if ind_j!=N:
            valor_j=array_prods[j][ind_j]
            if valor_j<valor_min:
                valor_min, prod_min=valor_j, j
    return (terminado, prod_min,valor_min)
        
        
    
def guardar_almacen(almacen, indice_alm ,valor_min):
    almacen[(indice_alm.value)]=valor_min
    v=indice_alm.value+1
    indice_alm.value=v
        

def organizador(almacen, indice_alm, semaforos_non_empty, indices_array_prod, array_prods):
    
    for j in range(NPROD):
        semaforos_non_empty[j].acquire()
    
    terminado=False
    
    while not terminado:
        
        (terminado, prod_min, valor_min)=coger_menor(indices_array_prod, array_prods)
        
        if not terminado:
            
            print(f"Guardamos el valor {valor_min} del productor {prod_min}", flush=True)
            
            guardar_almacen(almacen, indice_alm ,valor_min)
            
            v=indices_array_prod[prod_min].value+1
            indices_array_prod[prod_min].value=v
            if v<N:
                semaforos_non_empty[prod_min].acquire()
            
            # delay()
        else:
            print("Hemos terminado")

    
def main():
    
    almacen= Array('i', NPROD*N)
    
    print ("Almacen INICIAL", almacen[:])
    
    indice_alm = Value('i', 0)
    
    indices_array_prod=[Value('i', 0) for i in range(NPROD)]
    
    array_prods=[Array('i',N) for i in range(NPROD)]
    
    #Los inicializamos con valor -2 en todas sus posiciones
    for array in array_prods:
        for i in range(N):
            array[i]=-2
    
    print("Los buffers de los productores INICIALES:")
    for cont in range(NPROD):
        array=array_prods[cont]
        print("Productor",cont, "Buffer", array[:])
        
    semaforos_non_empty=[Semaphore(0) for i in range(NPROD)]
    
    prodlst = [ Process(target=productor,
                        name=f'prod_{i}',
                        args=(array_prods[i],semaforos_non_empty[i]))
                for i in range(NPROD) ]
    
    organiz=Process(target=organizador,
                      name="merger",
                      args=(almacen, indice_alm, semaforos_non_empty, indices_array_prod, array_prods))

    
    for p in prodlst + [organiz]:
        p.start()

    for p in prodlst + [organiz]:
        p.join()

    print ("Almacen FINAL", almacen[:],"Índice del almacen", indice_alm.value)
    
    print("Los buffers de los productores FINALES:")
    for cont in range(NPROD):
        array=array_prods[cont]
        print("Productor",cont, "Buffer", array[:])
    
if __name__ == '__main__':
    main()
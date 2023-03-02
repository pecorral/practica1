#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 28 18:29:51 2023

@author: Pedro Corral Ortiz-Coronado
"""

from multiprocessing import Process, Manager
from multiprocessing import Semaphore, BoundedSemaphore #, Lock
from multiprocessing import current_process
from multiprocessing import Value, Array
from time import sleep
import random


NPROD=6
N=10        #Numero de elementos que tiene que producir cada productor
K=2         #Tamaño de los buffer


def delay(factor = 3):
    sleep(random.random()/factor)



def producir_y_guardar(valor, array, i):
    a_sumar=random.randint(1,10)
    valor+=a_sumar
    
    delay(6)

    array[i]=valor
    return valor
    
def productor(array, nonEmpty, nonFull):
    valor=0
    
    for i in range(N):
        
        nonFull.acquire()
        valor=producir_y_guardar(valor, array,(i%K))
        print(f'Produciendo {current_process().name} el valor {valor}', flush=True)
        nonEmpty.release()
    
    #Ahora tenemos que dejarlo a -1 para indicar que hemos terminado de producir
    nonFull.acquire()
    array[(N%K)]=-1
    print(f'Prductor {current_process().name} ha TERMINADO de producir', flush=True)
    nonEmpty.release()
        


def coger_menor(indices_array_prod, array_prods):
    i=0
    prod_min=-1
    valor_min=-1
    terminado= True
    #Filtramos aquellos productores que ya hayan terminado
    while i<NPROD and terminado:
        ind_i=indices_array_prod[i].value
        valor_i=array_prods[i][ind_i]
        if valor_i!=-1:
            terminado=False
            prod_min=i
            valor_min=valor_i
        i+=1
    #Si hay alguno sin terminar escogemos el minimo valor producido
    for j in range(i,NPROD):
        ind_j=indices_array_prod[j].value
        valor_j=array_prods[j][ind_j]
        if valor_j>=0 and valor_j<valor_min:
                valor_min, prod_min=valor_j, j
    return (terminado, prod_min,valor_min)
        
        

    
def guardar_almacen_y_actualizar_indices(almacen, valor_min, indices_array_prod, prod_min):
    almacen.append(valor_min)
    #Actualizamos el indice del productor que ha producido el valor minimo (prod_min)
    w=(indices_array_prod[prod_min].value+1)%K
    indices_array_prod[prod_min].value=w 


def organizador(almacen, semaforos_non_empty,semaforos_non_full, indices_array_prod, array_prods):    
    for j in range(NPROD):
        semaforos_non_empty[j].acquire()
    
    terminado=False
    
    while not terminado:
        
        (terminado, prod_min, valor_min)=coger_menor(indices_array_prod, array_prods)
        
        if not terminado:
            
            print(f"Guardamos el valor {valor_min} del productor {prod_min}", flush=True)
            
            guardar_almacen_y_actualizar_indices(almacen, valor_min, indices_array_prod, prod_min)

            semaforos_non_full[prod_min].release()
            
            semaforos_non_empty[prod_min].acquire()
            

        else:
            print("Hemos terminado")

    
def main():
    
    a= Manager()
    almacen=a.list()
    
    print ("Almacen INICIAL", almacen[:])
    

    indices_array_prod=[Value('i', 0) for i in range(NPROD)]
    
    array_prods=[Array('i',K) for i in range(NPROD)]
    
    #Los inicializamos con valor -2 en todas sus posiciones
    for array in array_prods:
        for i in range(K):
            array[i]=-2
    
    print("Los buffers de los productores INICIALES:")
    for cont in range(NPROD):
        array=array_prods[cont]
        print("Productor",cont, "Buffer", array[:])
        
    semaforos_non_empty=[Semaphore(0) for i in range(NPROD)]
    
    semaforos_non_full=[BoundedSemaphore(K) for i in range(NPROD)]
    
    prodlst = [ Process(target=productor,
                        name=f'prod_{i}',
                        args=(array_prods[i],semaforos_non_empty[i],semaforos_non_full[i]))
                for i in range(NPROD) ]
    
    organiz=Process(target=organizador,
                      name="merger",
                      args=(almacen, semaforos_non_empty, semaforos_non_full, indices_array_prod, array_prods))

    
    for p in prodlst + [organiz]:
        p.start()

    for p in prodlst + [organiz]:
        p.join()

    print ("Almacen FINAL", almacen[:], "Contiene", len(almacen), "elementos")
    
    print("Los buffers de los productores FINALES:")
    for cont in range(NPROD):
        array=array_prods[cont]
        print("Productor",cont, "Buffer", array[:])
    
if __name__ == '__main__':
    main()
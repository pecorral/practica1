#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 23 09:07:19 2023

@author: Pedro Corral Ortiz-Coronado
"""

from multiprocessing import Process
from multiprocessing import BoundedSemaphore, Semaphore #,Lock
from multiprocessing import current_process
from multiprocessing import Value, Array
# from time import sleep
import random


NPROD=6
N=5


def producir(valor):
    nuevo_num=valor.value+ random.randint(1,10)
    valor.value=nuevo_num
    
    
def productor(nonEmpty, nonFull, valor):
    for i in range(N):
        nonFull.acquire()
        print(f"Produciendo {current_process().name}")
        producir(valor)
        nonEmpty.release()
    #Ahora tenemos que dejarlo a -1 para indicar que hemos terminado de producir
    nonFull.acquire()
    print(f'{current_process().name} ha terminado de producir')
    valor.value=-1
    nonEmpty.release()
    

def coger_menor(valores):
    i=0
    ind_min=-1
    valor_min=-1
    terminado=True
    while  i<len(valores) and terminado:
        valor_i=valores[i].value
        if valor_i!= -1:
            terminado=False
            valor_min=valor_i
            ind_min=i
        i+=1
    for j in range(i,len(valores)):
        valor_j=valores[j].value
        if valor_j>=0 and valor_j<valor_min:
            ind_min,valor_min=j,valor_j
    return (terminado, ind_min,valor_min)


def guardar_almacen(almacen, indice, valor_min):
    almacen[(indice.value)]=valor_min
    v=indice.value+1
    indice.value=v
    
    
def organizador(almacen,indice, semaforos_non_empty,semaforos_non_full,valores):    
    for i in range(NPROD):
        semaforos_non_empty[i].acquire()
    terminado=False
    while not terminado:
        (terminado,ind_min,valor_min)=coger_menor(valores)
        if not terminado:
            print(f"Guardamos el valor {valor_min}")
            guardar_almacen(almacen, indice ,valor_min)
            semaforos_non_full[ind_min].release()
            semaforos_non_empty[ind_min].acquire()
        else:
            print("Hemos terminado")


def main():
    
    almacen= Array('i', NPROD*N)
    
    print ("Almacen INICIAL", almacen[:])
    
    indice = Value('i', 0)
    
    valores=[Value('i',-2) for i in range(NPROD)]
    
    semaforos_non_empty=[Semaphore(0) for i in range(NPROD)]
    
    semaforos_non_full=[BoundedSemaphore(1) for i in range(NPROD)]
    
    prodlst = [ Process(target=productor,
                        name=f'prod_{i}',
                        args=(semaforos_non_empty[i],semaforos_non_full[i],valores[i]))
                for i in range(NPROD) ]
    
    organiz=Process(target=organizador,
                      name="merger",
                      args=(almacen,indice,semaforos_non_empty,semaforos_non_full,valores))

    
    for p in prodlst + [organiz]:
        p.start()

    for p in prodlst + [organiz]:
        p.join()

    print ("Almacen FINAL", almacen[:],"Índice", indice.value)
    

    
if __name__ == '__main__':
    main()
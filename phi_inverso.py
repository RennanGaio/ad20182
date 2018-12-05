# -*- coding: utf-8 -*-

import numpy as np
import math

def calc_exp(lamb):

    resultados=[]
    #gera um numero aleatorio entre 0 e 1, que sera o valor da pdf da exponencial
    for i in xrange(10000):
        n=np.random.rand()
    #calcula a função inversa da exponencial, para a partir do valor da pdf obter o valor de x referente ao tempo
        resultados.append(-math.log(1-n)/lamb)
    return np.mean(resultados)


if __name__ == '__main__':
    print calc_exp(0.5)
    print "2"

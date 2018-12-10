#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""trabSimulacao.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1ha-n9OE7WEfsYeEkUKceIiahgD1-KPON

# Trabalho de Simulação MAB-515
## Grupo:


*   **Alexandre Moreira**
*   **Daniel Atkinson**
*   **Rennan Gaio**
"""

import numpy as np
#import matplotlib.pyplot as plt
import time
from scipy import stats
import math
import random
import sys
# %matplotlib inline

class Fregues:
    #rodada é uma variável que nos indicará em qual rodada o freguês chegou na fila
    #rodada == -1 indica que freguês entrou no sistema na fase transiente
    def __init__(self, tempo: float, rodada: int):
        #variáveis que indicam marcos no tempo
        self.tempo_chegada = tempo
        self.tempo_comeco_servico: float
        self.tempo_termino_servico: float

        #variáveis que indicam duração
        self.tempo_em_servico: float
        self.tempo_em_espera: float
        self.tempo_total: float

        #variável que indica se cliente já entrou em serviço
        self.entrou_em_servico = False

        #variável que indica se cliente já terminou o servico
        self.terminou_servico = False

    def entraEmServico(self, tempo_comeco_servico: float):
        self.tempo_comeco_servico = tempo_comeco_servico
        self.entrou_em_servico = True

        #calcula o tempo que o freguês ficou em espera
        self.tempo_em_espera = self.tempo_comeco_servico - self.tempo_chegada

    def terminaServico(self, tempo_termino_servico: float):
        self.tempo_termino_servico = tempo_termino_servico
        self.terminou_servico = True

        #calcula o tempo que o freguês ficou em servico
        self.tempo_em_servico = self.tempo_termino_servico - self.tempo_comeco_servico

        #calcula o tempo total que o freguês ficou no sistema
        self.tempo_total = self.tempo_em_espera + self.tempo_em_servico



class EntradaLista:
    #evento == 0 indica chegada à fila
    #evento == 1 indica começo de serviço
    #evento == 2 indica término de serviço
    def __init__(self, evento: int, fregues: Fregues):
        self.evento = evento
        self.fregues = fregues
        if (evento == 0):
            self.tempo = fregues.tempo_chegada
        elif (evento == 1):
            self.tempo = fregues.tempo_comeco_servico
        else:
            self.tempo = fregues.tempo_termino_servico



class Fila:
    #IC é o intervalo de confiança
    #n é o número de rodadas de simulação
    #tipo_fila == 0 indica política FCFS
    #tipo_fila == 1 indica política LCFS
    #k é o número de coletas por rodada
    def __init__(self, tx_chegada: float, tx_servico: float, k: int, n: int, tipo_fila: int, IC: float, precisao: float, utilizacao: float):

        #flag que indica se ainda estamos na fase transiente
        self.__is_transiente = True

        #lista que irá guardar, para cada coleta, na fase __Tq_transiente
        #o tempo na fila de espera
        self.__Tq_transiente = []

        #contador de coletas na fase transiente
        self.__cont_coletas_transiente = 0

        #---------------------------------------------------

        #indica se a fila é FCFS (0) ou LCFS (1)
        self.__tipo_fila = tipo_fila

        #lista que será usada para efetuar o controle dos eventos que podem ocorrer no sistema
        self.__lista = []

        #variável que indica a quantidade de pessoas no sistema atualmente
        self.__n_pessoas_sist = 0

        #variável que indica a quantidade de pessoas na fila de espera atualmente
        self.__n_pessoas_espera = 0

        #variável que indica a quantidade de pessoas em serviço atualmente
        self.__n_pessoas_servico = 0

        self.__tx_chegada = tx_chegada

        self.__tx_servico = tx_servico

        #quantidade de coletas a serem feitas
        self.__k = k

        #quantidade de rodadas a serem feitas
        self.__n = n

        #variável que irá contar a quantidade de coletas feitas com o sistema
        #em equilíbro
        self.__cont_coletas = 0

        #variável que irá contar a quantidade de rodadas feitas
        self.__cont_rodadas = 0

        #matriz que irá guardar o tempo médio de espera na fila
        self.Tq_mean = np.zeros([1, n])

        #matriz que irá guardar o número médio de pessoas na fila de espera
        self.Nq_mean = np.zeros([1, n])

        #variável que irá guardar a área a cada chegada à fila e a cada entrada em serviço
        #nos eventos de interesse
        self.__area = 0

        #variável que irá guardar o tempo de ocorrência
        #do evento de interesse anterior
        self.__tempo_evento_ant = 0

        #variável que irá guardar o tempo de ocorrência
        #do evento de interesse atual
        self.__tempo_evento_atual = 0

    	#variável que irá guardar o tempo total que foi passado na fila de espera por rodada
        self.__tempo_total_espera = 0

  # def IC_da_media(mean_list):
  #   #percentil da T-student para mais de 120 amostras
  #   percentil = 1.645
  #   #qtd de amostras
  #   n = len(mean_list)
  #   #média amostral
  #   mean = np.sum(mean_list)/n
  #   #variancia amostral = SUM((Media - Media Amostral)^2) = S^2
  #   s = math.sqrt(np.sum( [(float(element) - float(mean))**2 for element in mean_list] ) / (n-1.0))
  #   #calculo do Intervalo de Confiança pela T-student
  #   lower = mean - (percentil*(s/math.sqrt(n)))
  #   upper = mean + (percentil*(s/math.sqrt(n)))
  #   center = lower + (upper - lower)/2
  #   if center/10 > (upper - lower):
  #       print "teste não obteve precisao de 5%, intervalo maior do que 10% do valor central"
  #   #retorna o limite inferior, limite superior, o valor central e a precisão, nessa ordem.
  #   return (lower, upper, center, upper/lower)

    def testeFaseTransiente(self):
        #percentil da T-student para mais de 120 amostras
        percentil = 1.645
        #qtd de amostras
        n = len(self.__Tq_transiente)
        #média amostral
        mean = np.sum(self.__Tq_transiente)/n
        #variancia amostral = SUM((Media - Media Amostral)^2) = S^2
        s = math.sqrt(np.sum( [(float(element) - float(mean))**2 for element in self.__Tq_transiente] ) / (n-1.0))
        #calculo do Intervalo de Confiança pela T-student
        lower = mean - (percentil*(s/math.sqrt(n)))
        upper = mean + (percentil*(s/math.sqrt(n)))
        center = lower + (upper - lower)/2
        if center/10 < (upper - lower):
            self.__is_transiente=False

    #função que irá calcular a soma da área (N * tempo) nos eventos de interesse
    def somaArea(self):
        self.__area = self.__area + self.__n_pessoas_espera*(self.__tempo_evento_atual - self.__tempo_evento_ant)
        self.__tempo_evento_ant = self.__tempo_evento_atual

    #função que irá calcular o número médio de pessoas a cada rodada
    def calculaNq(self):
        return self.__area/self.__tempo_total_espera

    #função que irá calcular o tempo médio passado na fila de espera
    def calculaTq(self):
        #dividimos o tempo total na fila de espera pela quantidade de pessoas que passaram por ela
        #como o nosso contador de coletas também é um contador de quantas pessoas entraram em
        #serviço, podemos usá-lo, se somarmos um
        return self.__tempo_total_espera/(self.__cont_coletas + 1)

    #simula o tempo até ocorrência do próximo evento, distribuído exponencialmente
    def simulaTempoAteEvento(self, taxa: float):
        r = random.random()
        tempo = -math.log(r)/taxa
        return tempo

    def controleLista(self):

        #variável que indica se a simulação acabou ou não
        acabou = False

        #chegou uma nova pessoa na fila
        if (self.__lista[-1].evento == 0):
            #preparando para gerar novo evento
            if (self.__n_pessoas_servico == 0):
                #se não tem ninguém sendo servido freguês imediatamente entra em serviço
                fregues = self.__lista[-1].fregues
                fregues.entraEmServico(fregues.tempo_chegada)
                entrada_lista = EntradaLista(1, fregues)

                #queremos continuar a fazer coletas do tempo de cada cliente na fila de espera
                #enquanto estivermos na fase transiente
                if (self.__is_transiente):
                    #se o nosso contador de coletas na fase transiente for menor do que kmin
                    #nós continuamos coletando os tempos
                    self.__Tq_transiente.append(0)
                    if (self.__cont_coletas_transiente >= self.__k):
                        self.testeFaseTransiente()

                if (not self.__is_transiente):
                    #só queremos contabilizar a área dos fregueses dessa rodada
                    #os que são de rodadas anteriores e ainda não terminaram estão no sistema
                    #somente para mantê-lo em equilíbrio
                    if (fregues.rodada == self.__cont_rodadas):
                        self.__cont_coletas += 1

                    #testa se já atingimos a qtd de coletas pra essa rodada
                    if (self.__cont_coletas == self.__k):
                        #podemos calcular o número médio de pessoas na rodada que completamos
                        self.Nq_mean[0,self.__cont_rodadas] = self.calculaNq()
                        self.Tq_mean[0,self.__cont_rodadas] = self.calculaTq()
                        self.__cont_rodadas += 1
                        #resetamos tudo que precisa ser recalculado para essa nova rodada
                        self.__cont_coletas = 0
                        self.__area = 0
                        self.__tempo_total_espera = 0
                        #testa se já atingimos a quantidade de rodadas estipulada
                        if (self.__cont_rodadas == self.__n):
                            acabou = True

            else:
                #se tem alguém em serviço precisamos simular uma chegada e um término de serviço
                #o evento que ocorrer em menor tempo será inserido na lista
                tempo_chegada = self.simulaTempoAteEvento(self.__tx_chegada)
                tempo_termino = self.simulaTempoAteEvento(self.__tx_servico)
                #se chega alguém antes do freguês em serviço terminar
                if (tempo_chegada < tempo_termino):
                    #não podemos esquecer de somar o tempo até a chegada com o tempo que decorreu até o momento
                    #se estivermos na fase transiente ainda precisamos settar o identificador
                    #de rodada do freguês como -1
                    if (self.__is_transiente):
                        fregues = Fregues(tempo_chegada + self.__lista[-1].tempo, -1)
                    else:
                        fregues = Fregues(tempo_chegada + self.__lista[-1].tempo, self.__cont_rodadas)
                    entrada_lista = EntradaLista(0, fregues)

                    #só queremos fazer o cálculo da área quando tivermos saído da fase transiente
                    if(not self.__is_transiente):
                        #devemos calcular as métricas antes de atualizar estado do sistema
                        self.__tempo_evento_ant = self.__tempo_evento_atual
                        self.__tempo_evento_atual = entrada_lista.tempo
                        self.somaArea()

                    self.__n_pessoas_espera += 1
                    self.__n_pessoas_sist += 1

                #se o freguês em serviço termina antes de chegar alguém
                else:
                    #encontramos a entrada correspondente ao freguês que estava em serviço
                    #iremos disparar o evento de término de serviço desse freguês
                    #percorremos a lista começando pela última posição
                    for i in range(len(self.__lista)-1, -1, -1):
                        #o último evento de começo de serviço corresponde ao freguês que está em serviço
                        if (self.__lista[i].evento == 1):
                            fregues = self.__lista[i].fregues
                            break
                    fregues.terminaServico(tempo_termino + self.__lista[-1].tempo)
                    entrada_lista = EntradaLista(2, fregues)
                    self.__n_pessoas_servico -= 1
                    self.__n_pessoas_sist -= 1

        #uma nova pessoa começou a ser servida
        if (self.__lista[-1].evento == 1):
            #preparando para gerar novo evento
            #mesmo caso para quando ocorre uma chegada na fila e já tem alguém em serviço
            tempo_chegada = self.simulaTempoAteEvento(self.__tx_chegada)
            tempo_termino = self.simulaTempoAteEvento(self.__tx_servico)
            if (tempo_chegada < tempo_termino):
                if(self.__is_transiente):
                    fregues = Fregues(tempo_chegada + self.__lista[-1].tempo, -1)
                else:
                    fregues = Fregues(tempo_chegada + self.__lista[-1].tempo, self.__cont_rodadas)
                entrada_lista = EntradaLista(0, fregues)

                #só queremos fazer o cálculo da área quando tivermos saído da fase transiente
                if(not self.__is_transiente):
                    #devemos calcular as métricas antes de atualizar estado do sistema
                    self.__tempo_evento_ant = self.__tempo_evento_atual
                    self.__tempo_evento_atual = entrada_lista.tempo
                    self.somaArea()

                self.__n_pessoas_espera += 1
                self.__n_pessoas_sist += 1
            else:
                for i in range(len(self.__lista)-1, -1, -1):
                    if (self.__lista[i].evento == 1):
                        fregues = self.__lista[i].fregues
                        break
                fregues.terminaServico(tempo_termino + self.__lista[-1].tempo)
                entrada_lista = EntradaLista(2, fregues)
                self.__n_pessoas_servico -= 1
                self.__n_pessoas_sist -= 1

        #uma pessoa acabou de completar seu serviço
        if (self.__lista[-1].evento == 2):
            #preparando para gerar novo evento
            #caso em que tem pelo menos uma pessoa na fila de espera após termino de serviço
            #precisamos botar alguém imediatamente em serviço, dependendo da política
            if (self.__n_pessoas_espera > 0):
                #correponde a FCFS
                if (self.__tipo_fila == 0):
                    for i in range(len(self.__lista)):
                        #queremos encontrar o freguês que entrou há mais tempo na fila que ainda não foi servido
                        if (self.__lista[i].evento == 0 and not self.__lista[i].fregues.entrou_em_servico):
                            fregues = self.__lista[i].fregues
                            break
                #corresponde a LCFS
                else:
                    #percorremos a lista a partir da última entrada
                    for i in range(len(self.__lista)-1, -1, -1):
                        #queremos encontrar o último freguês que entrou na fila e ainda não foi servido
                        if (self.__lista[i].evento == 0 and not self.__lista[i].fregues.entrou_em_servico):
                            fregues = self.__lista[i].fregues
                            break
                #esse freguês entra em serviço imediatamente
                fregues.entraEmServico(self.__lista[-1].tempo)
                entrada_lista = EntradaLista(1, fregues)

                #queremos continuar a fazer coletas do tempo de cada cliente na fila de espera
                #enquanto estivermos na fase transiente
                if (self.__is_transiente):
                    #se o nosso contador de coletas na fase transiente for menor do que kmin
                    #nós continuamos coletando os tempos
                    self.__Tq_transiente.append(fregues.tempo_comeco_servico - fregues.tempo_chegada)
                    if (self.__cont_coletas_transiente >= self.__k):
                        self.testeFaseTransiente()

                if (not self.__is_transiente):
                    #só queremos contabilizar a área dos fregueses dessa rodada
                    #os que são de rodadas anteriores e ainda não terminaram estão no sistema
                    #somente para mantê-lo em equilíbrio
                    if (fregues.rodada == self.__cont_rodadas):
                        self.__tempo_evento_ant = self.__tempo_evento_atual
                        self.__tempo_evento_atual = entrada_lista.tempo
                        self.somaArea()
                        self.__tempo_total_espera = self.__tempo_total_espera + self.__lista[-1].fregues.tempo_comeco_servico - self.__lista[-1].fregues.tempo_chegada
                        self.__cont_coletas += 1

                    #testa se já atingimos a qtd de coletas pra essa rodada
                    if (self.__cont_coletas == self.__k):
                        #podemos calcular o número médio de pessoas na rodada que completamos
                        self.Nq_mean[0,self.__cont_rodadas] = self.calculaNq()
                        self.Tq_mean[0,self.__cont_rodadas] = self.calculaTq()
                        self.__cont_rodadas += 1
                        #resetamos tudo que precisa ser recalculado para essa nova rodada
                        self.__cont_coletas = 0
                        self.__area = 0
                        self.__tempo_total_espera = 0
                        #testa se já atingimos a quantidade de rodadas estipulada
                        if (self.__cont_rodadas == self.__n):
                            acabou = True

                self.__n_pessoas_espera -= 1
                self.__n_pessoas_servico += 1
            #se não tiver ninguém na fila de espera temos que esperar a próxima chegada
            else:
                tempo_chegada = self.simulaTempoAteEvento(self.__tx_chegada)
                if (self.__is_transiente):
                    fregues = Fregues(tempo_chegada, -1)
                else:
                    fregues = Fregues(tempo_chegada, self.__cont_rodadas)
                entrada_lista = EntradaLista(0, fregues)

                #só queremos fazer o cálculo da área quando tivermos saído da fase transiente
                if(not self.__is_transiente):
                    #devemos calcular as métricas antes de atualizar estado do sistema
                    self.__tempo_evento_ant = self.__tempo_evento_atual
                    self.__tempo_evento_atual = entrada_lista.tempo
                    self.somaArea()

                self.__n_pessoas_espera += 1
                self.__n_pessoas_sist += 1

        self.__lista.append(entrada_lista)
        return acabou


    #função que irá rodar enquanto
    def iniciaProcesso(self):
        #simula tempo até evento da primeira chegada e adiciona essa entrada na lista
        tempo_primeira_chegada = self.simulaTempoAteEvento(self.__tx_chegada)
        fregues = Fregues(tempo_primeira_chegada, -1)
        entrada_lista = EntradaLista(0, fregues)
        self.__n_pessoas_espera += 1
        self.__n_pessoas_sist += 1
        self.__lista.append(entrada_lista)

        while self.__is_transiente:
            self.controleLista()
            self.__cont_coletas_transiente += 1

        while True:
            acabou = self.controleLista()
            if acabou:
                break



    # #adiciona uma nova entrada na lista de controle
    # def addNovaEntrada(self, nova_entrada: EntradaLista):
    #     #atualizando estado do sistema
    #     self.__lista.append(nova_entrada)
    #
    #     #chegou uma nova pessoa na fila
    #     if (nova_entrada.evento == 0):
    #         #só queremos fazer o cálculo da área quando tivermos saído da fase transiente
    #         if(not self.__is_transiente):
    #             #devemos calcular as métricas antes de atualizar estado do sistema
    #             self.__tempo_evento_ant = self.__tempo_evento_atual
    #             self.__tempo_evento_atual = nova_entrada.tempo
    #             self.somaArea()
    #
    #         #atualizando estado do sistema
    #         self.__n_pessoas_espera += 1
    #         self.__n_pessoas_sist += 1
    #
    #         #preparando para gerar novo evento
    #         if (self.__n_pessoas_servico == 0):
    #             #se não tem ninguém sendo servido freguês imediatamente entra em serviço
    #             fregues = nova_entrada.fregues
    #             fregues.entraEmServico(fregues.tempo_chegada)
    #             entrada_lista = EntradaLista(1, fregues)
    #         else:
    #             #se tem alguém em serviço precisamos simular uma chegada e um término de serviço
    #             #o evento que ocorrer em menor tempo será inserido na lista
    #             tempo_chegada = self.simulaTempoAteEvento(self.__tx_chegada)
    #             tempo_termino = self.simulaTempoAteEvento(self.__tx_servico)
    #             #se chega alguém antes do freguês em serviço terminar
    #             if (tempo_chegada < tempo_termino):
    #                 #não podemos esquecer de somar o tempo até a chegada com o tempo que decorreu até o momento
    #                 #se estivermos na fase transiente ainda precisamos settar o identificador
    #                 #de rodada do freguês como -1
    #                 if (self.__is_transiente):
    #                     fregues = Fregues(tempo_chegada + nova_entrada.tempo, -1)
    #                 else:
    #                     fregues = Fregues(tempo_chegada + nova_entrada.tempo, self.__cont_rodadas)
    #                 entrada_lista = EntradaLista(0, fregues)
    #             #se o freguês em serviço termina antes de chegar alguém
    #             else:
    #                 #encontramos a entrada correspondente ao freguês que estava em serviço
    #                 #iremos disparar o evento de término de serviço desse freguês
    #                 #percorremos a lista começando pela última posição
    #                 for i in range(len(self.__lista)-1, -1, -1):
    #                     #o último evento de começo de serviço corresponde ao freguês que está em serviço
    #                     if (self.__lista[i].evento == 1):
    #                         fregues = self.__lista[i].fregues
    #                         break
    #                 fregues.terminaServico(tempo_termino + nova_entrada.tempo)
    #                 entrada_lista = EntradaLista(2, fregues)
    #
    #     #uma nova pessoa começou a ser servida
    #     if (nova_entrada.evento == 1):
    #         #queremos continuar a fazer coletas do tempo de cada cliente na fila de espera
    #         #enquanto estivermos na fase transiente
    #         if (self.__is_transiente):
    #             #se o nosso contador de coletas na fase transiente for menor do que kmin
    #             #nós continuamos coletando os tempos
    #             if (self.__cont_coletas_transiente < self.__k):
    #                 fregues = nova_entrada.fregues
    #                 self.__Tq_transiente.append(fregues.tempo_comeco_servico - fregues.tempo_chegada)
    #                 self.__cont_coletas_transiente += 1
    #             #senão, a cada coleta, nós testamos se já saímos da fase transiente
    #             else:
    #                 self.testeFaseTransiente()
    #
    #         if (not self.__is_transiente):
    #             #só queremos contabilizar a área dos fregueses dessa rodada
    #             #os que são de rodadas anteriores e ainda não terminaram estão no sistema
    #             #somente para mantê-lo em equilíbrio
    #             if (nova_entrada.fregues.rodada == self.__cont_rodadas):
    #                 self.__tempo_evento_ant = self.__tempo_evento_atual
    #                 self.__tempo_evento_atual = nova_entrada.tempo
    #                 self.somaArea()
    #                 self.__tempo_total_espera = self.__tempo_total_espera + nova_entrada.fregues.tempo_comeco_servico - nova_entrada.fregues.tempo_chegada
    #                 self.__cont_coletas = self.__cont_coletas + 1
    #
    #             #testa se já atingimos a qtd de coletas pra essa rodada
    #             if (self.__cont_coletas == self.__k):
    #                 #podemos calcular o número médio de pessoas na rodada que completamos
    #                 self.Nq_mean[0,self.__cont_rodadas] = self.calculaNq()
    #                 self.Tq_mean[0,self.__cont_rodadas] = self.calculaTq()
    #                 self.__cont_rodadas += 1
    #                 #resetamos tudo que precisa ser recalculado para essa nova rodada
    #                 self.__cont_coletas = 0
    #                 self.__area = 0
    #                 self.__tempo_total_espera = 0
    #                 #testa se já atingimos a quantidade de rodadas estipulada
    #                 if (self.__cont_rodadas == self.__n):
    #                     return
    #
    #         #atualizando estado do sistema
    #         self.__n_pessoas_espera = self.__n_pessoas_espera - 1
    #
    #         #preparando para gerar novo evento
    #         #mesmo caso para quando ocorre uma chegada na fila e já tem alguém em serviço
    #         tempo_chegada = self.simulaTempoAteEvento(self.__tx_chegada)
    #         tempo_termino = self.simulaTempoAteEvento(self.__tx_servico)
    #         if (tempo_chegada < tempo_termino):
    #             if(self.__is_transiente):
    #                 fregues = Fregues(tempo_chegada + nova_entrada.tempo, -1)
    #             else:
    #                 fregues = Fregues(tempo_chegada + nova_entrada.tempo, self.__cont_rodadas)
    #             entrada_lista = EntradaLista(0, fregues)
    #         else:
    #             for i in range(len(self.__lista)-1, -1, -1):
    #                 if (self.__lista[i].evento == 1):
    #                     fregues = self.__lista[i].fregues
    #                     break
    #             fregues.terminaServico(tempo_termino + nova_entrada.tempo)
    #             entrada_lista = EntradaLista(2, fregues)
    #
    #     #uma pessoa acabou de completar seu serviço
    #     if (nova_entrada.evento == 2):
    #         #atualizando estado do sistema
    #         self.__n_pessoas_sist -= 1
    #
    #         #preparando para gerar novo evento
    #         #caso em que tem pelo menos uma pessoa na fila de espera após termino de serviço
    #         #precisamos botar alguém imediatamente em serviço, dependendo da política
    #         if (self.__n_pessoas_espera > 0):
    #             #correponde a FCFS
    #             if (self.__tipo_fila == 0):
    #                 for i in range(len(self.__lista)):
    #                     #queremos encontrar o freguês que entrou há mais tempo na fila que ainda não foi servido
    #                     if (self.__lista[i].evento == 0 and not self.__lista[i].fregues.entrou_em_servico):
    #                         fregues = self.__lista[i].fregues
    #                         break
    #             #corresponde a LCFS
    #             else:
    #                 #percorremos a lista a partir da última entrada
    #                 for i in range(len(self.__lista)-1, -1, -1):
    #                     #queremos encontrar o último freguês que entrou na fila e ainda não foi servido
    #                     if (self.__lista[i].evento == 0 and not self.__lista[i].fregues.entrou_em_servico):
    #                         fregues = self.__lista[i].fregues
    #                         break
    #             #esse freguês entra em serviço imediatamente
    #             fregues.entraEmServico(nova_entrada.tempo)
    #             entrada_lista = EntradaLista(1, fregues)
    #         #se não tiver ninguém na fila de espera temos que esperar a próxima chegada
    #         else:
    #             tempo_chegada = self.simulaTempoAteEvento(self.__tx_chegada)
    #             if (self.__is_transiente):
    #                 fregues = Fregues(tempo_chegada, -1)
    #             else:
    #                 fregues = Fregues(tempo_chegada, self.__cont_rodadas)
    #             entrada_lista = EntradaLista(0, fregues)
    #
    #     #gerando novo evento
    #     self.addNovaEntrada(entrada_lista)

if __name__ == '__main__':
    #vetor_utilizacoes = np.array([0.2, 0.4, 0.6, 0.8, 0.9])
    #n_utilizacoes = vetor_utilizacoes.shape[0]
    #mat_kmins = np.matrix([100, 150, 200], [100, 150, 200])
    #n_kmins = mat_kmins.shape[1]
    #n_rodadas = 3200
    #n_tipos_fila = 2
    #IC = 0.95
    #precisao = 0.05
    #Nq = np.zeros([n_tipos_fila, n_kmins, n_utilizacoes])
    #Tq = np.zeros([n_tipos_fila, n_kmins, n_utilizacoes])
    #self, tx_chegada: float, tx_servico: float, k: int, n: int, tipo_fila: int, IC: float, precisao: float, utilizacao: float):
    filaFCFS = Fila(0.2, 1, 100, 3200, 0, 0.95, 0.05, 0.2)
    filaFCFS.iniciaProcesso()
    Nq = filaFCFS.Nq.mean
    print(Nq)

# -*- coding: utf-8 -*-
"""
# Trabalho de Simulação MAB-515
## Grupo:


*   **Alexandre Moreira**
*   **Daniel Atkinson**
*   **Rennan Gaio**
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import math
import random
from scipy.stats import chi2


class Evento:
    #evento == 0 indica chegada à fila
    #evento == 1 indica começo de serviço
    #evento == 2 indica término de serviço
    def __init__(self, tipo_de_evento, fregues, tempo, rodada):
        self.tipo_de_evento=tipo_de_evento
        self.tempo_evento = tempo
        self.fregues = fregues
        self.rodada = rodada

class Fregues:
    #rodada é uma variável que nos indicará em qual rodada o freguês chegou na fila
    #rodada == -1 indica que freguês entrou no sistema na fase transiente
    def __init__(self, rodada):
        #variáveis que indicam marcos no tempo
        self.tempo_chegada = 0.0
        self.tempo_comeco_servico = 0.0
        self.tempo_termino_servico = 0.0
        self.rodada_fregues = rodada

    def tempoEmEspera(self):
        return self.tempo_comeco_servico - self.tempo_chegada

    def tempoEmServico(self):
        return self.tempo_termino_servico - self.tempo_comeco_servico

    def tempoTotal(self):
        return self.tempo_termino_servico - self.tempo_chegada

class Simulador:

    def __init__(self, lamb, mi, k, n_rodadas, tipo_fila):
        #variaveis do Simulador

        #flag que indica se ainda estamos na fase transiente
        self.is_transiente = True

        self.tx_chegada = lamb
        self.tx_servico = mi

        #quantidade minima de coletas por rodada
        self.min_k = k

        #numero de rodadas que o simulador deve executar
        self.n_rodadas = n_rodadas

        #FCFS ou LCFS
        self.tipo_fila = tipo_fila

        self.tempo = 0.0

        self.servidor_ocupado = False
        #-1 pois comeca na fase transiente
        self.rodada_atual = -1

        #listas do Simulador
        #lista de eventos que vai comandar a ordem em que acontecem as chegadas e saidas
        self.lista_de_eventos = []

        #fila da MM1, que terao clientes esperando para serem atendidos
        self.fila_de_fregueses = []

        #lista para salvar dados dos clientes para a geracao de graficos
        self.todos_fregueses_atendidos = []
        self.qtd_total_pessoas_fila = []

        #listas que irao guardar metricas
        self.W_barra_por_rodada = []

        #variaveis necessarias para o calculo de nq
        self.Nq_barra_por_rodada = []
        self.fregueses_na_fila_evento_anterior = 0
        self.tempo_evento_anterior = 0.0
        self.tempo_inicio_rodada = 0.0
        #variável que irá guardar a área a cada chegada à fila e a cada entrada em serviço
        #nos eventos de interesse
        self.area_fregueses_tempo = 0

        #lista de fregueses completos por rodada, que tambem sera usado para gerar as medias por rodada
        self.fregueses_atendidos_rodada = []

    def simulaTempoExponencial(self, taxa):
        r = random.random()
        # podemos utilizar dessa forma optimizada, pois tanto 1-r, quanto r sao numeros aleatorios de 0 a 1, dessa forma,
        # economizamos 1 operacao de subtracao por numero gerado
        tempo = (-1.0 * math.log(r)) / (taxa + 0.0)
        return tempo

    #funcao auxiliar para o calculo de pessoas na fila
    def somaArea(self):
        self.area_fregueses_tempo += (self.tempo - self.tempo_evento_anterior ) * self.fregueses_na_fila_evento_anterior

    #funcao para calcular a quantidade media de pessoas na fila da mm1
    def calculaNq(self):
        tempo_da_rodada = self.tempo - self.tempo_inicio_rodada
        self.Nq_barra_por_rodada.append(self.area_fregueses_tempo/tempo_da_rodada)

    def inserirEventoEmOrdem(self, evento):
        self.lista_de_eventos.append(evento)
        #essa incersao pode ser optimizada usando busca binaria
        self.lista_de_eventos = sorted(self.lista_de_eventos, key=lambda evento: evento.tempo_evento)

    def geraEventoChegada(self, fregues):
        tempo_evento = self.tempo + self.simulaTempoExponencial(self.tx_chegada)
        return Evento("evento_chegada", fregues, tempo_evento, self.rodada_atual)

    def geraEventoSaida(self, fregues):
        tempo_evento = self.tempo + self.simulaTempoExponencial(self.tx_servico)
        return Evento("evento_saida", fregues, tempo_evento, self.rodada_atual)


    def testeFaseTransiente(self):
        #percentil da T-student para mais de 120 amostras
        percentil = 1.645
        #qtd de amostras
        n = len(self.fregueses_atendidos_rodada)
        #média amostral
        tempos_de_fila = [fregues.tempoEmEspera() for fregues in self.fregueses_atendidos_rodada]
        mean = np.sum(tempos_de_fila)/n
        #variancia amostral = SUM((Media - Media Amostral)^2) = S^2
        s = math.sqrt(np.sum( [(float(element) - float(mean))**2 for element in tempos_de_fila] ) / (n-1.0))
        #calculo do Intervalo de Confiança pela T-student
        lower = mean - (percentil*(s/math.sqrt(n)))
        upper = mean + (percentil*(s/math.sqrt(n)))
        center = lower + (upper - lower)/2
        if center/10 < (upper - lower):
            self.is_transiente=False

    def adicionaWBarraDaRodada(self):
        n = float(len(self.fregueses_atendidos_rodada))
        tempos_de_fila = [fregues.tempoEmEspera() for fregues in self.fregueses_atendidos_rodada]
        self.W_barra_por_rodada.append( np.sum(tempos_de_fila) / n )



    def iniciaProcesso(self):
        #cria o primeiro evento de chegada para dar inicio ao simulador
        self.inserirEventoEmOrdem(self.geraEventoChegada(Fregues(self.rodada_atual)))

        while self.rodada_atual < self.n_rodadas:
            #print self.lista_de_eventos
            #funcao pop(0) retira o primeiro elemento da lista, que e o proximo evento que ira acontecer em ordem cronologica
            evento_atual = self.lista_de_eventos.pop(0)

            #print evento_atual.tipo_de_evento

            #verifica quantidade de pessoas que exitiam na fila antes de tratar o proximo evento
            self.fregueses_na_fila_evento_anterior = len(self.fila_de_fregueses)

            #testa para ver o tipo de evento que esta sendo tratado
            if evento_atual.tipo_de_evento == "evento_chegada":
                #atualiza o tempo global para o tempo em que o evento esta acontecendo
                self.tempo = evento_atual.tempo_evento

                #a classe fregues recebe seu tempo de chegada de acordo com o tempo do Evento que ocasionou a criacao desse fregues
                evento_atual.fregues.tempo_chegada = self.tempo

                #adiciona o fregues a fila da MM1
                self.fila_de_fregueses.append(evento_atual.fregues)

                #cria uma nova chegada de fregues na lista de eventos
                self.inserirEventoEmOrdem(self.geraEventoChegada(Fregues(self.rodada_atual)))

            #se o evento nao e de entrada, entao ele e de saida
            elif evento_atual.tipo_de_evento == "evento_saida":
                #atualiza o tempo global para o tempo em que o evento esta acontecendo
                self.tempo = evento_atual.tempo_evento

                #a classe fregues recebe seu tempo de saida de acordo com o tempo do Evento que ocasionou a saida desse fregues
                evento_atual.fregues.tempo_termino_servico = self.tempo

                # servidor deixa de estar ocupado
                self.servidor_ocupado = False

                # adicionando a lista de todos os clientes atendidos para metricas globais
                self.todos_fregueses_atendidos.append(evento_atual.fregues)

                # adicionando a lista de clientes atendidos nesta rodada para metricas locais
                self.fregueses_atendidos_rodada.append(evento_atual.fregues)

            #depois que um dos 2 eventos ocorreu, eu irei calcular a area de fregueses que esses eventos provocaram

            #faz calculo da area de pessoas por tempo para ser utilizado para calcular Nq_barra_por_rodada
            self.somaArea()

            #atualiza o valor do tempo do evento que acabou de acontecer, o proximo evento anterior
            self.tempo_evento_anterior = self.tempo

            #coleta de dados para gerar grafico
            self.qtd_total_pessoas_fila.append(len(self.fila_de_fregueses))

            #Se apois os eventos ocorrerem, existir alguem na fila e o servidor estiver acabado de ser liberado
            #Entao o programa vai servir o proximo fregues que esta em espera, com relacao a politica de atendimento
            if len(self.fila_de_fregueses) != 0 and not self.servidor_ocupado:
                #Se FCFS, eu irei tirar da fila de fregueses o fregues que entrou a mais tempo, o fregues da esquerda
                if self.tipo_fila == "FCFS":
                    fregues = self.fila_de_fregueses.pop(0)
                #Se LCFS, eu irei tirar da fila de fregueses o fregues que entrou a menos tempo, o fregues da direita
                elif self.tipo_fila == "LCFS":
                    fregues = self.fila_de_fregueses.pop()

                #atualiza o tempo em que o fregues entrou em servico
                fregues.tempo_comeco_servico = self.tempo

                #gera o evento de saida que essa entrada em servico ira ocasionar
                self.inserirEventoEmOrdem(self.geraEventoSaida(fregues))

                #servidor passa a estar ocupado
                self.servidor_ocupado = True



            if len(self.fregueses_atendidos_rodada) >= self.min_k:
                if self.is_transiente:
                    #print "teste transiente"
                    self.testeFaseTransiente()
                    #print "fase transiente"
                    #print self.is_transiente
                    #caso chegue ao fim da fase transiente, entao comecamos a rodada 0
                    #estarei estabelecendo um fim forcado para a fase transiente caso os tempos nao consigam convergir!
                    #esse tempo será o equivalente a 10 vezes o tamanho da rodada
                    if not self.is_transiente or len(self.fregueses_atendidos_rodada) > (10*self.min_k):
                        self.rodada_atual +=1
                        self.fregueses_atendidos_rodada = []
                        self.tempo_inicio_rodada = self.tempo
                        self.area_fregueses_tempo = 0
                else:
                    #gera metricas e estatisticas
                    self.calculaNq()
                    #print "fregueses atendidos na rodada: "+str(len(self.fregueses_atendidos_rodada))
                    self.adicionaWBarraDaRodada()

                    # limpando os clientes atendidos nesta rodada
                    self.fregueses_atendidos_rodada = []
                    self.area_fregueses_tempo = 0
                    self.tempo_inicio_rodada = self.tempo

                    # proxima rodada
                    #print "rodada: " + str(self.rodada_atual)
                    self.rodada_atual += 1


def ICDaMedia(mean_list):
    #percentil da T-student para mais de 120 amostras
    percentil = 1.645

    aprovado=""

    #qtd de amostras
    n = len(mean_list)

    #média amostral
    mean = np.sum(mean_list)/n

    #variancia amostral = SUM((Media - Media Amostral)^2) = S^2
    s = math.sqrt(np.sum( [(float(element) - float(mean))**2 for element in mean_list] ) / (n-1.0))

    #calculo do Intervalo de Confiança pela T-student
    lower = mean - (percentil*(s/math.sqrt(n)))
    upper = mean + (percentil*(s/math.sqrt(n)))

    center = lower + (upper - lower)/2.0

    if center/10.0 < (upper - lower):
        #print center/10.0
        #print upper - lower
        aprovado = False
        #print "teste IC da media não obteve precisao de 5%, intervalo maior do que 10% do valor central"
    else:
        aprovado=True

    #retorna o limite inferior, limite superior, o valor central e a precisão, nessa ordem.
    return (lower, upper, center, aprovado)


def ICDaVariacia(mean_list):
    #esse método utilizará a formula do qui-quadrado para medir a variancia

    #qtd de amostras
    n = len(mean_list)

    aprovado=""

    #média amostral
    mean = np.sum(mean_list)/n

    #dados obtidos na tabela da qui-quadrada para alpha=0.5, alpha/2 = 0.25
    #Qalpha2 = 74.222
    #Q1menosalpha2 = 129.561

    #como na tabela de qui-quadrado só temos ate 100 graus de liberdade, tivemos que usar uma funcao
    #auxiliar para calcular o valor dela para n = 3200

    Qalpha2 = chi2.isf(q=0.025, df=n-1)
    Q1menosalpha2 = chi2.isf(q=0.975, df=n-1)

    #variancia amostral = SUM((Media - Media Amostral)^2) = S^2
    s_quadrado=np.sum( [(float(element) - float(mean))**2 for element in mean_list] ) / (n-1.0)

    #calculo do Intervalo de Confiança pela qui-quadrado
    lower = (n-1)*s_quadrado/Q1menosalpha2
    upper = (n-1)*s_quadrado/Qalpha2

    center = lower + (upper - lower)/2.0

    if center/10.0 < (upper - lower):
        #print center/10.0
        #print upper - lower
        aprovado=False
        #print "teste IC da variancia não obteve precisao de 5%, intervalo maior do que 10% do valor central"
    else:
        aprovado=True

    #retorna o limite inferior, limite superior, o valor central e a precisão, nessa ordem.
    return (lower, upper, center, aprovado)



#a matriz de entrada desta funcao deve ter em cada linha tuplas com a (quantidade de pessoas) ou (tempo medio no sistema) pelo periodo de cada evento
#e cada linha deve ser representativa da execucao de todo o sistema do ro respectivamente 0.2, 0.4, 0.6, 0.8 e 0.9
def printa_grafico_numero_medio_por_tempo(matriz_de_metricas_por_ro):

    for ro_metrics in matriz_de_metricas_por_ro:
        plt.plot(*zip(*ro_metrics))

    plt.legend(['ro = 0.2', 'ro = 0.4', 'ro = 0.6', 'ro = 0.8', 'ro = 0.9'], loc='upper left')

    plt.show()




if __name__ == '__main__':
    vetor_lamb = [0.2, 0.4, 0.6, 0.8, 0.9]
    #vetor_lamb = [0.9]
    mi = 1
    #kmins = [100, 300, 500, 700, 1000]
    kmins = [150]
    n_rodadas = 3200
    n_tipos_fila = ["FCFS", "LCFS"]
    # IC = 0.95
    # precisao = 0.05

    for tipo_fila in n_tipos_fila:
        for lamb in vetor_lamb:
            for k in kmins:
            #for lamb in vetor_lamb:
                #self, tx_chegada: float, tx_servico: float, k: int, n: int, tipo_fila: int, IC: float, precisao: float, utilizacao: float):
                simulador = Simulador(lamb, mi, k, n_rodadas, tipo_fila)
                simulador.iniciaProcesso()

                #testando qualquer variavel para ver a corretude do simulador
                nqbarra = simulador.Nq_barra_por_rodada
                wbarra = simulador.W_barra_por_rodada

                tempos = [t.tempoEmEspera() for t in simulador.todos_fregueses_atendidos]
                pessoas_na_fila = simulador.qtd_total_pessoas_fila

                lowerMW, upperMW, centerMW , aprovadoMW= ICDaMedia(wbarra)
                lowerMNq, upperMNq, centerMNq , aprovadoMNq= ICDaMedia(nqbarra)
                lowerVW, upperVW, centerVW , aprovadoVW= ICDaVariacia(wbarra)
                lowerVNq, upperVNq, centerVNq , aprovadoVNq= ICDaVariacia(nqbarra)

                if aprovadoMW and aprovadoVW and aprovadoMNq and aprovadoVNq:

                    print "RESULTADOS DA SIMULACAO COM LAMB = " + str(lamb) + ", K = " + str(k) + ", TIPO DE FILA = " + tipo_fila
                    #print "media amostral = "+ str(np.mean(wbarra))
                    print "\n"
                    #item a
                    print "Tempo médio de espera em fila = "+str(centerMW)
                    print "intervalo de confiança da espera em fila = " + str(lowerMW) + " ate " + str(upperMW)
                    print "tamanho do intervalo de confianca do tempo medio = " + str(upperMW-lowerMW)
                    print "\n"

                    #item b
                    print "Variancia média de espera em fila = "+str(centerVW)
                    print "intervalo de confiança da variancia do tempo em fila = " + str(lowerVW) + " ate " + str(upperVW)
                    print "\n"

                    #item c
                    print "Nq médio da fila = "+str(centerMNq)
                    print "intervalo de confiança de Nq= " + str(lowerMNq) + " ate " + str(upperMNq)
                    print "tamanho do intervalo de confianca do tempo medio = " + str(upperMW-lowerMW)
                    print "\n"

                    #item d
                    print "Variancia média de Nq = "+str(centerVW)
                    print "intervalo de confiança da variancia de Nq = " + str(lowerVW) + " ate " + str(upperVW)
                    print "\n"

                    #fim da simulacao
                    print "fim da simulacao com lamb = " + str(lamb) + ", k = " + str(k) + ", tipo de fila = " + tipo_fila
                    print "#######################################################################"



                    #area de teste para prints de graficos para o Trabalho
                    #essa parte do codigo ficara comentada para nao gerar centenas de graficos especificos em todas as execucoes


                    #plt.plot(tempos[0:k])
                    #plt.show()

                    #plt.plot(pessoas_na_fila)
                    #plt.show()


                else:
                    #significa que a quantidade minima de eventos por rodada nao foi o suficiente para gerar os resultados esperados
                    #entao incrementamos a quantidade de rodadas minimas para a proxima bateria de testes, e como essa já nao é mais valida,
                    #os resultados com esse k nao sao mais interessantes
                    print "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
                    print "CONFIANÇA EXIGIDA NÃO FOI ATENDIDA, PULANDO PARA A PROXIMA ITERACAO COM K INCREMENTADO DE 100"
                    kmins.append(k+100)
                    print "NOVO VALOR DE K = " + str(k+100)
                    print "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"





        #         break
        #     break
        # break

import numpy as np

# fontes:
# http://www.portalaction.com.br/inferencia/intervalo-de-confianca
# http://www.portalaction.com.br/content/63-distribui%C3%A7%C3%A3o-qui-quadrado


#######Comentarios pertinentes

'''
GALERA LEIAM ISSO PFF

deveremos rodar todos os testes dentro de 3 for:

1- o for que vai para a disciplina utilizada
2- o for que vai para a utilizaçao do servidor ro=[0.2, 0.4, 0.6, 0.8, 0.9]
3- o for que vai variar a quantidade de kmin de coletas por rodada, para garantir os 5% de precisao


a) o W podera ser calculado utilizando o metodo IC da media, assim como o T
sendo que em um deles a entrada deve ser a media do tempo em fila de cada exeuçao e o outro o tempo total

b) a variancia de W pode ser medida utilizando a funcao IC da variancia, dando como entrada os tempos medios de fila das rodadas

c) calcula_nq gera seu Nq medio por rodada, depois para calcular o IC dele, basta passar essa lista para a funcao IC_da_media

d) O mesmo, mas para a lista de Nq, medindo a variancia de Nq com a funcao IC_da_variacia

depois de encontrados esses valores esperimentalmente, deveremos compara-los com a teoria, usando little => W*lamb=Nq


foi se criada ja uma funcao esqueleto/modelo com a ideia de fim de fase transiente
ela primeiramente roda um numero minimo de vezes e depois testa a precisao dos tempos de execucao
caso esses tempos se estabilizem ela finaliza a fase transiente e entra para as rodadas normais

essa funcao devera ser completamente modelada para nosso codigo principal, usando as variaveis corretas, etc.
'''

def IC_da_media(mean_list):
    #percentil da T-student para mais de 120 amostras
    percentil = 1.645

    #qtd de amostras
    n = len(mean_list)

    #média amostral
    mean = np.sum(mean_list)/n

    #variancia amostral = SUM((Media - Media Amostral)^2) = S^2
    s = math.sqrt(np.sum( [(float(element) - float(mean))**2 for element in mean_list] ) / (n-1.0))

    #calculo do Intervalo de Confiança pela T-student
    lower = mean - (percentil*(s/math.sqrt(n)))
    upper = mean + (percentil*(s/math.sqrt(n)))

    center = lower + (upper - lower)/2

    if center/10 > (upper - lower):
        print "teste não obteve precisao de 5%, intervalo maior do que 10% do valor central"

    #retorna o limite inferior, limite superior, o valor central e a precisão, nessa ordem.
    return (lower, upper, center, upper/lower)


def IC_da_variacia(mean_list):
    #esse método utilizará a formula do qui-quadrado para medir a variancia

    #dados obtidos na tabela da qui-quadrada para alpha=0.5, alpha/2 = 0.25
    Qalpha2 = 74.222
    Q1menosalpha2 = 129.561

    #qtd de amostras
    n = len(mean_list)

    #variancia amostral = SUM((Media - Media Amostral)^2) = S^2
    s_quadrado=np.sum( [(float(element) - float(mean))**2 for element in mean_list] ) / (n-1.0)

    #calculo do Intervalo de Confiança pela qui-quadrado
    lower = (n-1)*s_quadrado/Q1menosalpha2
    upper = (n-1)*s_quadrado/Qalpha2

    center = lower + (upper - lower)/2

    if center/10 > (upper - lower):
        print "teste não obteve precisao de 5%, intervalo maior do que 10% do valor central"

    #retorna o limite inferior, limite superior, o valor central e a precisão, nessa ordem.
    return (lower, upper, center, upper/lower)

#funcao auxiliar para o calculo de pessoas na fila
def soma_area(area_anterior, tempo_inicial, tempo_do_proximo_evento, nq):
    area_acumulada = area_anterior+(tempo_do_proximo_evento-tempo_inicial)*nq
    return area_acumulada

#funcao para calcular a quantidade media de pessoas na fila da mm1
def calcula_nq(area, tempo_inicial, tempo_final):
    tempo = tempo_final-tempo_inicial
    return area_final/tempo

#funcao esqueleto para definir o fim de uma fase transiente, e comecar as rodadas normais
def Fase_transiente():
    cont = 0
    rodadas_minimas = 100
    precisao_insuficiente = True
    tempo_de_cada_evento= []

    while cont < rodadas_minimas or precisao_insuficiente:
        #faz mais uma rodada
        precisao=IC_da_media(tempo_de_cada_evento)[3]
        if precisao < 0.05:
            precisao_insuficiente = False

    return

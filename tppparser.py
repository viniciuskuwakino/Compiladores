import sys
import os

from sys import argv, exit

from symbols_table import SymbolsTable
from symbols_func_table import SymbolsFuncTable
import logging

logging.basicConfig(
    level=logging.DEBUG,
    filename="parser.log",
    filemode="w",
    format="%(filename)10s:%(lineno)4d:%(message)s"
)
log = logging.getLogger()

import ply.yacc as yacc

# Get the token map from the lexer.  This is required.
from tpplex import tokens

from mytree import MyNode
from anytree.exporter import DotExporter, UniqueDotExporter
from anytree import RenderTree, AsciiStyle, PreOrderIter

from myerror import MyError

error_handler = MyError('ParserErrors')

root = None

symbol_table = SymbolsTable()
symbol_func_table = SymbolsFuncTable()


# def get_function(no):
    # pass
    # print(no.name)
    # aux = no.parent
    # print(aux)
    # while aux.name != 'programa':
    #     if aux.name == 'declaracao_funcao':
    #         print(aux.children[1].children[0].name)
    #         break
    #     aux = aux.parent

def get_params(no):
    params = list()
    for i in PreOrderIter(no):
        if i.name == 'parametro':
            params.append(i)

    params_list = list()
    for i in params:
        tipo = return_leaf(i.children[0]).name
        nome = return_leaf(i.children[2]).name
        params_list.append([tipo, nome])

    return params_list


def return_leaf(no):
    
    for node in no.descendants:
        if node.is_leaf:
            return node
        
    # node = [node for node in no.descendants if node.is_leaf]
    # # print(len(node))
    # for i in node:
    #     print(i.name)
    # [print(i.name) for i in node]

    # return node
    

def find_return(no):
    while len(no.children) == 2:
        if no.children[1].children[0].name == 'retorna':
            return return_leaf(no.children[1].children[0].children[-2]).name

        no = no.children[0]
    
    return ''


def add_symbol(no):
    tipo = return_leaf(no[1]).name
    dois_pontos = return_leaf(no[2]).name
    
    # ====================================================
    # erro de variavel ja declarada, no parser ou sema?
    # ====================================================

    if len(no[3].children[0].children) != 1:
        var = no[3].children[0].children
        
        var_name = return_leaf(var[0]).name
        
        check_var_exist = symbol_table.var_name_exists(var_name)
        
        if len(var[1].children) == 3:
            indice = return_leaf(var[1].children[1]).name
            if check_var_exist == '':
                symbol_table.add("VAR", var_name, tipo, 1, indice, 0, '', 'N', 'N', no.lineno(2))
            else:
                symbol_table.errors.append(['WAR-SEM-VAR-DECL-PREV', var_name, check_var_exist])
            
            
        elif len(var[1].children) == 4:
            indice_1 = return_leaf(var[1].children[0].children[1]).name
            indice_2 = return_leaf(var[1].children[2]).name
            if check_var_exist == '':
                symbol_table.add("VAR", var_name, tipo, 2, indice_1, indice_2, '', 'N', 'N', no.lineno(2))
            else:
                symbol_table.errors.append(['WAR-SEM-VAR-DECL-PREV', var_name, check_var_exist])

    else:
        var_name = return_leaf(no[3]).name
        check_var_exist = symbol_table.var_name_exists(var_name)
        
        if check_var_exist == '':
            symbol_table.add("VAR", var_name, tipo, 0, 1, 0, '', 'N', 'N', no.lineno(2))
        else:
            symbol_table.errors.append(['WAR-SEM-VAR-DECL-PREV', var_name, check_var_exist])
            

def add_func(no):
    if len(no[0].children) == 2:
        tipo = return_leaf(no[0].children[0]).name
        nome_func = return_leaf(no[0].children[1].children[0]).name

        lista_params = no[0].children[1].children[2]
        params = get_params(lista_params)

        corpo = no[0].children[1].children[-2]
        var_retorno = find_return(corpo)

        if nome_func == 'principal':
            symbol_func_table.add(tipo, nome_func, len(params), params, var_retorno, 'S')
        else:
            symbol_func_table.add(tipo, nome_func, len(params), params, var_retorno, 'N')
        # symbol_func_table.add(tipo, nome_func, len(params), params, no.lineno(2))

    else:
        tipo = 'vazio'
        nome_func = return_leaf(no[0].children[0].children[0]).name

        lista_params = no[0].children[0].children[2]
        params = get_params(lista_params)

        corpo = no[0].children[0].children[-2]
        var_retorno = find_return(corpo)

        if nome_func == 'principal':
            symbol_func_table.add(tipo, nome_func, len(params), params, var_retorno, 'S')
        else:
            symbol_func_table.add(tipo, nome_func, len(params), params, var_retorno, 'N')



    # if len(no[0])
    # for i in no:
    #     print(i.name)
        

# Sub-árvore.
#       (programa)
#           |
#   (lista_declaracoes)
#     /     |      \
#   ...    ...     ...

def p_programa(p):
    """programa : lista_declaracoes"""

    global root

    programa = MyNode(name='programa', type='PROGRAMA')

    root = programa
    p[0] = programa
    p[1].parent = programa


#    (lista_declaracoes)                          (lista_declaracoes)
#          /           \                                    |
# (lista_declaracoes)  (declaracao)                    (declaracao)


def p_lista_declaracoes(p):
    """lista_declaracoes : lista_declaracoes declaracao
                        | declaracao
    """
    pai = MyNode(name='lista_declaracoes', type='LISTA_DECLARACOES')
    p[0] = pai
    p[1].parent = pai

    if len(p) > 2:
        p[2].parent = pai


# Sub-árvore.
#      (declaracao)
#           |
#  (declaracao_variaveis ou
#   inicializacao_variaveis ou
#   declaracao_funcao)


def p_declaracao(p):
    """declaracao : declaracao_variaveis
                | inicializacao_variaveis
                | declaracao_funcao
    """
    pai = MyNode(name='declaracao', type='DECLARACAO')
    p[0] = pai
    p[1].parent = pai


# Sub-árvore.
#      (declaracao_variaveis)
#      / p[1]    |           \
# (tipo)    (DOIS_PONTOS)    (lista_variaveis)
#                |
#               (:)


def p_declaracao_variaveis(p):
    """declaracao_variaveis : tipo DOIS_PONTOS lista_variaveis"""

    # print("DECLARACAO DE VARIAVEIS")

    pai = MyNode(name='declaracao_variaveis', type='DECLARACAO_VARIAVEIS')
    p[0] = pai

    p[1].parent = pai

    filho = MyNode(name='DOIS_PONTOS', type='DOIS_PONTOS', parent=pai)
    filho_sym = MyNode(name=p[2], type='SIMBOLO', parent=filho)
    p[2] = filho

    p[3].parent = pai
    # print(p.lineno(2))

    add_symbol(p)


def p_declaracao_variaveis_error(p):
    """ declaracao_variaveis : error DOIS_PONTOS lista_variaveis
                            | tipo error lista_variaveis 
                            | tipo DOIS_PONTOS error
    """

    print(error_handler.newError('ERR-SYN-DECLARACAO-VARIAVEIS'))

    error_line = p.lineno(2)
    father = MyNode(name='ERR-SYN-DECLARACAO-VARIAVEIS:{}'.format(error_line), type='ERROR')
    logging.error(
        "Syntax error parsing index rule at line {}".format(error_line))
    parser.errok()
    p[0] = father


# Sub-árvore.
#   (inicializacao_variaveis)
#              |
#         (atribuicao)


def p_inicializacao_variaveis(p):
    """inicializacao_variaveis : atribuicao"""

    pai = MyNode(name='inicializacao_variaveis',
                 type='INICIALIZACAO_VARIAVEIS')
    p[0] = pai
    p[1].parent = pai


def p_lista_variaveis(p):
    """lista_variaveis : lista_variaveis VIRGULA var
                        | var
    """
    pai = MyNode(name='lista_variaveis', type='LISTA_VARIAVEIS')
    p[0] = pai
    if len(p) > 2:
        p[1].parent = pai
        filho = MyNode(name='virgula', type='VIRGULA', parent=pai)
        filho_sym = MyNode(name=',', type='SIMBOLO', parent=filho)
        p[3].parent = pai
    else:
        p[1].parent = pai


def p_var(p):
    """var : ID
            | ID indice
    """

    pai = MyNode(name='var', type='VAR')
    p[0] = pai
    filho = MyNode(name='ID', type='ID', parent=pai)
    filho_id = MyNode(name=p[1], type='ID', parent=filho)
    p[1] = filho
    if len(p) > 2:
        p[2].parent = pai


def p_indice(p):
    """indice : indice ABRE_COLCHETE expressao FECHA_COLCHETE
                | ABRE_COLCHETE expressao FECHA_COLCHETE
    """
    pai = MyNode(name='indice', type='INDICE')
    p[0] = pai
    if len(p) == 5:
        p[1].parent = pai  # indice

        filho2 = MyNode(name='abre_colchete', type='ABRE_COLCHETE', parent=pai)
        filho_sym2 = MyNode(name=p[2], type='SIMBOLO', parent=filho2)
        p[2] = filho2

        p[3].parent = pai  # expressao

        filho4 = MyNode(name='fecha_colchete', type='FECHA_COLCHETE', parent=pai)
        filho_sym4 = MyNode(name=p[4], type='SIMBOLO', parent=filho4)
        p[4] = filho4
    else:
        filho1 = MyNode(name='abre_colchete', type='ABRE_COLCHETE', parent=pai)
        filho_sym1 = MyNode(name=p[1], type='SIMBOLO', parent=filho1)
        p[1] = filho1

        p[2].parent = pai  # expressao

        filho3 = MyNode(name='fecha_colchete', type='FECHA_COLCHETE', parent=pai)
        filho_sym3 = MyNode(name=p[3], type='SIMBOLO', parent=filho3)
        p[3] = filho3


def p_indice_error(p):
    """indice : ABRE_COLCHETE error FECHA_COLCHETE
                | indice ABRE_COLCHETE error
                | indice ABRE_COLCHETE error FECHA_COLCHETE
    """

    print(error_handler.newError('ERR-SYN-INDICE'))

    error_line = p.lineno(2)
    father = MyNode(name='ERR-SYN-INDICE:{}'.format(error_line), type='ERROR')
    logging.error(
        "Syntax error parsing index rule at line {}".format(error_line))
    parser.errok()
    p[0] = father

    # if len(p) == 4:
    #     p[1] = new_node('ABRECOLCHETES', father)
    #     p[2].parent = father
    #     p[3] = new_node('FECHACOLCHETES', father)
    # else:
    #     p[1].parent = father
    #     p[2] = new_node('ABRECOLCHETES', father)
    #     p[3].parent = father
    #     p[4] = new_node('FECHACOLCHETES', father)


# Sub-árvore:
#    (tipo)
#      |
#  (FLUTUANTE)
def p_tipo(p):
    """tipo : INTEIRO
        | FLUTUANTE
    """

    pai = MyNode(name='tipo', type='TIPO')
    p[0] = pai
    # p[1] = MyNode(name=p[1], type=p[1].upper(), parent=pai)

    if p[1] == "inteiro":
        filho1 = MyNode(name='INTEIRO', type='INTEIRO', parent=pai)
        filho_sym = MyNode(name=p[1], type=p[1].upper(), parent=filho1)
        p[1] = filho1
    else:
        filho1 = MyNode(name='FLUTUANTE', type='FLUTUANTE', parent=pai)
        filho_sym = MyNode(name=p[1], type=p[1].upper(), parent=filho1)


def p_declaracao_funcao(p):
    """declaracao_funcao : tipo cabecalho 
                        | cabecalho 
    """
    # print(type(p[0]))
    # print("DECLARACAO DE FUNCAO")

    pai = MyNode(name='declaracao_funcao', type='DECLARACAO_FUNCAO')
    p[0] = pai
    p[1].parent = pai

    if len(p) == 3:
        p[2].parent = pai

    add_func(p)

    # return_leaf(p[0])
    # leaf_nodes = return_leaf(p[0])
    # [print(i.name) for i in leaf_nodes]
    # print("TERMINOU ===================== \n")

    # print(leaf_nodes)
    # if len(leaf_nodes) == 3:
    #             #     symbol_table.add('id', leaf_nodes[2].name, leaf_nodes[0].name, 0, 1, 0, 'global', False, 1)
    #             # if len(leaf_nodes) == 6:
    #             #     symbol_table.add('id', leaf_nodes[2].name, leaf_nodes[0].name, 1, leaf_nodes[4].name, 0, 'global', False, 1)
    #             # if len(leaf_nodes) == 9:
    #             #     symbol_table.add('id', leaf_nodes[2].name, leaf_nodes[0].name, 2, leaf_nodes[4].name, leaf_nodes[7].name, 'global', False, 1)
    #         if node.name == 'declaracao_funcao':
    #             # print('dec_function')
    #             leaf_nodes = return_leaf(node)
    #             for i in leaf_nodes:
    #                 print(i.name)


def p_declaracao_funcao_error(p):
    """declaracao_funcao : error cabecalho 
                        | tipo error
                        | error
    """

    print(error_handler.newError('ERR-SYN-DECLARACAO-FUNCAO'))

    error_line = p.lineno(2)
    father = MyNode(name='ERR-SYN-DECLARACAO-FUNCAO:{}'.format(error_line), type='ERROR')
    logging.error(
        "Syntax error parsing index rule at line {}".format(error_line))
    parser.errok()
    p[0] = father


def p_cabecalho(p):
    """cabecalho : ID ABRE_PARENTESE lista_parametros FECHA_PARENTESE corpo FIM"""

    pai = MyNode(name='cabecalho', type='CABECALHO')
    p[0] = pai

    filho1 = MyNode(name='ID', type='ID', parent=pai)
    filho_id = MyNode(name=p[1], type='ID', parent=filho1)
    p[1] = filho1

    filho2 = MyNode(name='ABRE_PARENTESE', type='ABRE_PARENTESE', parent=pai)
    filho_sym2 = MyNode(name='(', type='SIMBOLO', parent=filho2)
    p[2] = filho2

    p[3].parent = pai  # lista_parametros

    filho4 = MyNode(name='FECHA_PARENTESE', type='FECHA_PARENTESE', parent=pai)
    filho_sym4 = MyNode(name=')', type='SIMBOLO', parent=filho4)
    p[4] = filho4

    p[5].parent = pai  # corpo

    filho6 = MyNode(name='FIM', type='FIM', parent=pai)
    filho_id = MyNode(name='fim', type='FIM', parent=filho6)
    p[6] = filho6


def p_cabecalho_error(p):
    """cabecalho : ID ABRE_PARENTESE error FECHA_PARENTESE corpo FIM
                | ID ABRE_PARENTESE lista_parametros FECHA_PARENTESE error FIM
                | error ABRE_PARENTESE lista_parametros FECHA_PARENTESE corpo FIM
                | ID ABRE_PARENTESE lista_parametros FECHA_PARENTESE corpo 
    """

    print(error_handler.newError('ERR-SYN-CABECALHO'))
    
    error_line = p.lineno(2)
    father = MyNode(name='ERR-SYN-CABECALHO:{}'.format(error_line), type='ERROR')
    logging.error(
        "Syntax error parsing index rule at line {}".format(error_line))
    parser.errok()
    p[0] = father


def p_lista_parametros(p):
    """lista_parametros : lista_parametros VIRGULA parametro
                    | parametro
                    | vazio
    """

    pai = MyNode(name='lista_parametros', type='LISTA_PARAMETROS')
    p[0] = pai
    p[1].parent = pai

    if len(p) > 2:
        filho2 = MyNode(name='virgula', type='VIRGULA', parent=pai)
        filho_sym2 = MyNode(name=',', type='SIMBOLO', parent=filho2)
        p[2] = filho2
        p[3].parent = pai


def p_parametro(p):
    """parametro : tipo DOIS_PONTOS ID
                | parametro ABRE_COLCHETE FECHA_COLCHETE
    """

    pai = MyNode(name='parametro', type='PARAMETRO')
    p[0] = pai
    p[1].parent = pai

    if p[2] == ':':
        filho2 = MyNode(name='DOIS_PONTOS', type='DOIS_PONTOS', parent=pai)
        filho_sym2 = MyNode(name=':', type='SIMBOLO', parent=filho2)
        p[2] = filho2

        filho3 = MyNode(name='id', type='ID', parent=pai)
        filho_id = MyNode(name=p[3], type='ID', parent=filho3)
    else:
        filho2 = MyNode(name='abre_colchete', type='ABRE_COLCHETE', parent=pai)
        filho_sym2 = MyNode(name='[', type='SIMBOLO', parent=filho2)
        p[2] = filho2

        filho3 = MyNode(name='fecha_colchete', type='FECHA_COLCHETE', parent=pai)
        filho_sym3 = MyNode(name=']', type='SIMBOLO', parent=filho3)
        p[3] = filho3


def p_parametro_error(p):
    """parametro : tipo error ID
                | error ID
                | parametro error FECHA_COLCHETE
                | parametro ABRE_COLCHETE error
    """

    print(error_handler.newError('ERR-SYN-PARAMETRO'))
    error_line = p.lineno(2)
    father = MyNode(name='ERR-SYN-PARAMETRO:{}'.format(error_line), type='ERROR')
    logging.error(
        "Syntax error parsing index rule at line {}".format(error_line))
    parser.errok()
    p[0] = father


def p_corpo(p):
    """corpo : corpo acao
            | vazio
    """

    pai = MyNode(name='corpo', type='CORPO')
    p[0] = pai
    p[1].parent = pai

    if len(p) > 2:
        p[2].parent = pai


def p_acao(p):
    """acao : expressao
        | declaracao_variaveis
        | se
        | repita
        | leia
        | escreva
        | retorna
    """
    pai = MyNode(name='acao', type='ACAO')
    p[0] = pai
    p[1].parent = pai


# Sub-árvore:
#       ________ (se) ________________________________
#      /    /          \      \         \      \      \
# (SE) (expressao)  (ENTAO)  (corpo) (SENAO) (corpo) (FIM)
#  |       |           |
# (se)   (...)      (então) ....


def p_se(p):
    """se : SE expressao ENTAO corpo FIM
          | SE expressao ENTAO corpo SENAO corpo FIM
    """

    pai = MyNode(name='se', type='SE')
    p[0] = pai

    filho1 = MyNode(name='SE', type='SE', parent=pai)
    filho_se = MyNode(name=p[1], type='SE', parent=filho1)
    p[1] = filho1

    p[2].parent = pai

    filho3 = MyNode(name='ENTAO', type='ENTAO', parent=pai)
    filho_entao = MyNode(name=p[3], type='ENTAO', parent=filho3)
    p[3] = filho3

    p[4].parent = pai

    if len(p) == 8:
        filho5 = MyNode(name='SENAO', type='SENAO', parent=pai)
        filho_senao = MyNode(name=p[5], type='SENAO', parent=filho5)
        p[5] = filho5

        p[6].parent = pai

        filho7 = MyNode(name='FIM', type='FIM', parent=pai)
        filho_fim = MyNode(name=p[7], type='FIM', parent=filho7)
        p[7] = filho7
    else:
        filho5 = MyNode(name='fim', type='FIM', parent=pai)
        filho_fim = MyNode(name=p[5], type='FIM', parent=filho5)
        p[5] = filho5


def p_se_error(p):
    """se : error expressao ENTAO corpo FIM
        | SE expressao error corpo FIM
        | error expressao ENTAO corpo SENAO corpo FIM
        | SE expressao error corpo SENAO corpo FIM
        | SE expressao ENTAO corpo error corpo FIM
        | SE expressao ENTAO corpo SENAO corpo 
    """

    print(error_handler.newError('ERR-SYN-CONDICIONAL'))

    error_line = p.lineno(2)
    father = MyNode(name='ERR-SYN-CONDICIONAL:{}'.format(error_line), type='ERROR')
    logging.error(
        "Syntax error parsing index rule at line {}".format(error_line))
    parser.errok()
    p[0] = father


def p_repita(p):
    """repita : REPITA corpo ATE expressao"""

    pai = MyNode(name='repita', type='REPITA')
    p[0] = pai

    filho1 = MyNode(name='REPITA', type='REPITA', parent=pai)
    filho_repita = MyNode(name=p[1], type='REPITA', parent=filho1)
    p[1] = filho1

    p[2].parent = pai  # corpo.

    filho3 = MyNode(name='ATE', type='ATE', parent=pai)
    filho_ate = MyNode(name=p[3], type='ATE', parent=filho3)
    p[3] = filho3

    p[4].parent = pai  # expressao.


def p_repita_error(p):
    """repita : error corpo ATE expressao
            | REPITA corpo error expressao
    """

    print(error_handler.newError('ERR-SYN-REPITA'))

    error_line = p.lineno(2)
    father = MyNode(name='ERR-SYN-REPITA:{}'.format(error_line), type='ERROR')
    logging.error(
        "Syntax error parsing index rule at line {}".format(error_line))
    parser.errok()
    p[0] = father


def p_atribuicao(p):
    """atribuicao : var ATRIBUICAO expressao"""

    pai = MyNode(name='atribuicao', type='ATRIBUICAO')
    p[0] = pai

    p[1].parent = pai

    filho2 = MyNode(name='ATRIBUICAO', type='ATRIBUICAO', parent=pai)
    filho_sym2 = MyNode(name=':=', type='SIMBOLO', parent=filho2)
    p[2] = filho2

    p[3].parent = pai


def p_leia(p):
    """leia : LEIA ABRE_PARENTESE var FECHA_PARENTESE"""

    pai = MyNode(name='leia', type='LEIA')
    p[0] = pai

    filho1 = MyNode(name='LEIA', type='LEIA', parent=pai)
    filho_sym1 = MyNode(name=p[1], type='LEIA', parent=filho1)
    p[1] = filho1

    filho2 = MyNode(name='ABRE_PARENTESE', type='ABRE_PARENTESE', parent=pai)
    filho_sym2 = MyNode(name='(', type='SIMBOLO', parent=filho2)
    p[2] = filho2

    p[3].parent = pai  # var

    filho4 = MyNode(name='FECHA_PARENTESE', type='FECHA_PARENTESE', parent=pai)
    filho_sym4 = MyNode(name=')', type='SIMBOLO', parent=filho4)
    p[4] = filho4


def p_leia_error(p):
    """leia : LEIA ABRE_PARENTESE error FECHA_PARENTESE
    """

    print(error_handler.newError('ERR-SYN-LEIA'))

    error_line = p.lineno(2)
    father = MyNode(name='ERR-SYN-LEIA:{}'.format(error_line), type='ERROR')
    logging.error(
        "Syntax error parsing index rule at line {}".format(error_line))
    parser.errok()
    p[0] = father


def p_escreva(p):
    """escreva : ESCREVA ABRE_PARENTESE expressao FECHA_PARENTESE"""

    pai = MyNode(name='escreva', type='ESCREVA')
    p[0] = pai

    filho1 = MyNode(name='ESCREVA', type='ESCREVA', parent=pai)
    filho_sym1 = MyNode(name=p[1], type='ESCREVA', parent=filho1)
    p[1] = filho1

    filho2 = MyNode(name='ABRE_PARENTESE', type='ABRE_PARENTESE', parent=pai)
    filho_sym2 = MyNode(name='(', type='SIMBOLO', parent=filho2)
    p[2] = filho2

    p[3].parent = pai  # expressao.

    filho4 = MyNode(name='FECHA_PARENTESE', type='FECHA_PARENTESE', parent=pai)
    filho_sym4 = MyNode(name=')', type='SIMBOLO', parent=filho4)
    p[4] = filho4


def p_retorna(p):
    """retorna : RETORNA ABRE_PARENTESE expressao FECHA_PARENTESE"""

    pai = MyNode(name='retorna', type='RETORNA')
    p[0] = pai

    filho1 = MyNode(name='RETORNA', type='RETORNA', parent=pai)
    filho_sym1 = MyNode(name=p[1], type='RETORNA', parent=filho1)
    p[1] = filho1

    filho2 = MyNode(name='ABRE_PARENTESE', type='ABRE_PARENTESE', parent=pai)
    filho_sym2 = MyNode(name='(', type='SIMBOLO', parent=filho2)
    p[2] = filho2

    p[3].parent = pai  # expressao.

    filho4 = MyNode(name='FECHA_PARENTESE', type='FECHA_PARENTESE', parent=pai)
    filho_sym4 = MyNode(name=')', type='SIMBOLO', parent=filho4)
    p[4] = filho4


def p_expressao(p):
    """expressao : expressao_logica
                    | atribuicao
    """
    pai = MyNode(name='expressao', type='EXPRESSAO')
    p[0] = pai
    p[1].parent = pai


def p_expressao_logica(p):
    """expressao_logica : expressao_simples
                    | expressao_logica operador_logico expressao_simples
    """
    pai = MyNode(name='expressao_logica', type='EXPRESSAO_LOGICA')
    p[0] = pai
    p[1].parent = pai

    if len(p) > 2:
        p[2].parent = pai
        p[3].parent = pai


def p_expressao_simples(p):
    """expressao_simples : expressao_aditiva
                        | expressao_simples operador_relacional expressao_aditiva
    """

    pai = MyNode(name='expressao_simples', type='EXPRESSAO_SIMPLES')
    p[0] = pai
    p[1].parent = pai

    if len(p) > 2:
        p[2].parent = pai
        p[3].parent = pai


def p_expressao_aditiva(p):
    """expressao_aditiva : expressao_multiplicativa
                        | expressao_aditiva operador_soma expressao_multiplicativa
    """

    pai = MyNode(name='expressao_aditiva', type='EXPRESSAO_ADITIVA')
    p[0] = pai
    p[1].parent = pai

    if len(p) > 2:
        p[2].parent = pai
        p[3].parent = pai


def p_expressao_multiplicativa(p):
    """expressao_multiplicativa : expressao_unaria
                               | expressao_multiplicativa operador_multiplicacao expressao_unaria
        """

    pai = MyNode(name='expressao_multiplicativa', type='EXPRESSAO_MULTIPLICATIVA')
    p[0] = pai
    p[1].parent = pai

    if len(p) > 2:
        p[2].parent = pai
        p[3].parent = pai


def p_expressao_unaria(p):
    """expressao_unaria : fator
                        | operador_soma fator
                        | operador_negacao fator
        """
    pai = MyNode(name='expressao_unaria', type='EXPRESSAO_UNARIA')
    p[0] = pai
    p[1].parent = pai

    if p[1] == '!':
        filho1 = MyNode(name='operador_negacao',
                        type='OPERADOR_NEGACAO', parent=pai)
        filho_sym1 = MyNode(name=p[1], type='SIMBOLO', parent=filho1)
        p[1] = filho1
    else:
        p[1].parent = pai

    if len(p) > 2:
        p[2].parent = pai


def p_operador_relacional(p):
    """operador_relacional : MENOR
                            | MAIOR
                            | IGUAL
                            | DIFERENTE 
                            | MENOR_IGUAL
                            | MAIOR_IGUAL
    """
    pai = MyNode(name='operador_relacional', type='OPERADOR_RELACIONAL')
    p[0] = pai

    if p[1] == "<":
        filho = MyNode(name='MENOR', type='MENOR', parent=pai)
        filho_sym = MyNode(name=p[1], type='SIMBOLO', parent=filho)
    elif p[1] == ">":
        filho = MyNode(name='MAIOR', type='MAIOR', parent=pai)
        filho_sym = MyNode(name=p[1], type='SIMBOLO', parent=filho)
    elif p[1] == "=":
        filho = MyNode(name='IGUAL', type='IGUAL', parent=pai)
        filho_sym = MyNode(name=p[1], type='SIMBOLO', parent=filho)
    elif p[1] == "<>":
        filho = MyNode(name='DIFERENTE', type='DIFERENTE', parent=pai)
        filho_sym = MyNode(name=p[1], type='SIMBOLO', parent=filho)
    elif p[1] == "<=":
        filho = MyNode(name='MENOR_IGUAL', type='MENOR_IGUAL', parent=pai)
        filho_sym = MyNode(name=p[1], type='SIMBOLO', parent=filho)
    elif p[1] == ">=":
        filho = MyNode(name='MAIOR_IGUAL', type='MAIOR_IGUAL', parent=pai)
        filho_sym = MyNode(name=p[1], type='SIMBOLO', parent=filho)
    else:
        print('Erro operador relacional')

    p[1] = filho


def p_operador_soma(p):
    """operador_soma : MAIS
                    | MENOS
    """
    if p[1] == "+":
        mais = MyNode(name='MAIS', type='MAIS')
        mais_lexema = MyNode(name='+', type='SIMBOLO', parent=mais)
        p[0] = MyNode(name='operador_soma',
                      type='OPERADOR_SOMA', children=[mais])
    else:
        menos = MyNode(name='MENOS', type='MENOS')
        menos_lexema = MyNode(name='-', type='SIMBOLO', parent=menos)
        p[0] = MyNode(name='operador_soma',
                      type='OPERADOR_SOMA', children=[menos])


def p_operador_logico(p):
    """operador_logico : E
                    | OU
    """
    if p[1] == "&&":
        filho = MyNode(name='E', type='E')
        filho_lexema = MyNode(name=p[1], type='SIMBOLO', parent=filho)
        p[0] = MyNode(name='operador_logico',
                      type='OPERADOR_LOGICO', children=[filho])
    else:
        filho = MyNode(name='OU', type='OU')
        filho_lexema = MyNode(name=p[1], type='SIMBOLO', parent=filho)
        p[0] = MyNode(name='operador_logico',
                      type='OPERADOR_SOMA', children=[filho])


def p_operador_negacao(p):
    """operador_negacao : NAO"""

    if p[1] == "!":
        filho = MyNode(name='NAO', type='NAO')
        negacao_lexema = MyNode(name=p[1], type='SIMBOLO', parent=filho)
        p[0] = MyNode(name='operador_negacao',
                      type='OPERADOR_NEGACAO', children=[filho])


def p_operador_multiplicacao(p):
    """operador_multiplicacao : VEZES
                            | DIVIDE
        """
    if p[1] == "*":
        filho = MyNode(name='VEZES', type='VEZES')
        vezes_lexema = MyNode(name=p[1], type='SIMBOLO', parent=filho)
        p[0] = MyNode(name='operador_multiplicacao',
                      type='OPERADOR_MULTIPLICACAO', children=[filho])
    else:
        divide = MyNode(name='DIVIDE', type='DIVIDE')
        divide_lexema = MyNode(name=p[1], type='SIMBOLO', parent=divide)
        p[0] = MyNode(name='operador_multiplicacao',
                      type='OPERADOR_MULTIPLICACAO', children=[divide])


def p_fator(p):
    """fator : ABRE_PARENTESE expressao FECHA_PARENTESE
            | var
            | chamada_funcao
            | numero
        """
    pai = MyNode(name='fator', type='FATOR')
    p[0] = pai
    if len(p) > 2:
        filho1 = MyNode(name='ABRE_PARENTESE', type='ABRE_PARENTESE', parent=pai)
        filho_sym1 = MyNode(name=p[1], type='SIMBOLO', parent=filho1)
        p[1] = filho1

        p[2].parent = pai

        filho3 = MyNode(name='FECHA_PARENTESE', type='FECHA_PARENTESE', parent=pai)
        filho_sym3 = MyNode(name=p[3], type='SIMBOLO', parent=filho3)
        p[3] = filho3
    else:
        p[1].parent = pai


def p_fator_error(p):
    """fator : ABRE_PARENTESE error FECHA_PARENTESE
        """

    error_handler.newError('ERR-SYN-FATOR')

    error_line = p.lineno(2)
    father = MyNode(name='ERR-SYN-FATOR:{}'.format(error_line), type='ERROR')
    logging.error(
        "Syntax error parsing index rule at line {}".format(error_line))
    parser.errok()
    p[0] = father


# ERR-SYN-FATOR

def p_numero(p):
    """numero : NUM_INTEIRO
                | NUM_PONTO_FLUTUANTE
                | NUM_NOTACAO_CIENTIFICA
    """

    pai = MyNode(name='numero', type='NUMERO')
    p[0] = pai

    if str(p[1]).find('.') == -1:
        aux = MyNode(name='NUM_INTEIRO', type='NUM_INTEIRO', parent=pai)
        aux_val = MyNode(name=p[1], type='VALOR', parent=aux)
        p[1] = aux
    elif str(p[1]).find('e') >= 0:
        aux = MyNode(name='NUM_NOTACAO_CIENTIFICA',
                     type='NUM_NOTACAO_CIENTIFICA', parent=pai)
        aux_val = MyNode(name=p[1], type='VALOR', parent=aux)
        p[1] = aux
    else:
        aux = MyNode(name='NUM_PONTO_FLUTUANTE',
                     type='NUM_PONTO_FLUTUANTE', parent=pai)
        aux_val = MyNode(name=p[1], type='VALOR', parent=aux)
        p[1] = aux


def p_chamada_funcao(p):
    """chamada_funcao : ID ABRE_PARENTESE lista_argumentos FECHA_PARENTESE"""

    pai = MyNode(name='chamada_funcao', type='CHAMADA_FUNCAO')
    p[0] = pai
    if len(p) > 2:
        filho1 = MyNode(name='ID', type='ID', parent=pai)
        filho_id = MyNode(name=p[1], type='ID', parent=filho1)
        p[1] = filho1

        filho2 = MyNode(name='ABRE_PARENTESE', type='ABRE_PARENTESE', parent=pai)
        filho_sym = MyNode(name=p[2], type='SIMBOLO', parent=filho2)
        p[2] = filho2

        p[3].parent = pai

        filho4 = MyNode(name='FECHA_PARENTESE', type='FECHA_PARENTESE', parent=pai)
        filho_sym = MyNode(name=p[4], type='SIMBOLO', parent=filho4)
        p[4] = filho4
    else:
        p[1].parent = pai


def p_lista_argumentos(p):
    """lista_argumentos : lista_argumentos VIRGULA expressao
                    | expressao
                    | vazio
        """
    pai = MyNode(name='lista_argumentos', type='LISTA_ARGUMENTOS')
    p[0] = pai

    if len(p) > 2:
        p[1].parent = pai

        filho2 = MyNode(name='VIRGULA', type='VIRGULA', parent=pai)
        filho_sym = MyNode(name=p[2], type='SIMBOLO', parent=filho2)
        p[2] = filho2

        p[3].parent = pai
    else:
        p[1].parent = pai


# def p_lista_argumentos_error(p):
#     """lista_argumentos : error VIRGULA expressao
#                     | expressao
#                     | vazio
#         """
#     # error_handler.newError('ERR-SYN-LISTA-ARGUMENTOS')


def p_vazio(p):
    """vazio : """

    pai = MyNode(name='vazio', type='VAZIO')
    p[0] = pai


def p_error(p):
    if p:
        token = p
        print("Erro:[{line},{column}]: Erro próximo ao token '{token}'".format(
            line=token.lineno, column=token.lineno, token=token.value))


# Programa principal.

# Build the parser.
parser = yacc.yacc(method="LALR", optimize=True, start='programa', debug=True,
                   debuglog=log, write_tables=False, tabmodule='tpp_parser_tab')


def main():
    if len(sys.argv) < 2:
        raise TypeError(error_handler.newError('ERR-SYN-USE'))

    aux = argv[1].split('.')
    if aux[-1] != 'tpp':
        raise IOError(error_handler.newError('ERR-SYN-NOT-TPP'))
    elif not os.path.exists(argv[1]):
        raise IOError(error_handler.newError('ERR-SYN-FILE-NOT-EXISTS'))
    else:
        data = open(argv[1])
        source_file = data.read()
        parser.parse(source_file)

    if root and root.children != ():
        # print("Generating Syntax Tree Graph...")
        # DotExporter(root).to_picture(argv[1] + ".ast.png")
        UniqueDotExporter(root).to_picture(argv[1] + ".unique.ast.png")
        # DotExporter(root).to_dotfile(argv[1] + ".ast.dot")
        # UniqueDotExporter(root).to_dotfile(argv[1] + ".unique.ast.dot")
        # print(RenderTree(root, style=AsciiStyle()).by_attr())
        # print("Graph was generated.\nOutput file: " + argv[1] + ".ast.png")

        # DotExporter(root, graph="graph",
        #            nodenamefunc=MyNode.nodenamefunc,
        #            nodeattrfunc=lambda node: 'label=%s' % (node.type),
        #            edgeattrfunc=MyNode.edgeattrfunc,
        #            edgetypefunc=MyNode.edgetypefunc).to_picture(argv[1] + ".ast2.png")

        # DotExporter(root, nodenamefunc=lambda node: node.label).to_picture(argv[1] + ".ast3.png")

    else:
        print(error_handler.newError('WAR-SYN-NOT-GEN-SYN-TREE'))

    return root, symbol_table, symbol_func_table


if __name__ == "__main__":
    main()

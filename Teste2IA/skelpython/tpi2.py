#encoding: utf8

# YOUR NAME:Guilherme Ferreira Duarte
# YOUR NUMBER:107766

# COLLEAGUES WITH WHOM YOU DISCUSSED THIS ASSIGNMENT (names, numbers):
# - João Rodrigues 108214
# - André Miragaia 108412
# - fabio alves 108016
# - guilherme andrade 107696

from semantic_network import *
from constraintsearch import *

class MySN(SemanticNetwork):

    def __init__(self):
        SemanticNetwork.__init__(self)
        self.assoc_stats = {}
    
    def query_local(self, user=None, e1=None, rel=None, e2=None):
        self.query_result = []

        for u, attributes in self.declarations.items():
            for (entity1, relation), entity2 in attributes.items():
                if (
                    (user is None or u == user)
                    and (e1 is None or entity1 == e1)
                    and (rel is None or relation == rel)
                    and (e2 is None or entity2 == e2)
                ):
                    if isinstance(entity2, set):
                        for i in entity2:
                            self.query_result.append(
                                Declaration(u, Relation(entity1, relation, i))
                            )
                    else:
                        self.query_result.append(
                            Declaration(u, Relation(entity1, relation, entity2))
                        )
        return self.query_result
        
    def query(self, entity, assoc=None):
        decl = self.query_local(e1=entity, rel=assoc)

        p = [
            a.relation.entity2
            for a in self.query_local(e1=entity)
        ]

        self.query_result = decl + [
            item
            for a in p
            for item in self.query(a, assoc=assoc)
        ]
        
        self.query_result = [
            a
            for a in self.query_result
            if a.relation.name not in ['member', 'subtype']
        ]
    

        return self.query_result 

    def update_assoc_stats(self, assoc, user=None):
        def recursive_get_subtype(types):
            if not types:
                return []
            
            new_types = [rel.relation.entity2 for rel in self.query_local(user=user, rel="subtype", e1=types[0])]
            return new_types + recursive_get_subtype(types[1:] + new_types)  

        def calculate_frequencies(entities, user):
            type_count_dict = {}
            for ent in entities:
                types = [rel.relation.entity2 for rel in self.query_local(user=user, rel="member", e1=ent)]
                types = recursive_get_subtype(types) + types
                for type in types:
                    type_count_dict[type] = type_count_dict.get(type, 0) + 1
            return type_count_dict

        def calculate_common_frequencies(entities, user):
            type_count_dict = calculate_frequencies(entities, user)

            frequencies = {}
            N = len(entities)
            K = N - len(set(entities))

            for type, count in type_count_dict.items():
                if user is None:
                    frequencies[type] = count / (N - K + K**(1/2))
                else:
                    frequencies[type] = count / N

            return frequencies

        known_entities1 = [obj.relation.entity1 for obj in self.query_local(user=user, rel=assoc) if isObjectName(obj.relation.entity1)]
        known_entities2 = [obj.relation.entity2 for obj in self.query_local(user=user, rel=assoc) if isObjectName(obj.relation.entity2)]

        f1 = calculate_common_frequencies(known_entities1, user)
        f2 = calculate_common_frequencies(known_entities2, user)

        self.assoc_stats[(assoc, user)] = (f1, f2)
        return




class MyCS(ConstraintSearch):

    def __init__(self,domains,constraints):
        ConstraintSearch.__init__(self,domains,constraints)
        


    def search_all(self, domains=None, xpto=None):
        if xpto is None:
            xpto = []  # Lista para armazenar todas as soluções

        def getpropagate(domains, edges):
            while edges:
                (var1, var2) = edges.pop(0)
                constraint = self.constraints[var1, var2]
                domain = [x for x in domains[var1] if any(constraint(var1, x, var2, y) for y in domains[var2])]
                if len(domain) < len(domains[var1]):
                    domains[var1] = domain
                    edges += [(v1, v2) for (v1, v2) in self.constraints if v2 == var1]
            return domains

        index = 0

        # Domínio inicial é o self.domains, mas seguintes vão ser alterados
        # de acordo com as restrições e por isso são passados como argumento
        if domains is None:
            domains = self.domains

        stack = [(domains, xpto, index)]

        while stack:
            current_domains, current_xpto, current_index = stack.pop()

            # Se alguma variável tiver lista de valores vazia, falha
            if any([lv == [] for lv in current_domains.values()]):
                continue

            # Se nenhuma variável tiver mais do que um valor possível, foi encontrada 1 solução
            # Acrescentar à lista de soluções (xpto)
            if all([len(lv) == 1 for lv in list(current_domains.values())]):
                current_xpto.append({v: lv[0] for (v, lv) in current_domains.items()})
            # Caso contrário, continuar a pesquisar nesse domínio
            else:
                # Pesquisa com ordem de fixação pré-definida
                # Geram-se pesquisas para variações da var no index em estudo
                var = list(current_domains.keys())[current_index]
                # Que é incrementado na próxima pesquisa
                current_index += 1
                # Caso hajam variações para essa variável, fazer pesquisa para cada uma
                if len(current_domains[var]) > 1:
                    for val in current_domains[var]:
                        new_domains = dict(current_domains)
                        new_domains[var] = [val]
                        edges = [(v1, v2) for (v1, v2) in self.constraints if v2 == var]
                        new_domains = getpropagate(new_domains, edges)
                        stack.append((new_domains, current_xpto, current_index))
                # Caso contrário e ainda hajam vars para variar, prosseguir com domínio atual
                elif current_index < len(current_domains):
                    stack.append((current_domains, current_xpto, current_index))

        return xpto
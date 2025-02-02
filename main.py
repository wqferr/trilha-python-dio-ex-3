from typing import Optional
from datetime import date
from abc import ABC, abstractmethod

menu = """

[d] Depositar
[s] Sacar
[e] Extrato
[u] Criar usuário
[c] Criar conta
[q] Sair

=> """


class Historico:
    def __init__(self):
        self._transacoes: list["Transacao"] = []

    def adicionar_transacao(self, transacao: "Transacao") -> None:
        self._transacoes.append(transacao)

    def resumo(self) -> str:
        linhas = map(str, self._transacoes)
        return "\n".join(linhas)


class Cliente:
    def __init__(self, *, endereco: str):
        self._endereco = endereco
        self._contas: list["Conta"] = []

    def _checa_conta_pertence_a_si(self, conta: "Conta") -> None:
        if conta.cliente() is not self:
            raise ValueError("Cliente da conta não bate com o objeto cliente.")

    def realizar_transacao(self, conta: "Conta", transacao: "Transacao") -> None:
        self._checa_conta_pertence_a_si(conta)
        if transacao.registrar(conta):
            conta.historico().adicionar_transacao(transacao)

    def adicionar_conta(self, conta: "Conta") -> None:
        self._checa_conta_pertence_a_si(conta)
        self._contas.append(conta)


class PessoaFisica(Cliente):
    def __init__(
        self,
        *,
        nome: str,
        cpf: str,
        data_nascimento: date,
        endereco: str,
    ):
        super().__init__(endereco=endereco)
        self._nome = nome
        self._cpf = cpf
        self._data_nascimento = data_nascimento


class Conta:
    def __init__(
        self,
        agencia: str,
        numero: str,
        cliente: Cliente,
    ):
        self._agencia = agencia
        self._numero = numero
        self._cliente = cliente
        self._saldo = 0
        self._historico = Historico()
        cliente.adicionar_conta(self)

    def cliente(self) -> Cliente:
        return self._cliente

    def saldo(self) -> float:
        return self._saldo

    def historico(self) -> Historico:
        return self._historico

    # Me recuso a fazer isso, mas deixei aqui comentado só pra mostrar que sei fazer
    # @classmethod
    # def nova_conta(cls, agencia: str, numero: str, cliente: Cliente) -> "Conta":
    #     return cls(agencia, numero, cliente)

    def sacar(self, valor: float) -> bool:
        if self._saldo >= valor:
            self._saldo -= valor
            return True
        else:
            return False

    def depositar(self, valor: float) -> bool:
        self._saldo += valor
        return True


class ContaCorrente(Conta):
    def __init__(self, *, limite: float, limite_saques: int):
        self._limite = limite
        self._limite_saques = limite_saques
        self._saques_realizados = 0

    def sacar(self, valor: float) -> bool:
        if self._saques_realizados >= self._limite_saques:
            return False
        elif valor > self._limite:
            return False
        else:
            return super().sacar(valor)


class Transacao(ABC):
    @abstractmethod
    def registrar(conta: Conta) -> bool:
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass


class Deposito(Transacao):
    def __init__(self, valor: float):
        if valor < 0:
            raise ValueError("Depósito não deve ter um valor negativo.")
        self._valor = valor

    def registrar(self, conta: Conta) -> bool:
        return conta.depositar(self._valor)

    def __str__(self) -> str:
        return f"Depósito: R$ {self._valor:.2f}"


class Saque(Transacao):
    def __init__(self, valor: float):
        if valor < 0:
            raise ValueError("Saque não deve ter um valor negativo.")
        self._valor = valor

    def registrar(self, conta: Conta):
        return conta.sacar(self._valor)

    def __str__(self) -> str:
        return f"Saque: R$ {self._valor:.2f}"


saldo = 0
LIMITE_PADRAO = 500
extrato = ""
numero_saques = 0
LIMITE_SAQUES = 3
AGENCIA = "0001"


def valida_cpf(cpf: str):
    if len(cpf) != 11:
        return False
    else:
        return cpf.isnumeric()


def encontra_usuario(lista_usuarios: list[dict], *, cpf: str):
    for usuario in lista_usuarios:
        if usuario["cpf"] == cpf:
            return usuario
    return None


def novo_usuario(
    lista_usuarios: list[dict],
    *,
    nome: str,
    cpf: str,
    endereco: str,
) -> Optional[dict]:
    if not valida_cpf(cpf):
        print("CPF inválido.")
        return None

    usuario_com_cpf = encontra_usuario(lista_usuarios, cpf=cpf)
    if usuario_com_cpf is None:
        usuario = dict(nome=nome, cpf=cpf, endereco=endereco)
        lista_usuarios.append(usuario)
        return usuario
    else:
        print(f"Usuário com CPF duplicado: {cpf}.")
        return None


def nova_conta(lista_contas: list[dict], *, usuario: dict) -> Optional[dict]:
    if usuario is None:
        print("Uma conta precisa de um usuário vinculado.")
        return None
    else:
        conta = dict(agencia=AGENCIA, numero=len(lista_contas) + 1, usuario=usuario)
        lista_contas.append(conta)
        return conta


def saque(
    *,
    saldo,
    valor,
    extrato,
    limite,
    numero_saques,
    limite_saques,
) -> dict:
    if numero_saques >= limite_saques:
        print("Operação excederia limite de saques diários.")
    elif valor <= 0:
        print("Valor inválido: saque só suporta quantias positivas.")
    elif valor > limite:
        print("Operação excederia limite por saque.")
    elif valor > saldo:
        print("Saldo insuficiente.")
    else:
        saldo -= valor
        extrato += f"Saque: R$ {valor:.2f}\n"
        numero_saques += 1

    return dict(saldo=saldo, extrato=extrato, numero_saques=numero_saques)


def deposito(saldo, valor, extrato, /) -> dict:
    if valor <= 0:
        print("Valor inválido: depósito só suporta quantias positivas.")
    else:
        saldo += valor
        extrato += f"Depósito: R$ {valor:.2f}\n"

    return dict(saldo=saldo, extrato=extrato)


def exibe_extrato(saldo, /, *, extrato) -> None:
    if extrato:
        print(extrato)
    else:
        print("Extrato vazio.")
    print(f"\nSaldo: R$ {saldo:.2f}")


contas = []
usuarios = []

while True:
    opcao = input(menu)

    if opcao == "d":
        valor = float(input("Valor do depósito: "))
        resultado = deposito(saldo, valor, extrato)
        saldo = resultado["saldo"]
        extrato = resultado["extrato"]

    elif opcao == "s":
        valor = float(input("Valor do saque: "))
        resultado = saque(
            saldo=saldo,
            valor=valor,
            extrato=extrato,
            limite=LIMITE_PADRAO,
            numero_saques=numero_saques,
        )
        saldo = resultado["saldo"]
        extrato = resultado["extrato"]
        numero_saques = resultado["numero_saques"]

    elif opcao == "e":
        exibe_extrato(saldo, extrato=extrato)

    elif opcao == "u":
        nome = input("Nome: ")
        cpf = input("CPF: ")
        endereco = input("Endereço: ")
        novo_usuario(usuarios, nome=nome, cpf=cpf, endereco=endereco)

    elif opcao == "c":
        cpf = input("CPF do usuário: ")
        usuario = encontra_usuario(usuarios, cpf=cpf)
        if usuario is None:
            print("Usuário não encontrado.")
        else:
            conta = nova_conta(contas, usuario=usuario)
            print(f"Conta número {conta['numero']} criada.")

    elif opcao == "q":
        break

    else:
        print("Operação inválida, por favor selecione novamente a operação desejada.")

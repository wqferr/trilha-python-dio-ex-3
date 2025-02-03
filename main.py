from typing import Optional
from datetime import date
from abc import ABC, abstractmethod
from collections import defaultdict

menu_inicial = """

[u] Criar usuário
[l] Fazer login
[q] Sair

"""

menu_cliente = """

[c] Criar conta
[d] Depositar
[s] Sacar
[e] Extrato
[x] Fazer logout

=> """

msg_operacao_invalida = (
    "Operação inválida, por favor selecione novamente a operação desejada."
)


class Historico:
    def __init__(self):
        self._transacoes: list["Transacao"] = []

    def adicionar_transacao(self, transacao: "Transacao") -> None:
        self._transacoes.append(transacao)

    def resumo(self) -> str:
        linhas = map(str, self._transacoes)
        return "\n".join(linhas)


class Cliente:
    lista_clientes: list["Cliente"] = []

    def __init__(self, *, endereco: str):
        self._endereco = endereco
        self._contas: list["Conta"] = []
        Cliente.lista_clientes.append(self)

    def _checa_conta_pertence_a_si(self, conta: "Conta") -> None:
        if conta.cliente() is not self:
            raise ValueError("Cliente da conta não bate com o objeto cliente.")

    def busca_conta(self, agencia: str, numero: int) -> Optional["Conta"]:
        for conta in self._contas:
            if conta.agencia() == agencia and conta.numero() == numero:
                return conta
        return None

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

        if not PessoaFisica.valida_cpf(cpf):
            raise ValueError("CPF inválido.")
        else:
            cliente_existente = PessoaFisica.busca_por_cpf(cpf)
            if cliente_existente is not None and cliente_existente is not self:
                raise ValueError("CPF já existe.")

    def cpf(self) -> str:
        return self._cpf

    @classmethod
    def valida_cpf(cls, cpf: str):
        if len(cpf) != 11:
            return False
        else:
            return cpf.isnumeric()

    @classmethod
    def busca_por_cpf(cls, cpf: str) -> Optional[Cliente]:
        for cliente in cls.lista_clientes:
            if isinstance(cliente, PessoaFisica) and cliente.cpf() == cpf:
                return cliente
        return None


class Conta:
    contas_por_agencia: dict[str, list["Conta"]] = defaultdict(list)

    def __init__(
        self,
        agencia: str,
        cliente: Cliente,
    ):
        Conta.contas_por_agencia[agencia].append(self)
        self._agencia = agencia
        self._numero = len(Conta.contas_por_agencia[agencia])
        self._cliente = cliente
        self._saldo = 0
        self._historico = Historico()
        cliente.adicionar_conta(self)

    def agencia(self) -> str:
        return self._agencia

    def numero(self) -> int:
        return self._numero

    def cliente(self) -> Cliente:
        return self._cliente

    def saldo(self) -> float:
        return self._saldo

    def historico(self) -> Historico:
        return self._historico

    @classmethod
    def busca_agencia_numero(cls, agencia: str, numero: int) -> Optional["Conta"]:
        for conta in Conta.contas_por_agencia[agencia]:
            if conta._numero == numero:
                return conta
        return None

    # Me recuso a fazer isso, mas deixei aqui comentado só pra mostrar que sei fazer
    # @classmethod
    # def nova_conta(cls, agencia: str, cliente: Cliente) -> "Conta":
    #     return cls(agencia, cliente)

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
    def __init__(
        self,
        agencia: str,
        cliente: Cliente,
        *,
        limite: float,
        limite_saques: int,
    ):
        super().__init__(agencia, cliente)
        self._limite = limite
        self._limite_saques = limite_saques
        self._saques_realizados = 0

    def sacar(self, valor: float) -> bool:
        if self._saques_realizados >= self._limite_saques:
            return False
        elif valor > self._limite:
            return False
        else:
            self._saques_realizados += 1
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


LIMITE_PADRAO = 500
LIMITE_SAQUES = 3


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


def le_conta_cliente(cliente: Cliente) -> Optional[Conta]:
    agencia = input("Agência: ")
    try:
        numero_conta = int(input("Número da conta: "))
    except ValueError:
        print("Número de conta inválido.")
        return None

    conta = cliente.busca_conta(agencia, numero_conta)
    if conta:
        return conta
    else:
        print("Conta não encontrada para este cliente.")
        return None


contas = []
usuarios = []

while True:
    opcao_inicial = input(menu_inicial)

    if opcao_inicial == "q":
        break

    elif opcao_inicial == "u":
        nome = input("Nome: ")
        cpf = input("CPF: ")
        endereco = input("Endereço: ")
        data_nasc_raw = input("Data de nascimento: ")
        try:
            dia, mes, ano = map(int, data_nasc_raw.split("/"))
        except ValueError:
            print("Data inválida.")
        data_nascimento = date(year=ano, month=mes, day=dia)
        try:
            PessoaFisica(
                nome=nome, cpf=cpf, endereco=endereco, data_nascimento=data_nascimento
            )
        except ValueError as e:
            print(str(e))

    elif opcao_inicial == "l":
        cpf = input("CPF do cliente: ")
        cliente = PessoaFisica.busca_por_cpf(cpf)
        if not cliente:
            print("Cliente não encontrado.")
            continue

        while True:
            opcao_cliente = input(menu_cliente)

            if opcao_cliente == "x":
                break

            elif opcao_cliente == "c":
                agencia = input("Agência: ")
                nova_conta = ContaCorrente(
                    agencia, cliente, limite=LIMITE_PADRAO, limite_saques=LIMITE_SAQUES
                )
                print(
                    f"Nova conta criada: agência {agencia} número {nova_conta.numero()}."
                )

            elif opcao_cliente == "d":
                conta = le_conta_cliente(cliente)
                if not conta:
                    continue

                valor = float(input("Valor do depósito: "))
                cliente.realizar_transacao(conta, Deposito(valor))

            elif opcao_cliente == "s":
                conta = le_conta_cliente(cliente)
                if not conta:
                    continue

                valor = float(input("Valor do saque: "))
                cliente.realizar_transacao(conta, Saque(valor))

            elif opcao_cliente == "e":
                conta = le_conta_cliente(cliente)
                if not conta:
                    continue

                print(conta.historico().resumo())

            else:
                print(msg_operacao_invalida)

    else:
        print(msg_operacao_invalida)

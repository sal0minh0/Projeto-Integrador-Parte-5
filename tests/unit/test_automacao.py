import pytest
from src.automacao import (Tarefa, ControladorRobo, StatusTarefa, AcaoRobo, PlataformaDestino, TarefaInvalidaError)

class TestTarefa:
    
    def test_criacao_tarefa_valida(self):
        """Garante que a classe instancie corretamente com dados válidos."""
        tarefa = Tarefa(id_tarefa="T-001", status=StatusTarefa.PENDENTE, urgente=False, tentativas=0, plataforma=PlataformaDestino.PORTAL_WEB)
        assert tarefa.id_tarefa == "T-001"
        assert tarefa.tentativas == 0
        assert tarefa.plataforma == PlataformaDestino.PORTAL_WEB

    def test_erro_ao_criar_com_tentativas_negativas(self):
        """Verifica se a validação de tentativas negativas funciona."""
        with pytest.raises(TarefaInvalidaError, match="inteiro positivo"):
            Tarefa(id_tarefa="T-002", status=StatusTarefa.PENDENTE, urgente=False, tentativas=-1)

    def test_erro_ao_criar_com_tentativas_string(self):
        """Verifica segurança de tipagem na quantidade de tentativas."""
        with pytest.raises(TarefaInvalidaError):
            Tarefa(id_tarefa="T-003", status=StatusTarefa.PENDENTE, urgente=False, tentativas="dois") # type: ignore

    def test_erro_ao_criar_sem_id(self):
        """Verifica validação de ID vazio."""
        with pytest.raises(TarefaInvalidaError):
            Tarefa(id_tarefa="", status=StatusTarefa.PENDENTE, urgente=False, tentativas=0)

    def test_registrar_tentativa(self):
        """Garante que a função de incremento opera corretamente."""
        tarefa = Tarefa(id_tarefa="T-004", status=StatusTarefa.ERRO, urgente=False, tentativas=1)
        tarefa.registrar_tentativa()
        assert tarefa.tentativas == 2

@pytest.fixture
def controlador():
    """Prepara o ambiente de teste e injeta o controlador em cada método."""
    return ControladorRobo(max_tentativas=3)

class TestControladorRobo:

    def test_inicializacao_invalida_controlador(self):
        """Garante que o robô não comece com regras de repetição quebradas."""
        with pytest.raises(ValueError):
            ControladorRobo(max_tentativas=0)

    def test_acao_baixa_sistema_para_tarefas_concluidas(self, controlador):
        """Testa o cenário ideal onde o robô terminou o trabalho."""
        tarefa = Tarefa(id_tarefa="T-100", status=StatusTarefa.CONCLUIDO, urgente=False, tentativas=1)
        acao = controlador.determinar_acao(tarefa)
        assert acao == AcaoRobo.BAIXA_SISTEMA

    def test_acao_reprocessar_erro_dentro_do_limite(self, controlador):
        """Testa o comportamento do robô de tentar de novo após um erro."""
        tarefa = Tarefa(id_tarefa="T-101", status=StatusTarefa.ERRO, urgente=False, tentativas=1)
        acao = controlador.determinar_acao(tarefa)
        assert acao == AcaoRobo.REPROCESSAR

    def test_acao_reprocessar_erro_no_limite_exato(self, controlador):
        """Testando a borda de limite de tentativas do robô."""
        tarefa = Tarefa(id_tarefa="T-102", status=StatusTarefa.ERRO, urgente=False, tentativas=2)
        acao = controlador.determinar_acao(tarefa)
        assert acao == AcaoRobo.REPROCESSAR

    def test_acao_escalar_humano_erro_acima_do_limite(self, controlador):
        """Testa a passagem da tarefa para um humano após falhas seguidas."""
        tarefa = Tarefa(id_tarefa="T-103", status=StatusTarefa.ERRO, urgente=False, tentativas=3)
        acao = controlador.determinar_acao(tarefa)
        assert acao == AcaoRobo.ESCALAR_HUMANO

    def test_acao_processar_agora_tarefas_pendentes_urgentes(self, controlador):
        """Testa o robô prioriza as tarefas."""
        tarefa = Tarefa(id_tarefa="T-104", status=StatusTarefa.PENDENTE, urgente=True, tentativas=0)
        acao = controlador.determinar_acao(tarefa)
        assert acao == AcaoRobo.PROCESSAR_AGORA

    def test_acao_enviar_fila_tarefas_pendentes_nao_urgentes(self, controlador):
        """Testa o enfileiramento padrão para automações."""
        tarefa = Tarefa(id_tarefa="T-105", status=StatusTarefa.PENDENTE, urgente=False, tentativas=0)
        acao = controlador.determinar_acao(tarefa)
        assert acao == AcaoRobo.ENVIAR_FILA

    def test_acao_enviar_fila_tarefas_travadas_em_processamento(self, controlador):
        """Testa a recuperação de tarefas que travaram o robô."""
        tarefa = Tarefa(id_tarefa="T-106", status=StatusTarefa.EM_PROCESSAMENTO, urgente=False, tentativas=1)
        acao = controlador.determinar_acao(tarefa)
        assert acao == AcaoRobo.ENVIAR_FILA

    def test_acao_escalar_humano_status_invalido(self, controlador):
        """Testa a ação de fallback caso a tarefa tenha um status inválido/não mapeado."""
        tarefa = Tarefa(id_tarefa="T-107", status=None, urgente=False, tentativas=0) # type: ignore
        acao = controlador.determinar_acao(tarefa)
        assert acao == AcaoRobo.ESCALAR_HUMANO
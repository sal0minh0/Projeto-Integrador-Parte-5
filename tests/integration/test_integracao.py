import pytest
from src.automacao import (Tarefa, ControladorRobo, StatusTarefa, AcaoRobo, PlataformaDestino,
    RepositorioTarefasEmMemoria, ServicoProcessamento)

@pytest.fixture
def repositorio():
    return RepositorioTarefasEmMemoria()

@pytest.fixture
def controlador():
    return ControladorRobo(max_tentativas=3)

@pytest.fixture
def servico(repositorio, controlador):
    return ServicoProcessamento(repositorio, controlador)

class TestIntegracaoServicoAutomacao:

    def test_fluxo_reprocessamento_integra_camadas(self, servico, repositorio):
        """
        Valida o fluxo em que uma tarefa com erro, com tentativas abaixo do limite, é reprocessada. 
        """
        # 1. Preparação (Setup)
        tarefa = Tarefa(
            id_tarefa="INT-001",
            status=StatusTarefa.ERRO,
            urgente=False,
            tentativas=1,
            plataforma=PlataformaDestino.PORTAL_WEB
        )
        repositorio.salvar(tarefa)

        # 2. Execução (Ação)
        acao = servico.avaliar_e_processar_tarefa("INT-001")

        # 3. Verificação (Asserção)
        assert acao == AcaoRobo.REPROCESSAR
        
        # Verifica se as tentativas foram incrementadas no domínio e salvas no repositório
        tarefa_salva = repositorio.buscar("INT-001")
        assert tarefa_salva is not None
        assert tarefa_salva.tentativas == 2

    def test_fluxo_escalar_humano_limite_tentativas(self, servico, repositorio):
        """
        Valida se a tarefa é encaminhada a um humano 
        se ela atingir o limite de tentativas.
        """
        tarefa = Tarefa(
            id_tarefa="INT-002",
            status=StatusTarefa.ERRO,
            urgente=True,
            tentativas=3, 
            plataforma=PlataformaDestino.SISTEMA_DESKTOP
        )
        repositorio.salvar(tarefa)

        acao = servico.avaliar_e_processar_tarefa("INT-002")

        assert acao == AcaoRobo.ESCALAR_HUMANO
        
        tarefa_salva = repositorio.buscar("INT-002")
        assert tarefa_salva is not None
        assert tarefa_salva.tentativas == 3 # Nenhuma tentativa extra foi registrada

    def test_fluxo_baixa_sistema_sucesso(self, servico, repositorio):
        """
        Garante que tarefas concluídas recebam a ação correta no serviço.
        """
        tarefa = Tarefa(
            id_tarefa="INT-003",
            status=StatusTarefa.CONCLUIDO,
            urgente=False,
            tentativas=0,
            plataforma=PlataformaDestino.BANCO_DADOS
        )
        repositorio.salvar(tarefa)

        acao = servico.avaliar_e_processar_tarefa("INT-003")

        assert acao == AcaoRobo.BAIXA_SISTEMA

    def test_erro_tarefa_inexistente(self, servico):
        """
        Valida se o serviço lida corretamente quando tenta 
        processar uma tarefa que não existe no repositório.
        """
        with pytest.raises(ValueError, match="não encontrada no repositório"):
            servico.avaliar_e_processar_tarefa("INT-999")

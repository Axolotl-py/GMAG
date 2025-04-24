// Variáveis globais
let modoAtual = null;
let processamentoEmAndamento = false;

// Função para mostrar tela específica
function mostrarTela(idTela) {
    document.querySelectorAll('.tela').forEach(tela => {
        tela.classList.remove('ativa');
    });
    const telaSelecionada = document.getElementById(idTela);
    if (telaSelecionada) telaSelecionada.classList.add('ativa');
}

// Função para verificar diretórios
function verificarDiretorios() {
    const inputDir = document.getElementById('input-dir').value;
    const outputDir = document.getElementById('output-dir').value;
    const btnProcessar = document.getElementById('btn-processar');
    btnProcessar.disabled = !(inputDir && outputDir && modoAtual);
}

// Função para carregar diretórios salvos
async function carregarDiretoriosSalvos() {
    try {
        const dirs = await eel.obter_diretorios()();
        document.getElementById('input-dir').value = dirs.input_dir || '';
        document.getElementById('output-dir').value = dirs.output_dir || '';
        verificarDiretorios();
    } catch (error) {
        console.error("Erro ao carregar diretórios:", error);
    }
}

// Função para selecionar o modo de operação
function selecionarModo(modo) {
    modoAtual = modo;
    mostrarTela('tela-processamento');
    document.getElementById('titulo-processamento').textContent = 
        `Processamento ${modo.replace(/([A-Z])/g, ' $1').trim()}`;
    verificarDiretorios();
}

// Função principal para executar o processamento
async function executarProcessamento() {
    if (processamentoEmAndamento || !modoAtual) return;
    
    try {
        processamentoEmAndamento = true;
        const btnProcessar = document.getElementById('btn-processar');
        btnProcessar.disabled = true;
        
        atualizarStatus(`Iniciando ${modoAtual}...`, 'info');
        atualizarProgresso(0);
        
        const validacao = await eel.validar_diretorios()();
        if (!validacao.input.valido || !validacao.output.valido) {
            let mensagemErro = "Erros encontrados:";
            if (!validacao.input.valido) mensagemErro += `\n• Entrada: ${validacao.input.erro}`;
            if (!validacao.output.valido) mensagemErro += `\n• Saída: ${validacao.output.erro}`;
            atualizarStatus(mensagemErro, 'error');
            atualizarProgresso(100, 'error');
            return;
        }
        
        atualizarStatus(`Executando ${modoAtual}...`, 'info');
        atualizarProgresso(50);
        
        const resultado = await eel.executar_processamento_especifico(modoAtual)();
        
        if (resultado.status === 'success') {
            atualizarStatus(
                `${modoAtual} concluído em ${resultado.duracao.toFixed(2)}s!`,
                'success'
            );
            atualizarProgresso(100, 'success');
            await atualizarHistorico();
        } else {
            atualizarStatus(`Erro: ${resultado.message}`, 'error');
            atualizarProgresso(100, 'error');
        }
    } catch (error) {
        console.error(`Erro: ${error}`);
        atualizarStatus(`Falha: ${error.message}`, 'error');
        atualizarProgresso(100, 'error');
    } finally {
        processamentoEmAndamento = false;
        verificarDiretorios();
    }
}

// Funções auxiliares (mantidas conforme seu original)
function atualizarStatus(mensagem, tipo = 'info') {
    const statusElement = document.getElementById('status-processamento');
    statusElement.textContent = mensagem;
    statusElement.style.color = 
        tipo === 'error' ? '#ff4444' : 
        tipo === 'success' ? '#44ff44' : 
        'var(--accent-color)';
}

function atualizarProgresso(percentual, tipo = 'info') {
    const progresso = document.getElementById('progresso-processamento');
    progresso.style.width = `${percentual}%`;
    progresso.style.backgroundColor = 
        tipo === 'error' ? '#ff4444' : 
        tipo === 'success' ? '#44ff44' : 
        'var(--accent-color)';
}

async function atualizarHistorico() {
    try {
        const historico = await eel.obter_historico()();
        const historicoElement = document.getElementById('historico-processamentos');
        historicoElement.innerHTML = historico.map(item => `
            <div class="item-historico">
                <div class="data-historico">${item.data}</div>
                <div class="detalhes-historico">
                    <div>Modo: ${item.modo || 'N/A'}</div>
                    <div>Entrada: ${item.input}</div>
                    <div>Saída: ${item.output}</div>
                    <div>Duração: ${item.duracao.toFixed(2)}s</div>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error("Erro ao carregar histórico:", error);
    }
}

function mostrarSobre() {
    modoAtual = null;
    mostrarTela('tela-sobre');
    document.getElementById('titulo-sobre').textContent = 'Sobre o GMAG';
    document.getElementById('conteudo-sobre').innerHTML = `
        <div class="sobre-container">
            <h3>GMAG - Sistema de Análise de Materiais</h3>
            <p>Versão 1.0.0</p>
            <!-- Restante do conteúdo -->
        </div>
    `;
}

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    configurarTema();
    carregarDiretoriosSalvos();
    
    document.getElementById('btn-processar').addEventListener('click', executarProcessamento);
    
    document.querySelectorAll('.directory-input button').forEach(button => {
        button.addEventListener('click', function() {
            const tipo = this.textContent.includes('Entrada') ? 'input' : 'output';
            selecionarDiretorio(tipo);
        });
    });
});